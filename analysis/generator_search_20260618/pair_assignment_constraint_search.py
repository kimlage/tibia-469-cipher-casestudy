#!/usr/bin/env python3
"""Constraint-based assignment search for the 55 pair-table cells.

Previous searches found:

- the unordered-pair geometry is real;
- homophone class sizes track internal symbol frequency;
- exact cell placement is not recovered by arithmetic, source cycles, seeds,
  spatial features, or dispersion.

This script tests one remaining plausible human construction: after deciding
how many homophones each internal symbol gets, did the author distribute those
symbols through the 55 pair cells using a simple deterministic allocation
procedure (blocks, round-robin, greedy balance, low-discrepancy spread) over a
natural pair order?

No semantic translation is produced.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"

OUT_JSON = HERE / "pair_assignment_constraint_results.json"
OUT_MD = HERE / "pair_assignment_constraint_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260619


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pair_orders() -> dict[str, list[str]]:
    pairs = [f"{i}{j}" for i in range(10) for j in range(i, 10)]
    orders = {
        "upper_row": pairs,
        "upper_row_rev": list(reversed(pairs)),
        "upper_row_snake": [
            pair
            for i in range(10)
            for pair in ([f"{i}{j}" for j in range(i, 10)] if i % 2 == 0 else [f"{i}{j}" for j in range(9, i - 1, -1)])
        ],
        "upper_column": [f"{i}{j}" for j in range(10) for i in range(j + 1)],
        "upper_column_snake": [
            pair
            for j in range(10)
            for pair in ([f"{i}{j}" for i in range(j + 1)] if j % 2 == 0 else [f"{i}{j}" for i in range(j, -1, -1)])
        ],
        "by_sum": sorted(pairs, key=lambda p: (int(p[0]) + int(p[1]), int(p[0]), int(p[1]))),
        "by_sum_rev": sorted(pairs, key=lambda p: (int(p[0]) + int(p[1]), int(p[0]), int(p[1])), reverse=True),
        "by_diff": sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0]), int(p[1]))),
        "by_diff_rev": sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0]), int(p[1])), reverse=True),
        "by_product": sorted(pairs, key=lambda p: (int(p[0]) * int(p[1]), int(p[0]), int(p[1]))),
        "by_triangular_index": sorted(pairs, key=lambda p: int(p[1]) * (int(p[1]) + 1) // 2 + int(p[0])),
    }
    coords = []
    top, left, bottom, right = 0, 0, 9, 9
    while top <= bottom and left <= right:
        for y in range(left, right + 1):
            coords.append((top, y))
        top += 1
        for x in range(top, bottom + 1):
            coords.append((x, right))
        right -= 1
        if top <= bottom:
            for y in range(right, left - 1, -1):
                coords.append((bottom, y))
            bottom -= 1
        if left <= right:
            for x in range(bottom, top - 1, -1):
                coords.append((x, left))
            left += 1
    seen = []
    seen_set = set()
    for a, b in coords:
        pair = f"{min(a, b)}{max(a, b)}"
        if pair not in seen_set:
            seen.append(pair)
            seen_set.add(pair)
    orders["spiral_first_unordered"] = seen
    return orders


def acceptable_pair_symbols(pair_table: dict, pair: str) -> set[str]:
    row = pair_table[pair]
    if row["status"] == "pure":
        return {row["symbol_if_pure"]}
    return set(row["symbols"])


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def corpus_symbol_order() -> list[str]:
    occ = load_json(OCC_STREAMS)["occ"]
    events = []
    for symbol, rows in occ.items():
        for row in rows:
            events.append((int(row["book"]), int(row["pos"]), symbol))
    out = []
    seen = set()
    for _book, _pos, symbol in sorted(events):
        if symbol not in seen:
            out.append(symbol)
            seen.add(symbol)
    return out


def normalize_order(symbols: list[str]) -> list[str]:
    out = []
    for symbol in symbols:
        if symbol in SIGMA and symbol not in out:
            out.append(symbol)
    for symbol in SIGMA:
        if symbol not in out:
            out.append(symbol)
    return out


def symbol_orders(pair_counts: Counter[str]) -> dict[str, list[str]]:
    source_words = {
        "alpha": list(SIGMA),
        "pair_count_desc": [symbol for symbol, _count in pair_counts.most_common()],
        "pair_count_asc": [symbol for symbol, _count in sorted(pair_counts.items(), key=lambda item: (item[1], item[0]))],
        "first_corpus_symbol": corpus_symbol_order(),
        "itelbenna": list("ITELBENNA"),
        "telbenna": list("TELBENNA"),
        "honeminas": list("HONEMINAS"),
        "mathemagic": list("MATHEMAGIC"),
        "greatcalculator": list("GREATCALCULATOR"),
        "subjectiveviewer": list("SUBJECTIVEVIEWER"),
    }
    return {name: normalize_order(symbols) for name, symbols in source_words.items()}


def block_sequence(order: list[str], counts: Counter[str]) -> list[str]:
    out = []
    for symbol in order:
        out.extend([symbol] * counts[symbol])
    return out


def round_robin_sequence(order: list[str], counts: Counter[str]) -> list[str]:
    remaining = counts.copy()
    out = []
    while sum(remaining.values()) > 0:
        for symbol in order:
            if remaining[symbol] > 0:
                out.append(symbol)
                remaining[symbol] -= 1
    return out


def greedy_balance_sequence(order: list[str], counts: Counter[str]) -> list[str]:
    remaining = counts.copy()
    order_index = {symbol: idx for idx, symbol in enumerate(order)}
    out = []
    while sum(remaining.values()) > 0:
        candidates = [symbol for symbol, count in remaining.items() if count > 0]
        candidates.sort(key=lambda symbol: (-remaining[symbol], order_index.get(symbol, 999)))
        if out and len(candidates) > 1 and candidates[0] == out[-1]:
            candidates = candidates[1:] + candidates[:1]
        symbol = candidates[0]
        out.append(symbol)
        remaining[symbol] -= 1
    return out


def low_discrepancy_sequence(order: list[str], counts: Counter[str]) -> list[str]:
    slots = []
    order_index = {symbol: idx for idx, symbol in enumerate(order)}
    for symbol in order:
        count = counts[symbol]
        if count <= 0:
            continue
        for idx in range(count):
            slots.append(((idx + 0.5) / count, order_index[symbol], symbol))
    return [symbol for _position, _order, symbol in sorted(slots)]


def layered_frequency_sequence(order: list[str], counts: Counter[str]) -> list[str]:
    """Place one layer of every remaining symbol, rare-to-common by layer."""
    remaining = counts.copy()
    order_index = {symbol: idx for idx, symbol in enumerate(order)}
    out = []
    while sum(remaining.values()) > 0:
        layer = [symbol for symbol in order if remaining[symbol] > 0]
        layer.sort(key=lambda symbol: (remaining[symbol], order_index[symbol]))
        for symbol in layer:
            out.append(symbol)
            remaining[symbol] -= 1
    return out


ALGORITHMS = {
    "block": block_sequence,
    "round_robin": round_robin_sequence,
    "greedy_balance": greedy_balance_sequence,
    "low_discrepancy": low_discrepancy_sequence,
    "layered_frequency": layered_frequency_sequence,
}


def score_candidate(pair_table: dict, pairs: list[str], predicted: list[str]) -> dict:
    ok = [
        predicted[idx] in acceptable_pair_symbols(pair_table, pair)
        for idx, pair in enumerate(pairs)
    ]
    return {
        "correct": sum(ok),
        "total": len(ok),
        "accuracy": sum(ok) / len(ok),
    }


def build_candidates(pair_counts: Counter[str]) -> list[dict]:
    candidates = []
    for pair_order_id, pairs in pair_orders().items():
        for symbol_order_id, order in symbol_orders(pair_counts).items():
            for algorithm_id, builder in ALGORITHMS.items():
                sequence = builder(order, pair_counts)
                if len(sequence) != 55:
                    continue
                for reverse in (False, True):
                    pred = list(reversed(sequence)) if reverse else sequence
                    candidates.append(
                        {
                            "pair_order": pair_order_id,
                            "symbol_order": symbol_order_id,
                            "algorithm": algorithm_id,
                            "reverse": reverse,
                            "pairs": pairs,
                            "predicted": pred,
                        }
                    )
    return candidates


def control_search(candidates: list[dict], primary_labels: dict[str, str], trials: int = 5000) -> dict:
    random.seed(RANDOM_SEED)
    labels = list(primary_labels.values())
    pair_list = list(primary_labels)
    max_scores = []
    for _trial in range(trials):
        random.shuffle(labels)
        target = {pair: {label} for pair, label in zip(pair_list, labels)}
        best = 0
        for candidate in candidates:
            ok = sum(
                candidate["predicted"][idx] in target[pair]
                for idx, pair in enumerate(candidate["pairs"])
            )
            if ok > best:
                best = ok
        max_scores.append(best / 55)
    mean = sum(max_scores) / len(max_scores)
    sd = (sum((value - mean) ** 2 for value in max_scores) / (len(max_scores) - 1)) ** 0.5
    return {
        "trials": trials,
        "max_accuracy_mean": mean,
        "max_accuracy_sd": sd,
        "max_accuracy_seen": max(max_scores),
        "p_ge_observed": None,
        "scores": max_scores,
    }


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    natural_pairs = [f"{i}{j}" for i in range(10) for j in range(i, 10)]
    primary_labels = {pair: primary_pair_symbol(pair_table, pair) for pair in natural_pairs}
    pair_counts = Counter(primary_labels.values())
    candidates = build_candidates(pair_counts)

    rows = []
    for candidate in candidates:
        score = score_candidate(pair_table, candidate["pairs"], candidate["predicted"])
        rows.append(
            {
                "pair_order": candidate["pair_order"],
                "symbol_order": candidate["symbol_order"],
                "algorithm": candidate["algorithm"],
                "reverse": candidate["reverse"],
                "predicted_prefix": "".join(candidate["predicted"][:24]),
                **score,
            }
        )
    rows.sort(key=lambda row: (-row["accuracy"], row["algorithm"], row["pair_order"], row["symbol_order"]))
    best = rows[0]
    controls = control_search(candidates, primary_labels, trials=5000)
    controls["p_ge_observed"] = (sum(score >= best["accuracy"] for score in controls["scores"]) + 1) / (
        len(controls["scores"]) + 1
    )
    controls_without_scores = {key: value for key, value in controls.items() if key != "scores"}

    result = {
        "schema": "pair_assignment_constraint_results.v1",
        "translation_delta": "NONE",
        "accepted_original_formula": None,
        "candidate_count": len(candidates),
        "pair_counts": dict(sorted(pair_counts.items())),
        "best": best,
        "top_rows": rows[:50],
        "control": controls_without_scores,
        "verdict": "rejected_control_low_accuracy_posthoc",
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Pair Assignment Constraint Search",
        "",
        "Generated by `pair_assignment_constraint_search.py`.",
        "",
        "This pass asks whether the exact 55 pair-table cells can be reconstructed",
        "from the homophone counts by a simple deterministic allocation procedure.",
        "",
        "## Best Candidate",
        "",
        "| Pair order | Symbol order | Algorithm | Reverse | Accuracy | Control p | Verdict |",
        "|---|---|---|---:|---:|---:|---|",
        f"| `{best['pair_order']}` | `{best['symbol_order']}` | `{best['algorithm']}` | `{best['reverse']}` | {best['correct']}/{best['total']} ({best['accuracy']:.3f}) | {controls_without_scores['p_ge_observed']:.3f} | `{result['verdict']}` |",
        "",
        f"Search breadth: `{len(candidates)}` deterministic candidates; controls",
        "shuffle the same pair-symbol multiset and keep the same search breadth.",
        "",
        "The best row is too low in absolute accuracy and only borderline after",
        "post-hoc search correction, so it is not promoted.",
        "",
        "## Top Rows",
        "",
        "| Accuracy | Pair order | Symbol order | Algorithm | Reverse | Prefix |",
        "|---:|---|---|---|---:|---|",
    ]
    for row in rows[:15]:
        lines.append(
            f"| {row['accuracy']:.3f} | `{row['pair_order']}` | `{row['symbol_order']}` | `{row['algorithm']}` | `{row['reverse']}` | `{row['predicted_prefix']}` |"
        )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            "No simple count-respecting assignment rule recovers the exact pair-cell",
            "placement. The unresolved part remains the specific placement of the",
            "frequency-weighted homophones across the 55 unordered pair cells.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "best={}/{} accuracy={:.3f} p_ge={:.3f}".format(
            best["correct"],
            best["total"],
            best["accuracy"],
            controls_without_scores["p_ge_observed"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
