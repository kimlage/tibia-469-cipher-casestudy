#!/usr/bin/env python3
"""Usage-driven pair-cell placement search for 469.

Known result so far:

- the 55 unordered pair cells are real;
- homophone inventory size tracks internal symbol frequency;
- exact cell placement has not been explained by grid formulas, lore strings,
  seeds, simple assignment procedures, or sequence automata.

This pass tests a narrower construction hypothesis:

    after deciding the homophone inventory, did the author place symbols into
    pair cells according to how often those numeric cells are used in the books?

The search only uses numeric code usage to order cells. It then applies simple
allocation algorithms and tests whether the resulting labels match the frozen
pair table. A train/holdout split prevents choosing a rule on all books at
once. Controls preserve the exact symbol multiset and rerun the same search.

Mechanical only. No number<->plaintext meaning is promoted.
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
MANIFEST_JSON = HERE / "generator_holdout_manifest.json"

OUT_JSON = HERE / "usage_driven_pair_placement_results.json"
OUT_MD = HERE / "usage_driven_pair_placement_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260620
TRIALS = 3000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def numeric_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def all_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def natural_pair_orders() -> dict[str, list[str]]:
    pairs = all_pairs()
    return {
        "upper_row": pairs,
        "upper_row_rev": list(reversed(pairs)),
        "upper_row_snake": [
            pair
            for i in range(10)
            for pair in ([f"{i}{j}" for j in range(i, 10)] if i % 2 == 0 else [f"{i}{j}" for j in range(9, i - 1, -1)])
        ],
        "upper_column": [f"{i}{j}" for j in range(10) for i in range(j + 1)],
        "by_sum": sorted(pairs, key=lambda p: (int(p[0]) + int(p[1]), int(p[0]), int(p[1]))),
        "by_diff": sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0]), int(p[1]))),
        "by_product": sorted(pairs, key=lambda p: (int(p[0]) * int(p[1]), int(p[0]), int(p[1]))),
        "by_triangular_index": sorted(pairs, key=lambda p: int(p[1]) * (int(p[1]) + 1) // 2 + int(p[0])),
    }


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def acceptable_pair_symbols(pair_table: dict, pair: str) -> set[str]:
    row = pair_table[pair]
    if row["status"] == "pure":
        return {row["symbol_if_pure"]}
    return set(row["symbols"])


def events_by_book() -> dict[str, list[dict]]:
    occ = load_json(OCC_STREAMS)["occ"]
    by_book: dict[str, list[dict]] = defaultdict(list)
    for symbol, rows in occ.items():
        for row in rows:
            code = row["code"]
            by_book[str(row["book"])].append(
                {
                    "book": str(row["book"]),
                    "pos": int(row["pos"]),
                    "symbol": symbol,
                    "code": code,
                    "pair": "".join(sorted(code)),
                    "upper_orientation": code == "".join(sorted(code)),
                }
            )
    return {book: sorted(rows, key=lambda item: item["pos"]) for book, rows in by_book.items()}


def usage_stats(book_set: set[str], events: dict[str, list[dict]]) -> dict[str, dict]:
    rows = []
    for book in sorted(book_set, key=numeric_key):
        rows.extend({**event, "global_index": len(rows)} for event in events.get(book, []))

    by_pair = defaultdict(list)
    for row in rows:
        by_pair[row["pair"]].append(row)

    stats = {}
    for pair in all_pairs():
        pair_rows = by_pair.get(pair, [])
        count = len(pair_rows)
        first = pair_rows[0]["global_index"] if pair_rows else 10**9
        last = pair_rows[-1]["global_index"] if pair_rows else 10**9
        mean_index = sum(row["global_index"] for row in pair_rows) / count if count else 10**9
        upper_count = sum(row["upper_orientation"] for row in pair_rows)
        orientation_bias = abs(upper_count - (count - upper_count)) / count if count else 0.0
        first_book = int(pair_rows[0]["book"]) if pair_rows else 10**9
        first_pos = pair_rows[0]["pos"] if pair_rows else 10**9
        stats[pair] = {
            "count": count,
            "first_global_index": first,
            "last_global_index": last,
            "mean_global_index": mean_index,
            "orientation_bias": orientation_bias,
            "first_book": first_book,
            "first_pos": first_pos,
        }
    return stats


def pair_orders_from_usage(stats: dict[str, dict]) -> dict[str, list[str]]:
    pairs = all_pairs()
    orders = dict(natural_pair_orders())
    specs = {
        "usage_count_desc": lambda p: (-stats[p]["count"], p),
        "usage_count_asc": lambda p: (stats[p]["count"], p),
        "first_use_asc": lambda p: (stats[p]["first_global_index"], p),
        "first_use_desc": lambda p: (-stats[p]["first_global_index"], p),
        "last_use_asc": lambda p: (stats[p]["last_global_index"], p),
        "mean_use_asc": lambda p: (stats[p]["mean_global_index"], p),
        "first_book_pos": lambda p: (stats[p]["first_book"], stats[p]["first_pos"], p),
        "orientation_bias_desc": lambda p: (-stats[p]["orientation_bias"], -stats[p]["count"], p),
        "orientation_bias_asc": lambda p: (stats[p]["orientation_bias"], -stats[p]["count"], p),
    }
    for name, keyer in specs.items():
        orders[name] = sorted(pairs, key=keyer)
    return orders


def normalize_symbol_order(symbols: list[str]) -> list[str]:
    out = []
    for symbol in symbols:
        if symbol in SIGMA and symbol not in out:
            out.append(symbol)
    for symbol in SIGMA:
        if symbol not in out:
            out.append(symbol)
    return out


def symbol_orders_from_training(train_books: set[str], events: dict[str, list[dict]], primary_counts: Counter[str]) -> dict[str, list[str]]:
    train_symbol_counts = Counter()
    first_symbols = []
    seen = set()
    for book in sorted(train_books, key=numeric_key):
        for row in events.get(book, []):
            symbol = row["symbol"]
            train_symbol_counts[symbol] += 1
            if symbol not in seen:
                first_symbols.append(symbol)
                seen.add(symbol)
    source_orders = {
        "sigma": list(SIGMA),
        "pair_slot_count_desc": [symbol for symbol, _ in primary_counts.most_common()],
        "pair_slot_count_asc": [symbol for symbol, _ in sorted(primary_counts.items(), key=lambda item: (item[1], item[0]))],
        "train_symbol_count_desc": [symbol for symbol, _ in train_symbol_counts.most_common()],
        "train_symbol_count_asc": [symbol for symbol, _ in sorted(train_symbol_counts.items(), key=lambda item: (item[1], item[0]))],
        "train_first_symbol": first_symbols,
        "itelbenna": list("ITELBENNA"),
        "telbenna": list("TELBENNA"),
        "honeminas": list("HONEMINAS"),
        "greatcalculator": list("GREATCALCULATOR"),
    }
    return {name: normalize_symbol_order(symbols) for name, symbols in source_orders.items()}


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
        for idx in range(count):
            slots.append(((idx + 0.5) / count, order_index[symbol], symbol))
    return [symbol for _position, _order, symbol in sorted(slots)]


def layered_frequency_sequence(order: list[str], counts: Counter[str]) -> list[str]:
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


def score_prediction(pair_table: dict, pair_order: list[str], predicted: list[str]) -> dict:
    ok = [predicted[idx] in acceptable_pair_symbols(pair_table, pair) for idx, pair in enumerate(pair_order)]
    return {
        "correct": sum(ok),
        "total": len(ok),
        "accuracy": sum(ok) / len(ok),
    }


def build_candidates(pair_orders: dict[str, list[str]], symbol_orders: dict[str, list[str]], symbol_counts: Counter[str]) -> list[dict]:
    candidates = []
    for pair_order_id, pair_order in pair_orders.items():
        for symbol_order_id, symbol_order in symbol_orders.items():
            for algorithm_id, builder in ALGORITHMS.items():
                sequence = builder(symbol_order, symbol_counts)
                if len(sequence) != len(pair_order):
                    continue
                for reverse in (False, True):
                    predicted = list(reversed(sequence)) if reverse else sequence
                    candidates.append(
                        {
                            "pair_order_id": pair_order_id,
                            "symbol_order_id": symbol_order_id,
                            "algorithm": algorithm_id,
                            "reverse": reverse,
                            "pair_order": pair_order,
                            "predicted": predicted,
                        }
                    )
    return candidates


def evaluate_candidates(pair_table: dict, candidates: list[dict]) -> list[dict]:
    rows = []
    for candidate in candidates:
        score = score_prediction(pair_table, candidate["pair_order"], candidate["predicted"])
        rows.append(
            {
                "pair_order_id": candidate["pair_order_id"],
                "symbol_order_id": candidate["symbol_order_id"],
                "algorithm": candidate["algorithm"],
                "reverse": candidate["reverse"],
                **score,
            }
        )
    rows.sort(key=lambda row: (-row["accuracy"], row["pair_order_id"], row["symbol_order_id"], row["algorithm"], row["reverse"]))
    return rows


def make_pseudo_pair_table(pairs: list[str], labels: list[str]) -> dict:
    return {
        pair: {
            "status": "pure",
            "symbol_if_pure": labels[idx],
            "symbols": [labels[idx]],
        }
        for idx, pair in enumerate(pairs)
    }


def control_distribution(candidates: list[dict], labels: dict[str, str]) -> dict:
    rng = random.Random(RANDOM_SEED)
    pairs = all_pairs()
    label_values = [labels[pair] for pair in pairs]
    best_values = []
    shuffled = label_values[:]
    for _trial in range(TRIALS):
        rng.shuffle(shuffled)
        pseudo = make_pseudo_pair_table(pairs, shuffled)
        best = max(score_prediction(pseudo, candidate["pair_order"], candidate["predicted"])["accuracy"] for candidate in candidates)
        best_values.append(best)
    return summarize(best_values)


def same_candidate_control(candidate: dict, labels: dict[str, str], observed: float) -> dict:
    rng = random.Random(RANDOM_SEED + 1)
    pairs = all_pairs()
    label_values = [labels[pair] for pair in pairs]
    values = []
    shuffled = label_values[:]
    for _trial in range(TRIALS):
        rng.shuffle(shuffled)
        pseudo = make_pseudo_pair_table(pairs, shuffled)
        values.append(score_prediction(pseudo, candidate["pair_order"], candidate["predicted"])["accuracy"])
    summary = summarize(values)
    summary["p_ge_observed"] = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
    return summary


def summarize(values: list[float]) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    return {
        "trials": len(values),
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
    }


def materialize_candidate(template: dict, pair_orders: dict[str, list[str]], symbol_orders: dict[str, list[str]], symbol_counts: Counter[str]) -> dict:
    pair_order = pair_orders[template["pair_order_id"]]
    symbol_order = symbol_orders[template["symbol_order_id"]]
    sequence = ALGORITHMS[template["algorithm"]](symbol_order, symbol_counts)
    predicted = list(reversed(sequence)) if template["reverse"] else sequence
    return {**template, "pair_order": pair_order, "predicted": predicted}


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    events = events_by_book()
    if MANIFEST_JSON.exists():
        manifest = load_json(MANIFEST_JSON)
        holdout_books = set(manifest["book_holdouts"])
        train_books = set(manifest["book_training"])
    else:
        books = sorted(events, key=numeric_key)
        holdout_books = {book for idx, book in enumerate(books) if idx % 7 == 0}
        train_books = set(books) - holdout_books

    labels = {pair: primary_pair_symbol(pair_table, pair) for pair in all_pairs()}
    symbol_counts = Counter(labels.values())

    train_stats = usage_stats(train_books, events)
    holdout_stats = usage_stats(holdout_books, events)
    train_pair_orders = pair_orders_from_usage(train_stats)
    holdout_pair_orders = pair_orders_from_usage(holdout_stats)
    symbol_orders = symbol_orders_from_training(train_books, events, symbol_counts)

    candidates = build_candidates(train_pair_orders, symbol_orders, symbol_counts)
    train_rows = evaluate_candidates(pair_table, candidates)
    best_train = train_rows[0]
    control = control_distribution(candidates, labels)
    control["p_ge_observed"] = (
        "not_computed"
        if not train_rows
        else None
    )

    # Compute p after we know the observed score; kept separate so `summarize`
    # can remain a plain descriptive helper.
    rng = random.Random(RANDOM_SEED)
    pairs = all_pairs()
    label_values = [labels[pair] for pair in pairs]
    shuffled = label_values[:]
    ge = 0
    for _trial in range(TRIALS):
        rng.shuffle(shuffled)
        pseudo = make_pseudo_pair_table(pairs, shuffled)
        best = max(score_prediction(pseudo, candidate["pair_order"], candidate["predicted"])["accuracy"] for candidate in candidates)
        ge += best >= best_train["accuracy"]
    control["p_ge_observed"] = (ge + 1) / (TRIALS + 1)

    train_best_template = {
        key: best_train[key]
        for key in ["pair_order_id", "symbol_order_id", "algorithm", "reverse"]
    }
    holdout_candidate = materialize_candidate(train_best_template, holdout_pair_orders, symbol_orders, symbol_counts)
    holdout_score = score_prediction(pair_table, holdout_candidate["pair_order"], holdout_candidate["predicted"])
    holdout_control = same_candidate_control(holdout_candidate, labels, holdout_score["accuracy"])

    verdict = "rejected_control"
    if best_train["accuracy"] >= 0.55 and control["p_ge_observed"] <= 0.01 and holdout_control["p_ge_observed"] <= 0.05:
        verdict = "candidate_generator_usage_driven"

    result = {
        "schema": "usage_driven_pair_placement_results.v1",
        "random_seed": RANDOM_SEED,
        "trials": TRIALS,
        "train_books": sorted(train_books, key=numeric_key),
        "holdout_books": sorted(holdout_books, key=numeric_key),
        "candidate_count": len(candidates),
        "best_train": best_train,
        "train_best_control": control,
        "holdout_same_rule": {
            **train_best_template,
            **holdout_score,
            "control": holdout_control,
        },
        "top_train_rows": train_rows[:30],
        "usage_pair_order_examples": {
            "train_usage_count_desc": train_pair_orders["usage_count_desc"][:20],
            "train_first_use_asc": train_pair_orders["first_use_asc"][:20],
            "holdout_usage_count_desc": holdout_pair_orders["usage_count_desc"][:20],
            "holdout_first_use_asc": holdout_pair_orders["first_use_asc"][:20],
        },
        "verdict": verdict,
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Usage-Driven Pair Placement Search",
        "",
        "Generated by `usage_driven_pair_placement_search.py`.",
        "",
        "This pass asks whether the exact 55-cell pair table can be reconstructed",
        "by ordering numeric pair cells according to corpus usage, then allocating",
        "the known homophone inventory with simple human-scale procedures.",
        "",
        "## Best Train Rule",
        "",
        "| Pair order | Symbol order | Algorithm | Reverse | Accuracy | Control p |",
        "|---|---|---|---|---:|---:|",
        (
            f"| `{best_train['pair_order_id']}` | `{best_train['symbol_order_id']}` | "
            f"`{best_train['algorithm']}` | `{best_train['reverse']}` | "
            f"{best_train['correct']}/{best_train['total']} ({best_train['accuracy']:.3f}) | "
            f"{control['p_ge_observed']:.3f} |"
        ),
        "",
        "## Same Rule On Holdout Usage",
        "",
        "| Accuracy | Same-candidate p |",
        "|---:|---:|",
        f"| {holdout_score['correct']}/{holdout_score['total']} ({holdout_score['accuracy']:.3f}) | {holdout_control['p_ge_observed']:.3f} |",
        "",
        "## Top Train Rows",
        "",
        "| Pair order | Symbol order | Algorithm | Reverse | Accuracy |",
        "|---|---|---|---|---:|",
    ]
    for row in train_rows[:10]:
        lines.append(
            f"| `{row['pair_order_id']}` | `{row['symbol_order_id']}` | `{row['algorithm']}` | "
            f"`{row['reverse']}` | {row['correct']}/{row['total']} ({row['accuracy']:.3f}) |"
        )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"`{verdict}`.",
            "",
            "Usage-derived ordering does not currently reconstruct the exact pair-cell",
            "placement strongly enough to promote. This weakens the hypothesis that",
            "the cell layout was generated by sorting code cells by frequency, first",
            "use, or orientation bias. It remains compatible with a handmade table",
            "whose homophone inventory was frequency-weighted.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"verdict={verdict} best={best_train['accuracy']:.3f} holdout={holdout_score['accuracy']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
