#!/usr/bin/env python3
"""Residual marginal/line signature search after fixed E-priority layer.

Whole-table marginal tests are dominated by the diagonal E clue. This pass
removes the exact local E/blocker layer first and asks whether the remaining
40 cells still carry row/column/diagonal/digit marginal structure.

Controls shuffle only residual labels. No plaintext is inferred.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OUT_JSON = HERE / "residual_marginal_after_e_results.json"
OUT_MD = HERE / "residual_marginal_after_e_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 5000
SYMBOLS = "*ABCEFILNORSTV"
PAIRS = [f"{a}{b}" for a in range(10) for b in range(a, 10)]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def primary_pair_symbol(pair_table: dict[str, Any], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def labels_from_formula() -> dict[str, str]:
    formula = load_json(FORMULA_JSON)
    return {pair: primary_pair_symbol(formula["pair_table"], pair) for pair in PAIRS}


def fixed_claim_pairs() -> set[str]:
    return {
        "11",
        "15",
        "33",
        "44",
        "45",
        "47",
        "48",
        "55",
        "57",
        "58",
        "66",
        "77",
        "78",
        "88",
        "99",
    }


def entropy(labels: list[str]) -> float:
    total = len(labels)
    if not total:
        return 0.0
    counts = Counter(labels)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def residual_pairs() -> list[str]:
    return [pair for pair in PAIRS if pair not in fixed_claim_pairs()]


def line_groups(pairs: list[str]) -> dict[str, dict[str, list[str]]]:
    groups: dict[str, dict[str, list[str]]] = {
        "row": defaultdict(list),
        "column": defaultdict(list),
        "diag_diff": defaultdict(list),
        "anti_sum": defaultdict(list),
        "digit_incidence": defaultdict(list),
        "border": defaultdict(list),
    }
    for pair in pairs:
        a, b = int(pair[0]), int(pair[1])
        groups["row"][str(a)].append(pair)
        groups["column"][str(b)].append(pair)
        groups["diag_diff"][str(b - a)].append(pair)
        groups["anti_sum"][str(a + b)].append(pair)
        groups["border"][str(int(a == 0 or b == 9))].append(pair)
        groups["digit_incidence"][str(a)].append(pair)
        if b != a:
            groups["digit_incidence"][str(b)].append(pair)
    return {kind: dict(rows) for kind, rows in groups.items()}


def metric_rows(labels: dict[str, str], pairs: list[str]) -> list[dict[str, Any]]:
    rows = []
    groups = line_groups(pairs)
    for kind, lines in groups.items():
        eligible = {line_id: line_pairs for line_id, line_pairs in lines.items() if len(line_pairs) >= 2}
        if not eligible:
            continue
        max_fracs = []
        entropies = []
        pure_count = 0
        low_entropy_count = 0
        best_line = None
        for line_id, line_pairs in eligible.items():
            line_labels = [labels[pair] for pair in line_pairs]
            counts = Counter(line_labels)
            max_count = max(counts.values())
            max_frac = max_count / len(line_pairs)
            h = entropy(line_labels)
            max_fracs.append(max_frac)
            entropies.append(h)
            pure_count += int(max_count == len(line_pairs))
            low_entropy_count += int(h <= 1.0)
            candidate = {
                "kind": kind,
                "line_id": line_id,
                "size": len(line_pairs),
                "labels": "".join(line_labels),
                "max_fraction": max_frac,
                "entropy": h,
            }
            if best_line is None or (max_frac, len(line_pairs), -h, line_id) > (
                best_line["max_fraction"],
                best_line["size"],
                -best_line["entropy"],
                best_line["line_id"],
            ):
                best_line = candidate
        rows.extend(
            [
                {
                    "metric": f"{kind}_best_max_fraction",
                    "value": max(max_fracs),
                    "high_is_good": True,
                    "best_line": best_line,
                },
                {
                    "metric": f"{kind}_mean_entropy",
                    "value": sum(entropies) / len(entropies),
                    "high_is_good": False,
                    "best_line": best_line,
                },
                {
                    "metric": f"{kind}_pure_line_count",
                    "value": pure_count,
                    "high_is_good": True,
                    "best_line": best_line,
                },
                {
                    "metric": f"{kind}_low_entropy_count",
                    "value": low_entropy_count,
                    "high_is_good": True,
                    "best_line": best_line,
                },
            ]
        )

    digit_vectors = {}
    for digit in range(10):
        touched = [pair for pair in pairs if str(digit) in pair]
        if touched:
            digit_vectors[str(digit)] = Counter(labels[pair] for pair in touched)
    max_digit_share = max((max(counter.values()) / sum(counter.values())) for counter in digit_vectors.values())
    sum_digit_entropy = sum(entropy(list(counter.elements())) for counter in digit_vectors.values())
    rows.append(
        {
            "metric": "digit_incidence_max_share",
            "value": max_digit_share,
            "high_is_good": True,
            "best_line": None,
        }
    )
    rows.append(
        {
            "metric": "digit_incidence_sum_entropy",
            "value": sum_digit_entropy,
            "high_is_good": False,
            "best_line": None,
        }
    )
    return rows


def controls(labels: dict[str, str], pairs: list[str], observed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    values = {row["metric"]: [] for row in observed_rows}
    residual_labels = [labels[pair] for pair in pairs]
    for _trial in range(CONTROL_TRIALS):
        shuffled_values = residual_labels[:]
        rng.shuffle(shuffled_values)
        shuffled = dict(labels)
        for pair, symbol in zip(pairs, shuffled_values):
            shuffled[pair] = symbol
        for row in metric_rows(shuffled, pairs):
            values[row["metric"]].append(row["value"])

    out = {}
    for row in observed_rows:
        vals = values[row["metric"]]
        mean = sum(vals) / len(vals)
        sd = (sum((value - mean) ** 2 for value in vals) / (len(vals) - 1)) ** 0.5
        if row["high_is_good"]:
            p = (sum(value >= row["value"] for value in vals) + 1) / (len(vals) + 1)
            z = (row["value"] - mean) / sd if sd else 0.0
        else:
            p = (sum(value <= row["value"] for value in vals) + 1) / (len(vals) + 1)
            z = (mean - row["value"]) / sd if sd else 0.0
        out[row["metric"]] = {
            "observed": row["value"],
            "mean": mean,
            "sd": sd,
            "min": min(vals),
            "max": max(vals),
            "p_good_direction": p,
            "z_good_direction": z,
        }
    return out


def classify(best: dict[str, Any], corrected_p: float) -> str:
    if corrected_p <= 0.05:
        return "weak_residual_marginal_signal"
    return "residual_marginal_not_promoted"


def write_report(result: dict[str, Any]) -> None:
    best = result["best"]
    lines = [
        "# Residual Marginal After E Search",
        "",
        "Generated by `residual_marginal_after_e_search.py`.",
        "",
        "This removes the fixed priority E/blocker layer and tests whether",
        "row/column/diagonal/digit marginal statistics still carry pair-label",
        "structure on the 40 remaining cells.",
        "",
        "## Summary",
        "",
        "| Residual cells | Best metric | Observed | z | raw p | corrected p | Verdict |",
        "|---:|---|---:|---:|---:|---:|---|",
        f"| {result['residual_pair_count']} | `{best['metric']}` | {best['value']:.3f} | {best['z_good_direction']:.2f} | {best['p_good_direction']:.5f} | {result['best_bonferroni_p']:.5f} | `{result['verdict']}` |",
        "",
        "## Top Metrics",
        "",
        "| Metric | Observed | Mean | z | raw p | Best line |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in result["top_rows"][:18]:
        line = row.get("best_line")
        line_text = "-"
        if line:
            line_text = f"{line['kind']}:{line['line_id']} `{line['labels']}`"
        lines.append(
            f"| `{row['metric']}` | {row['value']:.3f} | {row['control_mean']:.3f} | {row['z_good_direction']:.2f} | {row['p_good_direction']:.5f} | {line_text} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "A positive result would show that the non-E residual table still has a",
        "compact marginal/line signature after the strongest local layer is",
        "removed. Otherwise, the remaining placement is not explained by simple",
        "row/column/diagonal/digit constraints.",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    labels = labels_from_formula()
    pairs = residual_pairs()
    observed_rows = metric_rows(labels, pairs)
    ctl = controls(labels, pairs, observed_rows)
    rows = []
    for row in observed_rows:
        control = ctl[row["metric"]]
        rows.append(
            {
                **row,
                "control_mean": control["mean"],
                "control_sd": control["sd"],
                "p_good_direction": control["p_good_direction"],
                "z_good_direction": control["z_good_direction"],
            }
        )
    rows.sort(key=lambda row: (row["p_good_direction"], -row["z_good_direction"], row["metric"]))
    best = rows[0]
    corrected = min(1.0, best["p_good_direction"] * len(rows))
    result = {
        "schema": "residual_marginal_after_e_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "removed_fixed_claim_pairs": sorted(fixed_claim_pairs()),
        "residual_pair_count": len(pairs),
        "rows": rows,
        "top_rows": rows[:30],
        "best": best,
        "best_bonferroni_p": corrected,
        "controls": ctl,
        "verdict": classify(best, corrected),
        "translation_delta": "NONE",
        "new_plaintext": False,
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "best={metric} z={z:.2f} p={p:.5f} bonf={bonf:.5f} verdict={verdict}".format(
            metric=best["metric"],
            z=best["z_good_direction"],
            p=best["p_good_direction"],
            bonf=corrected,
            verdict=result["verdict"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
