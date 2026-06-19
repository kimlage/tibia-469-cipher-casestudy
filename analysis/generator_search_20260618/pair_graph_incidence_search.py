#!/usr/bin/env python3
"""Graph-incidence search for the 469 pair table.

The unordered-pair table can be viewed as a colored graph over digits 0..9
with loops. If the original formula assigned symbols by digit affinities,
each symbol's incident-degree vector might show compact structure: contiguous
digit spans, smooth digit-order profiles, modular bias, or hub concentration.

This pass tests those graph-level signatures against controls that preserve
the exact symbol inventory and shuffle labels over the 55 unordered cells.
It does not translate 469.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "pair_graph_incidence_results.json"
OUT_MD = HERE / "pair_graph_incidence_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260621
CONTROL_TRIALS = 20000

DIGIT_ORDERS = {
    "natural": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    "natural_rev": [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
    "keypad": [1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
    "numpad": [7, 8, 9, 4, 5, 6, 1, 2, 3, 0],
    "center_out": [4, 5, 3, 6, 2, 7, 1, 8, 0, 9],
    "edges_in": [0, 9, 1, 8, 2, 7, 3, 6, 4, 5],
}


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
    return sorted(row["symbols"])[0]


def labels_from_formula(formula: dict) -> list[str]:
    return [primary_pair_symbol(formula["pair_table"], pair) for pair in all_pairs()]


def degree_vectors(labels: list[str]) -> dict[str, list[int]]:
    out = {symbol: [0] * 10 for symbol in SIGMA}
    for pair, symbol in zip(all_pairs(), labels):
        a, b = int(pair[0]), int(pair[1])
        out[symbol][a] += 1
        out[symbol][b] += 1
    return out


def entropy(values: list[int]) -> float:
    total = sum(values)
    if not total:
        return 0.0
    result = 0.0
    for value in values:
        if value:
            p = value / total
            result -= p * math.log2(p)
    return result


def order_values(values: list[int], order: list[int]) -> list[int]:
    return [values[digit] for digit in order]


def active_span(values: list[int], order: list[int]) -> int:
    ordered = order_values(values, order)
    active = [idx for idx, value in enumerate(ordered) if value]
    return max(active) - min(active) + 1 if active else 0


def smooth_abs(values: list[int], order: list[int]) -> int:
    ordered = order_values(values, order)
    return sum(abs(ordered[index] - ordered[index - 1]) for index in range(1, len(ordered)))


def metrics(labels: list[str]) -> dict:
    vectors = degree_vectors(labels)
    base = {
        "sum_entropy": sum(entropy(vector) for vector in vectors.values()),
        "sum_max_share": sum(max(vector) / sum(vector) if sum(vector) else 0.0 for vector in vectors.values()),
        "sum_active_count": sum(sum(1 for value in vector if value) for vector in vectors.values()),
        "sum_mod_bias": 0.0,
    }
    for vector in vectors.values():
        total = sum(vector)
        best = 0.0
        for modulus in [2, 3, 4, 5]:
            for residue in range(modulus):
                if total:
                    best = max(best, sum(vector[digit] for digit in range(10) if digit % modulus == residue) / total)
        base["sum_mod_bias"] += best

    order_metrics = {}
    for order_id, order in DIGIT_ORDERS.items():
        order_metrics[f"smooth_abs_{order_id}"] = sum(smooth_abs(vector, order) for vector in vectors.values())
        order_metrics[f"active_span_{order_id}"] = sum(active_span(vector, order) for vector in vectors.values())
    base["best_smooth_abs"] = min(value for key, value in order_metrics.items() if key.startswith("smooth_abs_"))
    base["best_smooth_order"] = min(
        (value, key.removeprefix("smooth_abs_")) for key, value in order_metrics.items() if key.startswith("smooth_abs_")
    )[1]
    base["best_active_span"] = min(value for key, value in order_metrics.items() if key.startswith("active_span_"))
    base["best_active_span_order"] = min(
        (value, key.removeprefix("active_span_")) for key, value in order_metrics.items() if key.startswith("active_span_")
    )[1]
    base.update(order_metrics)
    return base


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


def control(observed_labels: list[str]) -> dict:
    rng = random.Random(RANDOM_SEED)
    values = {
        "sum_entropy": [],
        "sum_max_share": [],
        "sum_active_count": [],
        "sum_mod_bias": [],
        "best_smooth_abs": [],
        "best_active_span": [],
    }
    labels = observed_labels[:]
    for _trial in range(CONTROL_TRIALS):
        rng.shuffle(labels)
        current = metrics(labels)
        for key in values:
            values[key].append(current[key])
    return values


def write_report(result: dict) -> None:
    lines = [
        "# Pair Graph Incidence Search",
        "",
        "Generated by `pair_graph_incidence_search.py`.",
        "",
        "This pass treats the 55 unordered cells as a colored graph over digits",
        "and tests whether symbol incidence degrees reveal a compact digit-affinity",
        "formula.",
        "",
        "## Metrics",
        "",
        "| Metric | Observed | Control mean | z | p | Verdict |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in result["metric_rows"]:
        lines.append(
            f"| `{row['metric']}` | {row['observed']:.3f} | {row['control_mean']:.3f} | "
            f"{row['z_good_direction']:.2f} | {row['p_good_direction']:.5f} | `{row['verdict']}` |"
        )
    lines += [
        "",
        "Best digit orders:",
        "",
        f"- Smoothness: `{result['observed_metrics']['best_smooth_order']}`.",
        f"- Active span: `{result['observed_metrics']['best_active_span_order']}`.",
        "",
        "## Degree Vectors",
        "",
        "| Symbol | Degree vector over digits 0..9 |",
        "|---|---|",
    ]
    for symbol, vector in result["degree_vectors"].items():
        lines.append(f"| `{symbol}` | `{vector}` |")
    lines += [
        "",
        "## Verdict",
        "",
    ]
    if result["verdict"] == "rejected_control":
        lines.append(
            "No graph-incidence signature survives the control/multiple-comparison gate. "
            "The pair table still looks frequency-weighted in class size, but its "
            "cell placement is not explained by a compact digit-incidence rule."
        )
    else:
        lines.append("A graph-incidence signature survived controls; treat as mechanical only.")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    observed_labels = labels_from_formula(formula)
    observed = metrics(observed_labels)
    controls = control(observed_labels)
    tested = {
        "sum_entropy": True,
        "sum_max_share": False,
        "sum_active_count": True,
        "sum_mod_bias": False,
        "best_smooth_abs": True,
        "best_active_span": True,
    }
    rows = []
    for metric, low_is_good in tested.items():
        summary = summarize(controls[metric], observed[metric], low_is_good=low_is_good)
        rows.append(
            {
                "metric": metric,
                **summary,
                "direction": "low" if low_is_good else "high",
                "bonferroni_p": min(1.0, summary["p_good_direction"] * len(tested)),
                "verdict": "candidate" if summary["p_good_direction"] * len(tested) <= 0.01 else "rejected_control",
            }
        )
    rows.sort(key=lambda row: row["bonferroni_p"])
    verdict = "candidate_graph_incidence_formula" if rows[0]["bonferroni_p"] <= 0.01 else "rejected_control"
    result = {
        "schema": "pair_graph_incidence_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "observed_metrics": observed,
        "degree_vectors": degree_vectors(observed_labels),
        "metric_rows": rows,
        "best_metric": rows[0],
        "verdict": verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} best={rows[0]['metric']} p={rows[0]['p_good_direction']:.5f} "
        f"bonferroni={rows[0]['bonferroni_p']:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
