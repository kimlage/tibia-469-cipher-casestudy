#!/usr/bin/env python3
"""Pair-context clustering search for the 469 pair table.

The frequency-weighted inventory explains how many homophone pair cells each
internal symbol receives, but not which cells. This pass tests whether the
observed homophone grouping is contextual: pair cells assigned to the same
symbol should have more similar raw code-neighbourhood distributions than a
random grouping with the same symbol inventory.

Context features are deliberately non-semantic and are computed from the raw
code stream: previous/next unordered pair, previous/next ordered code, and the
combined previous+next unordered-pair window. No plaintext is produced.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = HERE / "tape_based_formula_469.json"
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"

OUT_JSON = HERE / "pair_context_cluster_results.json"
OUT_MD = HERE / "pair_context_cluster_report.md"

RANDOM_SEED = 46920260623
CONTROL_TRIALS = 10000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    # The sole conflict {19,91} is represented by a primary label for pair-level
    # controls; ordered-code effects are tested in the orientation front.
    return sorted(row["symbols"])[0]


def load_token_sequences() -> dict[str, list[tuple[str, str]]]:
    occ = load_json(OCC_STREAMS)["occ"]
    by_book: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for _symbol, rows in occ.items():
        for row in rows:
            code = row["code"]
            pair = "".join(sorted(code))
            by_book[str(row["book"])].append((int(row["pos"]), code, pair))
    return {
        book: [(code, pair) for _pos, code, pair in sorted(rows)]
        for book, rows in by_book.items()
    }


def build_context_counters(pairs: list[str]) -> tuple[dict[str, dict[str, Counter]], Counter]:
    contexts = {
        "prev_pair": {pair: Counter() for pair in pairs},
        "next_pair": {pair: Counter() for pair in pairs},
        "prev_code": {pair: Counter() for pair in pairs},
        "next_code": {pair: Counter() for pair in pairs},
        "pair_window": {pair: Counter() for pair in pairs},
    }
    counts: Counter[str] = Counter()
    for _book, seq in load_token_sequences().items():
        for index, (code, pair) in enumerate(seq):
            prev_code, prev_pair = seq[index - 1] if index else ("<s>", "<s>")
            next_code, next_pair = seq[index + 1] if index + 1 < len(seq) else ("</s>", "</s>")
            counts[pair] += 1
            contexts["prev_pair"][pair][prev_pair] += 1
            contexts["next_pair"][pair][next_pair] += 1
            contexts["prev_code"][pair][prev_code] += 1
            contexts["next_code"][pair][next_code] += 1
            contexts["pair_window"][pair][f"{prev_pair}_{next_pair}"] += 1
    return contexts, counts


def jsd(left: Counter, right: Counter) -> float:
    left_total = sum(left.values())
    right_total = sum(right.values())
    if not left_total or not right_total:
        return 0.0
    out = 0.0
    for key in set(left) | set(right):
        p = left.get(key, 0) / left_total
        q = right.get(key, 0) / right_total
        m = (p + q) / 2.0
        if p:
            out += 0.5 * p * math.log2(p / m)
        if q:
            out += 0.5 * q * math.log2(q / m)
    return out


def distance_matrices(pairs: list[str], contexts: dict[str, dict[str, Counter]]) -> dict[str, list[list[float]]]:
    matrices = {}
    for feature, by_pair in contexts.items():
        matrix = [[0.0 for _ in pairs] for _ in pairs]
        for left_index, left in enumerate(pairs):
            for right_index in range(left_index + 1, len(pairs)):
                right = pairs[right_index]
                value = jsd(by_pair[left], by_pair[right])
                matrix[left_index][right_index] = value
                matrix[right_index][left_index] = value
        matrices[feature] = matrix
    return matrices


def same_label_pairs(labels: list[str]) -> list[tuple[int, int]]:
    by_symbol: dict[str, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        by_symbol[label].append(index)
    out = []
    for indices in by_symbol.values():
        for pos, left in enumerate(indices):
            for right in indices[pos + 1 :]:
                out.append((left, right))
    return out


def weighted_within_jsd(labels: list[str], matrix: list[list[float]], counts: list[int]) -> float:
    numer = 0.0
    denom = 0.0
    for left, right in same_label_pairs(labels):
        weight = math.sqrt(counts[left] * counts[right])
        numer += matrix[left][right] * weight
        denom += weight
    return numer / denom if denom else 0.0


def unweighted_within_jsd(labels: list[str], matrix: list[list[float]]) -> float:
    pairs = same_label_pairs(labels)
    return sum(matrix[left][right] for left, right in pairs) / len(pairs)


def nearest_same_label_fraction(labels: list[str], matrix: list[list[float]]) -> float:
    hits = 0
    for index, label in enumerate(labels):
        nearest = min(
            (matrix[index][other], other)
            for other in range(len(labels))
            if other != index
        )[1]
        hits += labels[nearest] == label
    return hits / len(labels)


def metrics(labels: list[str], matrices: dict[str, list[list[float]]], counts: list[int]) -> dict:
    out = {}
    for feature, matrix in matrices.items():
        out[f"{feature}_weighted_jsd"] = weighted_within_jsd(labels, matrix, counts)
        out[f"{feature}_unweighted_jsd"] = unweighted_within_jsd(labels, matrix)
    out["pair_window_nearest_same_fraction"] = nearest_same_label_fraction(labels, matrices["pair_window"])
    return out


def summarize(values: list[float], observed: float, low_is_good: bool) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    if low_is_good:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    else:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "z_good_direction": z,
        "p_good_direction": p,
        "control_min": min(values),
        "control_max": max(values),
    }


def controls(labels: list[str], observed: dict, matrices: dict[str, list[list[float]]], counts: list[int]) -> dict:
    rng = random.Random(RANDOM_SEED)
    sampled = {key: [] for key in observed}
    current = labels[:]
    for _trial in range(CONTROL_TRIALS):
        rng.shuffle(current)
        row = metrics(current, matrices, counts)
        for key, value in row.items():
            sampled[key].append(value)

    directions = {
        key: not key.endswith("_nearest_same_fraction")
        for key in observed
    }
    rows = []
    for key, values in sampled.items():
        summary = summarize(values, observed[key], low_is_good=directions[key])
        rows.append(
            {
                "metric": key,
                "direction": "low" if directions[key] else "high",
                **summary,
            }
        )
    for row in rows:
        row["bonferroni_p"] = min(1.0, row["p_good_direction"] * len(rows))
        if row["bonferroni_p"] <= 0.01:
            row["verdict"] = "candidate"
        elif row["bonferroni_p"] <= 0.05:
            row["verdict"] = "not_promoted_hint"
        else:
            row["verdict"] = "rejected_control"
    rows.sort(key=lambda row: row["bonferroni_p"])
    return {"metric_rows": rows, "best": rows[0]}


def class_summary(labels: list[str], pairs: list[str], matrix: list[list[float]], counts: list[int]) -> list[dict]:
    by_symbol: dict[str, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        by_symbol[label].append(index)
    rows = []
    for symbol, indices in sorted(by_symbol.items()):
        if len(indices) < 2:
            continue
        distances = []
        weights = []
        for pos, left in enumerate(indices):
            for right in indices[pos + 1 :]:
                distances.append(matrix[left][right])
                weights.append(math.sqrt(counts[left] * counts[right]))
        weighted = sum(value * weight for value, weight in zip(distances, weights)) / sum(weights)
        rows.append(
            {
                "symbol": symbol,
                "pair_count": len(indices),
                "token_count": sum(counts[index] for index in indices),
                "weighted_pair_window_jsd": weighted,
                "unweighted_pair_window_jsd": sum(distances) / len(distances),
                "pairs": [pairs[index] for index in indices],
            }
        )
    rows.sort(key=lambda row: row["weighted_pair_window_jsd"])
    return rows


def write_report(result: dict) -> None:
    lines = [
        "# Pair Context Cluster Search",
        "",
        "Generated by `pair_context_cluster_search.py`.",
        "",
        "This pass tests whether pair cells assigned to the same internal symbol",
        "have more similar raw code-neighbourhood contexts than random pair-label",
        "groupings with the same homophone inventory. It does not translate 469.",
        "",
        "## Controlled Metrics",
        "",
        "| Metric | Observed | Control mean | z | p | Bonferroni p | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["control"]["metric_rows"]:
        lines.append(
            f"| `{row['metric']}` | {row['observed']:.6f} | {row['control_mean']:.6f} | "
            f"{row['z_good_direction']:.2f} | {row['p_good_direction']:.5f} | "
            f"{row['bonferroni_p']:.5f} | `{row['verdict']}` |"
        )
    lines += [
        "",
        "## Most Context-Compact Classes",
        "",
        "| Symbol | Pair cells | Token count | Weighted pair-window JSD | Pairs |",
        "|---|---:|---:|---:|---|",
    ]
    for row in result["class_summary"][:10]:
        lines.append(
            f"| `{row['symbol']}` | {row['pair_count']} | {row['token_count']} | "
            f"{row['weighted_pair_window_jsd']:.6f} | `{', '.join(row['pairs'])}` |"
        )
    lines += ["", "## Verdict", ""]
    if result["verdict"] == "candidate_contextual_homophone_grouping":
        lines.append(
            "Same-symbol pair cells are context-clustered beyond inventory-preserving "
            "controls. This is a mechanical clue for the homophone grouping layer, "
            "not a deterministic formula for every cell."
        )
    elif result["verdict"] == "not_promoted_context_cluster_hint":
        lines.append(
            "The strongest context-clustering metric is suggestive but misses the "
            "strict promotion gate after multiple-test correction. Track it as a "
            "mechanical hint for homophone grouping, not as an accepted formula."
        )
    else:
        lines.append(
            "No same-symbol context clustering metric survives the control gate. "
            "The exact pair grouping remains unexplained by raw code-neighbourhood context."
        )
    lines += ["", f"Translation delta: `{result['translation_delta']}`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pairs = all_pairs()
    labels = [primary_pair_symbol(formula["pair_table"], pair) for pair in pairs]
    contexts, count_by_pair = build_context_counters(pairs)
    counts = [count_by_pair[pair] for pair in pairs]
    matrices = distance_matrices(pairs, contexts)
    observed = metrics(labels, matrices, counts)
    control = controls(labels, observed, matrices, counts)
    if control["best"]["bonferroni_p"] <= 0.01:
        verdict = "candidate_contextual_homophone_grouping"
    elif control["best"]["bonferroni_p"] <= 0.05:
        verdict = "not_promoted_context_cluster_hint"
    else:
        verdict = "rejected_control"
    result = {
        "schema": "pair_context_cluster_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "pair_count": len(pairs),
        "token_count": sum(counts),
        "observed": observed,
        "control": control,
        "class_summary": class_summary(labels, pairs, matrices["pair_window"], counts),
        "verdict": verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} best={control['best']['metric']} "
        f"p={control['best']['p_good_direction']:.5f} "
        f"bonferroni={control['best']['bonferroni_p']:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
