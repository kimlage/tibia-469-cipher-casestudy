#!/usr/bin/env python3
"""Marginal/diagonal signature search for the 469 pair table.

Many searches try to recover the exact 55-cell placement. This pass asks a
weaker but useful question: do rows, columns, diagonals, borders, or digit
marginals show a compact signature that is unlikely under symbol-inventory
preserving shuffles?

Mechanical only. No plaintext is promoted.
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

OUT_JSON = HERE / "pair_marginal_signature_results.json"
OUT_MD = HERE / "pair_marginal_signature_report.md"

RANDOM_SEED = 46920260624
CONTROL_TRIALS = 30000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def primary_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def entropy(labels: list[str]) -> float:
    counts = Counter(labels)
    total = len(labels)
    out = 0.0
    for count in counts.values():
        p = count / total
        out -= p * math.log2(p)
    return out


def line_groups() -> dict[str, dict[str, list[str]]]:
    pairs = all_pairs()
    groups: dict[str, dict[str, list[str]]] = {
        "row": {},
        "column": {},
        "diagonal_diff": {},
        "anti_diagonal_sum": {},
        "border": {},
        "digit_incidence": {},
    }
    for i in range(10):
        groups["row"][str(i)] = [f"{i}{j}" for j in range(i, 10)]
        groups["column"][str(i)] = [f"{j}{i}" for j in range(i + 1)]
        groups["digit_incidence"][str(i)] = [pair for pair in pairs if str(i) in pair]
    for diff in range(10):
        groups["diagonal_diff"][str(diff)] = [pair for pair in pairs if int(pair[1]) - int(pair[0]) == diff]
    for summ in range(19):
        groups["anti_diagonal_sum"][str(summ)] = [pair for pair in pairs if int(pair[0]) + int(pair[1]) == summ]
    groups["border"]["has_zero_or_nine"] = [pair for pair in pairs if pair[0] in "09" or pair[1] in "09"]
    groups["border"]["interior"] = [pair for pair in pairs if not (pair[0] in "09" or pair[1] in "09")]
    groups["border"]["diagonal"] = [f"{i}{i}" for i in range(10)]
    groups["border"]["off_diagonal"] = [pair for pair in pairs if pair[0] != pair[1]]
    return groups


def metrics(labels_by_pair: dict[str, str]) -> dict[str, float | int | str | dict]:
    groups = line_groups()
    diagonal = groups["border"]["diagonal"]
    diagonal_labels = [labels_by_pair[pair] for pair in diagonal]
    e_symbol = "E"

    line_rows = []
    for kind in ["row", "column", "diagonal_diff", "anti_diagonal_sum", "digit_incidence"]:
        for line_id, pairs in groups[kind].items():
            labels = [labels_by_pair[pair] for pair in pairs]
            counts = Counter(labels)
            line_rows.append(
                {
                    "kind": kind,
                    "line_id": line_id,
                    "length": len(pairs),
                    "max_count": max(counts.values()),
                    "max_fraction": max(counts.values()) / len(labels),
                    "entropy": entropy(labels),
                    "labels": "".join(labels),
                    "pairs": pairs,
                }
            )

    long_lines = [row for row in line_rows if row["length"] >= 5]
    border_labels = [labels_by_pair[pair] for pair in groups["border"]["has_zero_or_nine"]]
    interior_labels = [labels_by_pair[pair] for pair in groups["border"]["interior"]]

    return {
        "diagonal_sequence": "".join(diagonal_labels),
        "diagonal_e_count": diagonal_labels.count(e_symbol),
        "diagonal_max_symbol_count": max(Counter(diagonal_labels).values()),
        "diagonal_entropy": entropy(diagonal_labels),
        "diagonal_distinct_symbols": len(set(diagonal_labels)),
        "best_long_line_max_fraction": max(row["max_fraction"] for row in long_lines),
        "best_long_line": max(long_lines, key=lambda row: (row["max_fraction"], row["length"], row["kind"], row["line_id"])),
        "mean_long_line_entropy": sum(row["entropy"] for row in long_lines) / len(long_lines),
        "low_entropy_line_count": sum(1 for row in long_lines if row["entropy"] <= 1.5),
        "border_e_count": border_labels.count(e_symbol),
        "interior_e_count": interior_labels.count(e_symbol),
        "border_entropy": entropy(border_labels),
        "interior_entropy": entropy(interior_labels),
        "line_rows": line_rows,
    }


def summarize(values: list[float], observed: float, high_is_good: bool) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    if high_is_good:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "z_good_direction": z,
        "p_good_direction": p,
        "control_min": min(values),
        "control_max": max(values),
    }


def controls(observed_labels: dict[str, str], observed: dict) -> dict:
    rng = random.Random(RANDOM_SEED)
    pairs = all_pairs()
    labels = [observed_labels[pair] for pair in pairs]
    values = {
        "diagonal_e_count": [],
        "diagonal_max_symbol_count": [],
        "diagonal_entropy": [],
        "diagonal_distinct_symbols": [],
        "best_long_line_max_fraction": [],
        "mean_long_line_entropy": [],
        "low_entropy_line_count": [],
        "border_e_count": [],
        "border_entropy": [],
    }
    current = labels[:]
    for _trial in range(CONTROL_TRIALS):
        rng.shuffle(current)
        shuffled = dict(zip(pairs, current))
        row = metrics(shuffled)
        for key in values:
            values[key].append(row[key])
    directions = {
        "diagonal_e_count": True,
        "diagonal_max_symbol_count": True,
        "diagonal_entropy": False,
        "diagonal_distinct_symbols": False,
        "best_long_line_max_fraction": True,
        "mean_long_line_entropy": False,
        "low_entropy_line_count": True,
        "border_e_count": True,
        "border_entropy": False,
    }
    rows = []
    for key, vals in values.items():
        summary = summarize(vals, observed[key], high_is_good=directions[key])
        rows.append(
            {
                "metric": key,
                "direction": "high" if directions[key] else "low",
                **summary,
                "bonferroni_p": min(1.0, summary["p_good_direction"] * len(values)),
            }
        )
    rows.sort(key=lambda row: row["bonferroni_p"])
    return {"metric_rows": rows, "best": rows[0]}


def write_report(result: dict) -> None:
    observed = result["observed"]
    lines = [
        "# Pair Marginal Signature Search",
        "",
        "Generated by `pair_marginal_signature_search.py`.",
        "",
        "This pass tests whether diagonals, rows, columns, borders, or digit",
        "marginals carry a compact pair-table signature beyond shuffled controls.",
        "It does not translate 469.",
        "",
        "## Observed Highlights",
        "",
        f"- Diagonal sequence: `{observed['diagonal_sequence']}`.",
        f"- Diagonal E count: {observed['diagonal_e_count']} / 10.",
        f"- Best long line: `{observed['best_long_line']['kind']}:{observed['best_long_line']['line_id']}` = `{observed['best_long_line']['labels']}`.",
        f"- Best long-line max fraction: {observed['best_long_line_max_fraction']:.3f}.",
        "",
        "## Controlled Metrics",
        "",
        "| Metric | Observed | Control mean | z | p | Bonferroni p | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["control"]["metric_rows"]:
        verdict = "candidate" if row["bonferroni_p"] <= 0.01 else "rejected_control"
        lines.append(
            f"| `{row['metric']}` | {row['observed']:.3f} | {row['control_mean']:.3f} | "
            f"{row['z_good_direction']:.2f} | {row['p_good_direction']:.5f} | "
            f"{row['bonferroni_p']:.5f} | `{verdict}` |"
        )
    lines += [
        "",
        "## Top Lines",
        "",
        "| Kind | ID | Length | Max fraction | Entropy | Labels |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in sorted(observed["line_rows"], key=lambda item: (-item["max_fraction"], -item["length"]))[:20]:
        lines.append(
            f"| `{row['kind']}` | `{row['line_id']}` | {row['length']} | "
            f"{row['max_fraction']:.3f} | {row['entropy']:.3f} | `{row['labels']}` |"
        )
    lines += ["", "## Verdict", ""]
    if result["verdict"] == "candidate_marginal_signature":
        lines.append("A marginal/diagonal signature survived controls. Treat as mechanical only.")
    else:
        lines.append(
            "No diagonal, marginal, row/column, anti-diagonal, or border statistic "
            "survives the inventory-preserving control gate. Marginals do not "
            "recover the original pair-table placement."
        )
    lines += ["", f"Translation delta: `{result['translation_delta']}`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    labels = {pair: primary_symbol(formula["pair_table"], pair) for pair in all_pairs()}
    observed = metrics(labels)
    control = controls(labels, observed)
    verdict = "candidate_marginal_signature" if control["best"]["bonferroni_p"] <= 0.01 else "rejected_control"
    result = {
        "schema": "pair_marginal_signature_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "observed": observed,
        "control": control,
        "verdict": verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} best={control['best']['metric']} "
        f"p={control['best']['p_good_direction']:.5f} bonferroni={control['best']['bonferroni_p']:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
