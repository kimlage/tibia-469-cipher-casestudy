#!/usr/bin/env python3
"""Label-blind directed-provenance search for the 6<->9 split layer.

The prior 6<->9 reports ask whether symbol labels are nearly invariant under
swapping digit identities 6 and 9.  This pass deliberately avoids using the
symbol labels as features.  It asks whether directed-surface metadata that is
available before assigning semantic symbols (upper/lower presence, missing
directed code 39, the directed 19/91 conflict cell, edge/self-pair geometry,
and named lore-number anchors) can explain which of the nine 6<->9 local orbits
are mixed and which side carries the lower/canonical label.

Mechanical only.  No plaintext, glossary, or translation is promoted.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "digit_orbit_directed_provenance_results.json"
OUT_MD = HERE / "digit_orbit_directed_provenance_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 1000


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    if k == 0 or k == n:
        return 0.0
    return math.log2(math.comb(n, k))


def symbol_key(symbol: str) -> int:
    return SIGMA.index(symbol)


def pair_key(pair: tuple[int, int]) -> str:
    return f"{pair[0]}{pair[1]}"


def primary_pair_symbol(pair_table: dict[str, dict[str, Any]], pair: tuple[int, int]) -> str:
    cell = pair_table[pair_key(pair)]
    if cell["status"] == "pure":
        return cell["symbol_if_pure"]
    return min(cell["symbols"], key=symbol_key)


def orbit_pair_for_x(x: int, side_digit: int) -> tuple[int, int]:
    if x == 6 and side_digit == 9:
        return (9, 9)
    a, b = x, side_digit
    return (a, b) if a <= b else (b, a)


def present_directed_codes(formula: dict[str, Any]) -> set[str]:
    return set(formula["code_to_symbol"])


def directed_codes_for_pair(pair: tuple[int, int]) -> list[str]:
    a, b = pair
    if a == b:
        return [f"{a}{b}"]
    return [f"{a}{b}", f"{b}{a}"]


def pair_features(pair: tuple[int, int], code_set: set[str], formula: dict[str, Any]) -> dict[str, Any]:
    codes = directed_codes_for_pair(pair)
    present = [code for code in codes if code in code_set]
    a, b = pair
    upper = f"{a}{b}" if a <= b else f"{b}{a}"
    lower = f"{b}{a}" if a < b else upper
    cell = formula["pair_table"][pair_key(pair)]
    return {
        "pair": pair_key(pair),
        "a": a,
        "b": b,
        "is_diagonal": a == b,
        "is_edge_digit": a in {0, 8} or b in {0, 8},
        "touches_1": a == 1 or b == 1,
        "touches_3": a == 3 or b == 3,
        "touches_lore_469": bool({a, b} & {4, 6, 9}),
        "touches_lore_3478": bool({a, b} & {3, 4, 7, 8}),
        "directed_code_count": len(present),
        "missing_directed_count": len(codes) - len(present),
        "upper_present": upper in code_set,
        "lower_present": lower in code_set,
        "has_missing_upper": upper not in code_set,
        "has_missing_lower": lower not in code_set,
        "has_conflict_cell": cell["status"] == "conflict",
        "status_conflict": cell["status"] == "conflict",
        "status_pure": cell["status"] == "pure",
    }


def build_orbit_rows(formula: dict[str, Any]) -> list[dict[str, Any]]:
    code_set = present_directed_codes(formula)
    pair_table = formula["pair_table"]
    rows: list[dict[str, Any]] = []
    for x in range(9):
        pair6 = orbit_pair_for_x(x, 6)
        pair9 = orbit_pair_for_x(x, 9)
        label6 = primary_pair_symbol(pair_table, pair6)
        label9 = primary_pair_symbol(pair_table, pair9)
        ordered = sorted([label6, label9], key=symbol_key)
        f6 = pair_features(pair6, code_set, formula)
        f9 = pair_features(pair9, code_set, formula)
        feature_row = {
            "x": x,
            "x_edge_0_8": x in {0, 8},
            "x_low_0_1": x <= 1,
            "x_lore_exception_19_39": x in {1, 3},
            "x_lore_469_projected": x in {4, 6},
            "x_lore_3478_projected": x in {3, 4, 7, 8},
            "x_fibonacci": x in {0, 1, 2, 3, 5, 8},
            "x_triangular": x in {0, 1, 3, 6},
            "x_square": x in {0, 1, 4},
            "side6_is_diagonal": f6["is_diagonal"],
            "side9_is_diagonal": f9["is_diagonal"],
            "side6_missing_directed": f6["missing_directed_count"] > 0,
            "side9_missing_directed": f9["missing_directed_count"] > 0,
            "side6_has_missing_upper": f6["has_missing_upper"],
            "side9_has_missing_upper": f9["has_missing_upper"],
            "side6_has_conflict_cell": f6["has_conflict_cell"],
            "side9_has_conflict_cell": f9["has_conflict_cell"],
            "either_missing_directed": f6["missing_directed_count"] > 0 or f9["missing_directed_count"] > 0,
            "either_missing_upper": f6["has_missing_upper"] or f9["has_missing_upper"],
            "either_conflict_cell": f6["has_conflict_cell"] or f9["has_conflict_cell"],
            "either_directed_anomaly": f6["missing_directed_count"] > 0 or f9["missing_directed_count"] > 0 or f6["has_conflict_cell"] or f9["has_conflict_cell"],
            "either_edge_pair": f6["is_edge_digit"] or f9["is_edge_digit"],
            "either_lore_3478": f6["touches_lore_3478"] or f9["touches_lore_3478"],
            "either_lore_469": f6["touches_lore_469"] or f9["touches_lore_469"],
        }
        rows.append(
            {
                "x": x,
                "pair6": pair_key(pair6),
                "pair9": pair_key(pair9),
                "label6": label6,
                "label9": label9,
                "mixed": label6 != label9,
                "lower_label_on_side6": label6 == ordered[0],
                "side6_features": f6,
                "side9_features": f9,
                "features": feature_row,
            }
        )
    return rows


def atomic_rules(feature_names: list[str]) -> list[dict[str, Any]]:
    rules = []
    for name in feature_names:
        rules.append({"id": name, "xs": set(), "feature": name, "cost": 1.0, "kind": "atomic"})
        rules.append({"id": f"not_{name}", "xs": set(), "feature": name, "negate": True, "cost": 1.2, "kind": "atomic_not"})
    for k in range(9):
        rules.append({"id": f"x_le_{k}", "xs": set(range(k + 1)), "cost": 1.7, "kind": "threshold"})
        rules.append({"id": f"x_ge_{k}", "xs": set(range(k, 9)), "cost": 1.7, "kind": "threshold"})
    for modulus in range(2, 7):
        for residue in range(modulus):
            rules.append({"id": f"x_mod_{modulus}_eq_{residue}", "xs": {x for x in range(9) if x % modulus == residue}, "cost": 2.0 + math.log2(modulus) / 4, "kind": "modular"})
    return rules


def materialize_rules(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature_names = sorted(rows[0]["features"])
    out = []
    for rule in atomic_rules(feature_names):
        if "feature" in rule:
            xs = {row["x"] for row in rows if bool(row["features"][rule["feature"]]) ^ bool(rule.get("negate", False))}
            rule = {**rule, "xs": xs}
        out.append(rule)
    atomic = out[:]
    for left, right in itertools.combinations(atomic, 2):
        out.append(
            {
                "id": f"or({left['id']},{right['id']})",
                "xs": set(left["xs"]) | set(right["xs"]),
                "cost": left["cost"] + right["cost"] + 1.0,
                "kind": "compound_or",
            }
        )
        out.append(
            {
                "id": f"and({left['id']},{right['id']})",
                "xs": set(left["xs"]) & set(right["xs"]),
                "cost": left["cost"] + right["cost"] + 1.1,
                "kind": "compound_and",
            }
        )
    dedup: dict[tuple[int, ...], dict[str, Any]] = {}
    for rule in out:
        key = tuple(sorted(rule["xs"]))
        current = dedup.get(key)
        if current is None or rule["cost"] < current["cost"]:
            dedup[key] = rule
    return list(dedup.values())


def score_rule(rule: dict[str, Any], target_xs: set[int]) -> dict[str, Any]:
    pred = set(rule["xs"])
    tp = len(pred & target_xs)
    fp = len(pred - target_xs)
    fn = len(target_xs - pred)
    tn = 9 - tp - fp - fn
    acc = (tp + tn) / 9.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    exact = fp == 0 and fn == 0
    residual_bits = (fp + fn) * (math.log2(9) + 1.0)
    mdl_bits = rule["cost"] + residual_bits
    explicit_bits = log2_comb(9, len(target_xs))
    return {
        "id": rule["id"],
        "kind": rule["kind"],
        "predicted_xs": sorted(pred),
        "target_xs": sorted(target_xs),
        "cost": rule["cost"],
        "accuracy": acc,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "exact": exact,
        "mdl_bits": mdl_bits,
        "explicit_subset_bits": explicit_bits,
        "mdl_gain_vs_explicit_subset_bits": explicit_bits - mdl_bits,
    }


def best_rules(rules: list[dict[str, Any]], target_xs: set[int]) -> dict[str, Any]:
    scored = [score_rule(rule, target_xs) for rule in rules]
    by_accuracy = sorted(scored, key=lambda row: (-row["accuracy"], -row["f1"], row["mdl_bits"], row["id"]))
    by_mdl = sorted(scored, key=lambda row: (row["mdl_bits"], -row["accuracy"], row["id"]))
    return {"best_by_accuracy": by_accuracy[0], "best_by_mdl": by_mdl[0], "top_rows": by_accuracy[:30]}


def side_rule_candidates(mixed_xs: set[int], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for rule in rules:
        selected = set(rule["xs"]) & mixed_xs
        rows.append(
            {
                "id": f"side6_if_{rule['id']}",
                "side6_xs": selected,
                "cost": rule["cost"],
                "kind": rule["kind"],
            }
        )
    dedup: dict[tuple[int, ...], dict[str, Any]] = {}
    for row in rows:
        key = tuple(sorted(row["side6_xs"]))
        current = dedup.get(key)
        if current is None or row["cost"] < current["cost"]:
            dedup[key] = row
    return list(dedup.values())


def score_side_rule(rule: dict[str, Any], target_side6_xs: set[int], mixed_xs: set[int]) -> dict[str, Any]:
    pred = set(rule["side6_xs"])
    correct = sum((x in pred) == (x in target_side6_xs) for x in mixed_xs)
    errors = len(mixed_xs) - correct
    mdl_bits = rule["cost"] + errors * (math.log2(max(1, len(mixed_xs))) + 1.0)
    explicit_bits = len(mixed_xs)
    return {
        "id": rule["id"],
        "kind": rule["kind"],
        "predicted_side6_xs": sorted(pred),
        "target_side6_xs": sorted(target_side6_xs),
        "correct": correct,
        "total": len(mixed_xs),
        "accuracy": correct / len(mixed_xs) if mixed_xs else 1.0,
        "cost": rule["cost"],
        "mdl_bits": mdl_bits,
        "explicit_bits": explicit_bits,
        "mdl_gain_vs_explicit_bits": explicit_bits - mdl_bits,
    }


def best_side_rules(rows: list[dict[str, Any]], rules: list[dict[str, Any]]) -> dict[str, Any]:
    mixed_xs = {row["x"] for row in rows if row["mixed"]}
    target_side6_xs = {row["x"] for row in rows if row["mixed"] and row["lower_label_on_side6"]}
    candidates = side_rule_candidates(mixed_xs, rules)
    scored = [score_side_rule(rule, target_side6_xs, mixed_xs) for rule in candidates]
    by_accuracy = sorted(scored, key=lambda row: (-row["accuracy"], row["mdl_bits"], row["id"]))
    by_mdl = sorted(scored, key=lambda row: (row["mdl_bits"], -row["accuracy"], row["id"]))
    return {"best_by_accuracy": by_accuracy[0], "best_by_mdl": by_mdl[0], "top_rows": by_accuracy[:30]}


def exhaustive_subset_control(rules: list[dict[str, Any]], observed: dict[str, Any], target_size: int) -> dict[str, Any]:
    acc_values = []
    mdl_values = []
    exact_costs = []
    for xs_tuple in itertools.combinations(range(9), target_size):
        target = set(xs_tuple)
        best = best_rules(rules, target)
        acc_values.append(best["best_by_accuracy"]["accuracy"])
        mdl_values.append(best["best_by_mdl"]["mdl_bits"])
        exact_rows = [score_rule(rule, target) for rule in rules if set(rule["xs"]) == target]
        exact_costs.append(min((row["cost"] for row in exact_rows), default=float("inf")))
    observed_acc = observed["best_by_accuracy"]["accuracy"]
    observed_mdl = observed["best_by_mdl"]["mdl_bits"]
    observed_exact_cost = observed["best_by_accuracy"]["cost"] if observed["best_by_accuracy"]["exact"] else float("inf")
    finite_costs = [value for value in exact_costs if math.isfinite(value)]
    return {
        "target_size": target_size,
        "subsets": len(acc_values),
        "best_accuracy": summarize(acc_values, observed_acc, True),
        "best_mdl_bits": summarize(mdl_values, observed_mdl, False),
        "exact_rule_cost": summarize(finite_costs, observed_exact_cost, False) if math.isfinite(observed_exact_cost) else None,
        "exact_rule_fraction": len(finite_costs) / len(acc_values),
    }


def shuffle_control(rows: list[dict[str, Any]], rules: list[dict[str, Any]], observed: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    target = [row["mixed"] for row in rows]
    acc_values = []
    mdl_values = []
    for _ in range(CONTROL_TRIALS):
        rng.shuffle(target)
        xs = {row["x"] for row, value in zip(rows, target) if value}
        best = best_rules(rules, xs)
        acc_values.append(best["best_by_accuracy"]["accuracy"])
        mdl_values.append(best["best_by_mdl"]["mdl_bits"])
    return {
        "trials": CONTROL_TRIALS,
        "best_accuracy": summarize(acc_values, observed["best_by_accuracy"]["accuracy"], True),
        "best_mdl_bits": summarize(mdl_values, observed["best_by_mdl"]["mdl_bits"], False),
    }


def summarize(values: list[float], observed: float, higher_is_better: bool) -> dict[str, Any]:
    finite = [value for value in values if math.isfinite(value)]
    mean = sum(finite) / len(finite)
    sd = (sum((value - mean) ** 2 for value in finite) / (len(finite) - 1)) ** 0.5 if len(finite) > 1 else 0.0
    if higher_is_better:
        p = (sum(value >= observed for value in finite) + 1) / (len(finite) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in finite) + 1) / (len(finite) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(finite),
        "max": max(finite),
        "p_good_direction": p,
        "z_good_direction": z,
    }


def verdict(result: dict[str, Any]) -> str:
    mixed = result["mixedness"]
    exact_p = result["controls"]["exhaustive_same_size_subsets"]["exact_rule_cost"]["p_good_direction"]
    mdl_p = result["controls"]["exhaustive_same_size_subsets"]["best_mdl_bits"]["p_good_direction"]
    best = mixed["best_by_accuracy"]
    if best["exact"] and best["mdl_gain_vs_explicit_subset_bits"] > 0 and exact_p <= 0.05 and mdl_p <= 0.05:
        return "candidate_directed_provenance_split_rule"
    if best["exact"] and best["mdl_gain_vs_explicit_subset_bits"] > 0 and max(exact_p, mdl_p) <= 0.20:
        return "weak_directed_provenance_signal"
    if best["exact"]:
        return "descriptive_directed_provenance_microfit"
    return "rejected_control"


def write_report(result: dict[str, Any]) -> None:
    rows = result["orbit_rows"]
    mixed = result["mixedness"]
    side = result["side_orientation"]
    controls = result["controls"]
    lines = [
        "# Digit-Orbit Directed Provenance Search",
        "",
        "Generated by `digit_orbit_directed_provenance_search.py`.",
        "",
        "Scope: the nine non-singleton `6 <-> 9` quotient orbits. Feature rules",
        "are label-blind: they use directed code presence, missing/reverse",
        "metadata, conflict-cell flags, edge/diagonal geometry, and named lore",
        "digit anchors, but not the symbol labels as predictors.",
        "",
        "Methodological quarantine: `conflict-cell` flags are derived from the",
        "frozen mechanical table and are therefore treated as structural anomaly",
        "metadata, not as independent evidence. They can organize the ledger, but",
        "cannot promote an origin formula by themselves.",
        "",
        "## Target Rows",
        "",
        "| x | pair6 | pair9 | mixed | lower label on side6 | label-blind anomaly features |",
        "|---:|---|---|---:|---:|---|",
    ]
    for row in rows:
        features = row["features"]
        active = [
            name
            for name in [
                "either_directed_anomaly",
                "either_missing_upper",
                "either_conflict_cell",
                "x_edge_0_8",
                "x_lore_exception_19_39",
                "x_triangular",
                "x_fibonacci",
            ]
            if features[name]
        ]
        lines.append(
            f"| {row['x']} | `{row['pair6']}` | `{row['pair9']}` | {str(row['mixed']).lower()} | {str(row['lower_label_on_side6']).lower()} | `{', '.join(active) if active else '-'}` |"
        )
    best = mixed["best_by_accuracy"]
    best_mdl = mixed["best_by_mdl"]
    side_best = side["best_by_accuracy"]
    lines.extend(
        [
            "",
            "## Best Rules",
            "",
            "| Target | Best rule | Accuracy | MDL bits | Gain vs explicit subset | Control p | Verdict use |",
            "|---|---|---:|---:|---:|---:|---|",
            f"| mixedness | `{best['id']}` | {best['accuracy']:.3f} | {best['mdl_bits']:.2f} | {best['mdl_gain_vs_explicit_subset_bits']:.2f} | {controls['exhaustive_same_size_subsets']['exact_rule_cost']['p_good_direction']:.4f} | descriptive only unless controls hold |",
            f"| mixedness by MDL | `{best_mdl['id']}` | {best_mdl['accuracy']:.3f} | {best_mdl['mdl_bits']:.2f} | {best_mdl['mdl_gain_vs_explicit_subset_bits']:.2f} | {controls['exhaustive_same_size_subsets']['best_mdl_bits']['p_good_direction']:.4f} | compression check |",
            f"| side orientation | `{side_best['id']}` | {side_best['accuracy']:.3f} | {side_best['mdl_bits']:.2f} | {side_best['mdl_gain_vs_explicit_bits']:.2f} | n/a | tiny four-case diagnostic |",
            "",
            "## Controls",
            "",
            "| Control | Metric | Observed | Mean | Max/Min | p(good) |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    ex = controls["exhaustive_same_size_subsets"]
    shuf = controls["label_shuffle_preserving_mixed_count"]
    lines.append(
        f"| exhaustive 4-of-9 subsets | best accuracy | {ex['best_accuracy']['observed']:.3f} | {ex['best_accuracy']['mean']:.3f} | {ex['best_accuracy']['max']:.3f} | {ex['best_accuracy']['p_good_direction']:.4f} |"
    )
    lines.append(
        f"| exhaustive 4-of-9 subsets | best MDL bits | {ex['best_mdl_bits']['observed']:.2f} | {ex['best_mdl_bits']['mean']:.2f} | {ex['best_mdl_bits']['min']:.2f} | {ex['best_mdl_bits']['p_good_direction']:.4f} |"
    )
    lines.append(
        f"| exhaustive 4-of-9 subsets | exact rule cost | {ex['exact_rule_cost']['observed']:.2f} | {ex['exact_rule_cost']['mean']:.2f} | {ex['exact_rule_cost']['min']:.2f} | {ex['exact_rule_cost']['p_good_direction']:.4f} |"
    )
    lines.append(
        f"| mixed-label shuffle | best accuracy | {shuf['best_accuracy']['observed']:.3f} | {shuf['best_accuracy']['mean']:.3f} | {shuf['best_accuracy']['max']:.3f} | {shuf['best_accuracy']['p_good_direction']:.4f} |"
    )
    lines.append(
        f"| mixed-label shuffle | best MDL bits | {shuf['best_mdl_bits']['observed']:.2f} | {shuf['best_mdl_bits']['mean']:.2f} | {shuf['best_mdl_bits']['min']:.2f} | {shuf['best_mdl_bits']['p_good_direction']:.4f} |"
    )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"`{result['verdict']}`.",
            "",
            "Conservative reading: directed-surface provenance cleanly names the",
            "`19/91` conflict and missing-`39` orphan, but it still needs edge",
            "digits to cover `06/09` and `68/89`. That is useful anomaly",
            "bookkeeping, not an independent generator for the pair-table labels.",
            "",
            "Translation delta: `NONE`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    rows = build_orbit_rows(formula)
    rules = materialize_rules(rows)
    mixed_target = {row["x"] for row in rows if row["mixed"]}
    mixed = best_rules(rules, mixed_target)
    side = best_side_rules(rows, rules)
    result = {
        "schema": "digit_orbit_directed_provenance_results.v1",
        "translation_delta": "NONE",
        "target": "6_9_quotient_mixed_orbits_label_blind_directed_provenance",
        "rule_count": len(rules),
        "orbit_rows": rows,
        "mixedness": mixed,
        "side_orientation": side,
    }
    result["controls"] = {
        "exhaustive_same_size_subsets": exhaustive_subset_control(rules, mixed, len(mixed_target)),
        "label_shuffle_preserving_mixed_count": shuffle_control(rows, rules, mixed),
    }
    result["verdict"] = verdict(result)
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "verdict={verdict} best={rule} accuracy={acc:.3f} mdl_gain={gain:.2f}".format(
            verdict=result["verdict"],
            rule=mixed["best_by_accuracy"]["id"],
            acc=mixed["best_by_accuracy"]["accuracy"],
            gain=mixed["best_by_accuracy"]["mdl_gain_vs_explicit_subset_bits"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
