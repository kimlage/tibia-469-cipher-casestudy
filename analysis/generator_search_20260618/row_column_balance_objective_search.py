#!/usr/bin/env python3
"""Row/column balance objective search for the 469 pair table.

This pass tests a human-plausible placement objective: after choosing the
homophone inventory, maybe the author distributed cells to balance symbols over
digits, rows, columns, borders, or local incidence. A true construction
objective should make the observed table unusually good versus
inventory-preserving shuffles and hard to improve by simple label swaps.

Mechanical only. No plaintext or translation is promoted.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "row_column_balance_objective_results.json"
OUT_MD = HERE / "row_column_balance_objective_report.md"

SIGMA = list("*ABCEFILNORSTV")
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 5000
GREEDY_MAX_SWAPS = 80


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[tuple[int, int]]:
    return [(a, b) for a in range(10) for b in range(a, 10)]


def primary_pair_symbol(pair_table: dict, pair: tuple[int, int]) -> str:
    row = pair_table[f"{pair[0]}{pair[1]}"]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if not total:
        return 0.0
    return -sum((count / total) * math.log2(count / total) for count in counter.values() if count)


def incident_counts(pairs: list[tuple[int, int]], labels: list[str], loop_twice: bool = False) -> dict[int, Counter[str]]:
    counts = {digit: Counter() for digit in range(10)}
    for (a, b), label in zip(pairs, labels):
        counts[a][label] += 1
        if b != a or loop_twice:
            counts[b][label] += 1
    return counts


def line_counts(pairs: list[tuple[int, int]], labels: list[str]) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for (a, b), label in zip(pairs, labels):
        counts[f"row_{a}"][label] += 1
        counts[f"col_{b}"][label] += 1
        counts[f"sum_{a + b}"][label] += 1
        counts[f"diff_{b - a}"][label] += 1
        if a == b:
            counts["diag"][label] += 1
        if a in (0, 9) or b in (0, 9):
            counts["border"][label] += 1
    return counts


def same_symbol_shared_digit(pairs: list[tuple[int, int]], labels: list[str]) -> int:
    total = 0
    for i, (a1, b1) in enumerate(pairs):
        d1 = {a1, b1}
        for j in range(i + 1, len(pairs)):
            if labels[i] != labels[j]:
                continue
            a2, b2 = pairs[j]
            if d1.intersection({a2, b2}):
                total += 1
    return total


def same_symbol_line_runs(pairs: list[tuple[int, int]], labels: list[str]) -> int:
    label_by_pair = dict(zip(pairs, labels))
    total = 0
    for a in range(10):
        row = [label_by_pair[(a, b)] for b in range(a, 10)]
        total += sum(1 for x, y in zip(row, row[1:]) if x == y)
    for b in range(10):
        col = [label_by_pair[(a, b)] for a in range(0, b + 1)]
        total += sum(1 for x, y in zip(col, col[1:]) if x == y)
    for diff in range(10):
        line = [label_by_pair[(a, a + diff)] for a in range(0, 10 - diff)]
        total += sum(1 for x, y in zip(line, line[1:]) if x == y)
    return total


def l2_against_expected(counts: dict[object, Counter[str]], global_counts: Counter[str], total_cells: int) -> float:
    value = 0.0
    for counter in counts.values():
        line_total = sum(counter.values())
        for symbol in SIGMA:
            expected = line_total * global_counts[symbol] / total_cells
            value += (counter[symbol] - expected) ** 2
    return value


def metrics(pairs: list[tuple[int, int]], labels: list[str]) -> dict[str, float]:
    global_counts = Counter(labels)
    inc = incident_counts(pairs, labels)
    inc_twice = incident_counts(pairs, labels, loop_twice=True)
    lines = line_counts(pairs, labels)
    entropies = [entropy(counter) for counter in inc.values()]
    max_shares = []
    for counter in inc.values():
        total = sum(counter.values())
        max_shares.append(max(counter.values()) / total if total else 0.0)
    return {
        "incident_entropy_sum": sum(entropies),
        "incident_min_entropy": min(entropies),
        "incident_max_share_sum": sum(max_shares),
        "incident_l2_expected": l2_against_expected(inc, global_counts, len(labels)),
        "incident_l2_expected_loop_twice": l2_against_expected(inc_twice, global_counts, len(labels)),
        "line_l2_expected": l2_against_expected(lines, global_counts, len(labels)),
        "same_symbol_shared_digit": float(same_symbol_shared_digit(pairs, labels)),
        "same_symbol_line_runs": float(same_symbol_line_runs(pairs, labels)),
    }


DIRECTION = {
    "incident_entropy_sum": "high",
    "incident_min_entropy": "high",
    "incident_max_share_sum": "low",
    "incident_l2_expected": "low",
    "incident_l2_expected_loop_twice": "low",
    "line_l2_expected": "low",
    "same_symbol_shared_digit": "low",
    "same_symbol_line_runs": "low",
}


def summarize_controls(values: list[float], observed: float, direction: str) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    if direction == "high":
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "control_min": min(values),
        "control_max": max(values),
        "z_good_direction": z,
        "p_good_direction": p,
    }


def better(value: float, current: float, direction: str) -> bool:
    return value > current if direction == "high" else value < current


def best_one_swap(pairs: list[tuple[int, int]], labels: list[str], metric_name: str) -> dict:
    direction = DIRECTION[metric_name]
    observed = metrics(pairs, labels)[metric_name]
    best_labels = labels[:]
    best_value = observed
    best_swap = None
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            if labels[i] == labels[j]:
                continue
            trial = labels[:]
            trial[i], trial[j] = trial[j], trial[i]
            value = metrics(pairs, trial)[metric_name]
            if better(value, best_value, direction):
                best_value = value
                best_labels = trial
                best_swap = [f"{pairs[i][0]}{pairs[i][1]}", f"{pairs[j][0]}{pairs[j][1]}"]
    return {
        "metric": metric_name,
        "direction": direction,
        "observed": observed,
        "best_one_swap": best_value,
        "swap": best_swap,
        "improved": best_swap is not None,
        "best_one_swap_labels": best_labels,
    }


def greedy_optimize(pairs: list[tuple[int, int]], labels: list[str], metric_name: str) -> dict:
    current = labels[:]
    swaps = []
    for _ in range(GREEDY_MAX_SWAPS):
        step = best_one_swap(pairs, current, metric_name)
        if not step["improved"]:
            break
        a, b = step["swap"]
        idx_a = next(idx for idx, pair in enumerate(pairs) if f"{pair[0]}{pair[1]}" == a)
        idx_b = next(idx for idx, pair in enumerate(pairs) if f"{pair[0]}{pair[1]}" == b)
        current[idx_a], current[idx_b] = current[idx_b], current[idx_a]
        swaps.append({"swap": step["swap"], "value": step["best_one_swap"]})
    return {
        "metric": metric_name,
        "swaps": swaps[:30],
        "swap_count": len(swaps),
        "final_value": metrics(pairs, current)[metric_name],
    }


def verdict(rows: list[dict]) -> str:
    best_p = min(row["control"]["p_good_direction"] for row in rows)
    bonf = min(1.0, best_p * len(rows))
    locally_optimal = all(not row["one_swap"]["improved"] for row in rows if row["control"]["p_good_direction"] <= 0.05)
    if bonf <= 0.01 and locally_optimal:
        return "candidate_balance_objective"
    if bonf <= 0.05:
        return "weak_balance_signal_not_local_optimum" if not locally_optimal else "weak_balance_signal"
    return "rejected_control"


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pairs = natural_pairs()
    labels = [primary_pair_symbol(formula["pair_table"], pair) for pair in pairs]
    observed_metrics = metrics(pairs, labels)
    rng = random.Random(RANDOM_SEED)
    control_values = {name: [] for name in observed_metrics}
    for _ in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        row = metrics(pairs, shuffled)
        for name, value in row.items():
            control_values[name].append(value)
    rows = []
    for name, observed in observed_metrics.items():
        ctrl = summarize_controls(control_values[name], observed, DIRECTION[name])
        one = best_one_swap(pairs, labels, name)
        greedy = greedy_optimize(pairs, labels, name)
        rows.append(
            {
                "metric": name,
                "direction": DIRECTION[name],
                "control": ctrl,
                "one_swap": {k: v for k, v in one.items() if k != "best_one_swap_labels"},
                "greedy": greedy,
            }
        )
    rows.sort(key=lambda row: (row["control"]["p_good_direction"], -row["control"]["z_good_direction"], row["metric"]))
    result_verdict = verdict(rows)
    result = {
        "schema": "row_column_balance_objective_results.v1",
        "translation_delta": "NONE",
        "control_trials": CONTROL_TRIALS,
        "metrics": rows,
        "verdict": result_verdict,
    }
    write_json(OUT_JSON, result)

    best = rows[0]
    lines = [
        "# Row/Column Balance Objective Search",
        "",
        "Generated by `row_column_balance_objective_search.py`.",
        "",
        "This pass tests whether the observed pair-cell placement looks like it",
        "was optimized to distribute the known homophone inventory smoothly over",
        "digits, rows, columns, diagonals, or local same-symbol adjacencies.",
        "It is mechanical only and assigns no plaintext.",
        "",
        "## Summary",
        "",
        "| Strongest metric | Direction | Observed | Control mean | z | p | One-swap improves? | Greedy swaps | Verdict |",
        "|---|---|---:|---:|---:|---:|---|---:|---|",
        f"| `{best['metric']}` | {best['direction']} | {best['control']['observed']:.3f} | {best['control']['control_mean']:.3f} | {best['control']['z_good_direction']:.2f} | {best['control']['p_good_direction']:.5f} | {best['one_swap']['improved']} | {best['greedy']['swap_count']} | `{result_verdict}` |",
        "",
        "## Metrics",
        "",
        "| Metric | Direction | Observed | Mean | z | p | One-swap value | Greedy final |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['metric']}` | {row['direction']} | {row['control']['observed']:.3f} | "
            f"{row['control']['control_mean']:.3f} | {row['control']['z_good_direction']:.2f} | "
            f"{row['control']['p_good_direction']:.5f} | {row['one_swap']['best_one_swap']:.3f} | "
            f"{row['greedy']['final_value']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A placement objective is plausible only if the observed table is",
            "exceptional versus inventory-preserving shuffles and is at least a",
            "local optimum under inventory-preserving swaps. This pass rejects",
            "metrics that can be improved by a single swap or by a short greedy",
            "swap sequence.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "best={} p={:.5f} one_swap={} verdict={}".format(
            best["metric"],
            best["control"]["p_good_direction"],
            best["one_swap"]["improved"],
            result_verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
