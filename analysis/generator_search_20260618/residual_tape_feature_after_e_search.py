#!/usr/bin/env python3
"""Residual tape-feature search after fixed E-priority layer.

The whole-table tape-feature probe mostly rediscovered a broad E-ish grid
split. This pass removes the fixed priority E/blocker layer first and asks:
do tape/literal usage features explain the remaining 40 pair labels?

Controls shuffle only the residual labels. No plaintext is inferred.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any

import tape_feature_pair_label_search as tape_search
import usage_driven_pair_placement_search as usage_search


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TAPE_FORMULA_JSON = HERE / "tape_based_formula_469.json"
OUT_JSON = HERE / "residual_tape_feature_after_e_results.json"
OUT_MD = HERE / "residual_tape_feature_after_e_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 1000
SYMBOLS = "*ABCEFILNORSTV"
SYMBOL_BITS = math.log2(len(SYMBOLS))
CELL_BITS = math.log2(55)
LABEL_EXCEPTION_BITS = SYMBOL_BITS + CELL_BITS


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fixed_claims() -> set[str]:
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


def log2_multinomial(labels: list[str]) -> float:
    counts = Counter(labels)
    bits = math.lgamma(len(labels) + 1) / math.log(2)
    for count in counts.values():
        bits -= math.lgamma(count + 1) / math.log(2)
    return bits


def usage_features_by_pair() -> dict[str, dict[str, int]]:
    events = usage_search.events_by_book()
    all_books = set(events)
    stats = usage_search.usage_stats(all_books, events)
    out = {}
    for pair, row in stats.items():
        out[pair] = {
            "usage_count": int(row["count"]),
            "usage_first_global_bin": int(row["first_global_index"] // 50),
            "usage_last_global_bin": int(row["last_global_index"] // 50),
            "usage_mean_global_bin": int(row["mean_global_index"] // 50),
            "usage_orientation_bias_pct": int(round(100 * row["orientation_bias"])),
            "usage_first_book": int(row["first_book"]),
            "usage_first_pos_bin": int(row["first_pos"] // 10),
        }
    return out


def tree_cost_bits(row: dict[str, Any]) -> float:
    predicate_bits = 8.0 * max(0, row.get("leaf_count", 1) - 1)
    leaf_bits = row.get("leaf_count", 1) * SYMBOL_BITS
    exception_bits = row["errors"] * LABEL_EXCEPTION_BITS
    return predicate_bits + leaf_bits + exception_bits


def run_residual_search(feature_set_id: str, feature_names: list[str], pairs: list[str], labels: dict[str, str], features: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    predicates = tape_search.build_predicates(features, feature_names)
    rows = tape_search.run_search(feature_set_id, feature_names, pairs, labels, features)
    for depth in [2, 3]:
        tree = tape_search.fit_tree(pairs, labels, features, predicates, depth=depth)
        row = tape_search.score_tree(tree, pairs, labels, features)
        row.update(
            {
                "feature_set": feature_set_id,
                "rule_class": f"tree_depth_{depth}",
                "rules": tape_search.tree_rules(tree),
                "leaf_count": tape_search.leaf_count(tree),
            }
        )
        rows.append(row)
    lookup_bits = log2_multinomial([labels[pair] for pair in pairs])
    for row in rows:
        row["rough_mdl_bits"] = tree_cost_bits(row)
        row["lookup_bits"] = lookup_bits
        row["mdl_gain_vs_residual_lookup_bits"] = lookup_bits - row["rough_mdl_bits"]
        row["mdl_ratio_vs_residual_lookup"] = row["rough_mdl_bits"] / lookup_bits
    rows.sort(
        key=lambda row: (
            -row["mdl_gain_vs_residual_lookup_bits"],
            -row["accuracy"],
            row["leaf_count"],
            row["rule_class"],
        )
    )
    return rows[:12]


def controls(feature_sets: dict[str, list[str]], pairs: list[str], labels: dict[str, str], features: dict[str, dict[str, Any]], observed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    symbols = [labels[pair] for pair in pairs]
    observed_best = {}
    for row in observed_rows:
        key = row["feature_set"]
        old = observed_best.get(key)
        if old is None or row["mdl_gain_vs_residual_lookup_bits"] > old["mdl_gain_vs_residual_lookup_bits"]:
            observed_best[key] = row

    values = {feature_set: {"accuracy": [], "mdl_gain": []} for feature_set in feature_sets}
    for _trial in range(CONTROL_TRIALS):
        shuffled = symbols[:]
        rng.shuffle(shuffled)
        shuffled_labels = dict(zip(pairs, shuffled))
        for feature_set, names in feature_sets.items():
            rows = run_residual_search(feature_set, names, pairs, shuffled_labels, features)
            best = rows[0]
            values[feature_set]["accuracy"].append(best["accuracy"])
            values[feature_set]["mdl_gain"].append(best["mdl_gain_vs_residual_lookup_bits"])

    def summarize(vals: list[float], observed: float) -> dict[str, float]:
        mean = sum(vals) / len(vals)
        sd = (sum((value - mean) ** 2 for value in vals) / (len(vals) - 1)) ** 0.5
        return {
            "observed": observed,
            "mean": mean,
            "sd": sd,
            "min": min(vals),
            "max": max(vals),
            "p_good_direction": (sum(value >= observed for value in vals) + 1) / (len(vals) + 1),
            "z_good_direction": (observed - mean) / sd if sd else 0.0,
        }

    out = {}
    for feature_set, best in observed_best.items():
        out[feature_set] = {
            "accuracy": summarize(values[feature_set]["accuracy"], best["accuracy"]),
            "mdl_gain": summarize(values[feature_set]["mdl_gain"], best["mdl_gain_vs_residual_lookup_bits"]),
        }
    return out


def classify(best: dict[str, Any], ctl: dict[str, Any]) -> str:
    if best["mdl_gain_vs_residual_lookup_bits"] > 0 and ctl["mdl_gain"]["p_good_direction"] <= 0.05:
        return "candidate_residual_tape_feature_formula"
    if best["accuracy"] >= 0.40 and ctl["accuracy"]["p_good_direction"] <= 0.05:
        return "weak_residual_tape_feature_signal"
    return "residual_tape_feature_not_promoted"


def write_report(result: dict[str, Any]) -> None:
    best = result["best"]
    ctl = result["controls"][best["feature_set"]]
    lines = [
        "# Residual Tape Feature After E Search",
        "",
        "Generated by `residual_tape_feature_after_e_search.py`.",
        "",
        "This removes the fixed priority E/blocker layer and tests tape/literal",
        "and usage/order features only on the 40 remaining pair cells.",
        "",
        "## Summary",
        "",
        "| Cells | Feature set | Rule | Accuracy | MDL/residual lookup | Gain | p(acc) | p(MDL) | Verdict |",
        "|---:|---|---|---:|---:|---:|---:|---:|---|",
        f"| {best['total']} | `{best['feature_set']}` | `{best['rule_class']}` | {best['accuracy']:.3f} | {best['mdl_ratio_vs_residual_lookup']:.3f} | {best['mdl_gain_vs_residual_lookup_bits']:.1f} | {ctl['accuracy']['p_good_direction']:.5f} | {ctl['mdl_gain']['p_good_direction']:.5f} | `{result['verdict']}` |",
        "",
        "## Best Rules",
        "",
    ]
    for rule in best["rules"][:20]:
        lines.append(f"- `{rule}`")
    lines += [
        "",
        "## Top Rows",
        "",
        "| Feature set | Rule | Accuracy | Leaves | MDL/lookup | Gain |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in result["top_rows"][:16]:
        lines.append(
            f"| `{row['feature_set']}` | `{row['rule_class']}` | {row['accuracy']:.3f} | {row['leaf_count']} | {row['mdl_ratio_vs_residual_lookup']:.3f} | {row['mdl_gain_vs_residual_lookup_bits']:.1f} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "A positive result would mean the tape/usage assembly layer helps explain",
        "the non-E pair-label placement after the strongest local matrix layer is",
        "removed. Otherwise, tape and usage remain assembly diagnostics rather",
        "than pair-table generators.",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(TAPE_FORMULA_JSON)
    projected = tape_search.project(formula)
    tape_features = tape_search.tape_features_by_pair(formula, projected)
    usage_features = usage_features_by_pair()
    features = {
        pair: {
            **tape_features[pair],
            **usage_features[pair],
            **tape_search.grid_features(pair),
        }
        for pair in tape_search.all_pairs()
    }
    labels = {pair: tape_search.primary_pair_symbol(formula["pair_table"], pair) for pair in tape_search.all_pairs()}
    pairs = [pair for pair in tape_search.all_pairs() if pair not in fixed_claims()]
    tape_feature_names = sorted(next(iter(tape_features.values())).keys())
    usage_feature_names = sorted(next(iter(usage_features.values())).keys())
    grid_feature_names = sorted(tape_search.grid_features("00").keys())
    feature_sets = {
        "tape_only": tape_feature_names,
        "usage_only": usage_feature_names,
        "tape_plus_usage": tape_feature_names + usage_feature_names,
        "tape_usage_grid": tape_feature_names + usage_feature_names + grid_feature_names,
    }
    rows = []
    for feature_set, names in feature_sets.items():
        rows.extend(run_residual_search(feature_set, names, pairs, labels, features))
    rows.sort(
        key=lambda row: (
            -row["mdl_gain_vs_residual_lookup_bits"],
            -row["accuracy"],
            row["leaf_count"],
            row["feature_set"],
        )
    )
    ctl = controls(feature_sets, pairs, labels, features, rows)
    best = rows[0]
    verdict = classify(best, ctl[best["feature_set"]])
    result = {
        "schema": "residual_tape_feature_after_e_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "removed_fixed_claim_pairs": sorted(fixed_claims()),
        "residual_pair_count": len(pairs),
        "rows": rows,
        "top_rows": rows[:20],
        "best": best,
        "controls": ctl,
        "feature_sets": feature_sets,
        "verdict": verdict,
        "translation_delta": "NONE",
        "new_plaintext": False,
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "best={feature_set}/{rule_class} acc={acc:.3f} gain={gain:.1f} p={p:.5f} verdict={verdict}".format(
            feature_set=best["feature_set"],
            rule_class=best["rule_class"],
            acc=best["accuracy"],
            gain=best["mdl_gain_vs_residual_lookup_bits"],
            p=ctl[best["feature_set"]]["mdl_gain"]["p_good_direction"],
            verdict=verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
