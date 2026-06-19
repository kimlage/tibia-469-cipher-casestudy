#!/usr/bin/env python3
"""Lore-number anomaly operator search.

Broad lore-number searches as seeds, hashes, and zero masks are already
negative. This narrow pass asks a smaller question: do lore digit strings select
the known structural anomaly cells better than digit-multiset permutations,
same-length random strings, or random anomaly subsets?

Mechanical only. No plaintext, glossary, or semantic translation is promoted.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

OUT_JSON = HERE / "lore_anomaly_operator_results.json"
OUT_MD = HERE / "lore_anomaly_operator_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 5000
LORE_STRINGS = {
    "one": "1",
    "tibia_469": "469",
    "paradox_3478": "3478",
    "honeminas_43153": "43153",
    "magic_web_34784": "34784",
    "number_74032": "74032",
    "number_45331": "45331",
}


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pair_cells() -> list[str]:
    return [f"{a}{b}" for a in range(10) for b in range(a, 10)]


CELLS = pair_cells()
CELL_SET = set(CELLS)


TARGETS = {
    "ordered_exception_cells": {"19", "39", "33", "66"},
    "mixed_6_9_orbit_cells": {"06", "09", "16", "19", "36", "39", "68", "89"},
    "mixed_6_9_exception_cells": {"09", "16", "36", "89"},
    "all_structural_anomaly_cells": {"06", "09", "16", "19", "33", "36", "39", "66", "68", "89"},
    "sevenseg_mixed_cells": {"06", "09", "68", "89"},
}


def norm_pair(a: int, b: int) -> str:
    left, right = sorted([a, b])
    return f"{left}{right}"


def add_rule(rules: list[dict[str, Any]], lore_id: str, value: str, family: str, name: str, cells: set[str], cost: float) -> None:
    cells = set(cells) & CELL_SET
    if not cells or len(cells) == len(CELLS):
        return
    rules.append(
        {
            "rule_id": f"{lore_id}:{family}:{name}",
            "lore_id": lore_id,
            "value": value,
            "family": family,
            "name": name,
            "cells": sorted(cells),
            "selected_count": len(cells),
            "cost": cost,
        }
    )


def build_rules(lore_strings: dict[str, str]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for lore_id, value in lore_strings.items():
        digits = [int(ch) for ch in value]
        digit_set = set(digits)
        unique_digits = sorted(digit_set)
        first = digits[0]
        last = digits[-1]
        base_cost = math.log2(len(lore_strings)) + math.log2(max(2, len(value))) + 1.0

        add_rule(
            rules,
            lore_id,
            value,
            "digit_set",
            "both_digits_in_string",
            {norm_pair(a, b) for a in digit_set for b in digit_set},
            base_cost + 1.2,
        )
        add_rule(
            rules,
            lore_id,
            value,
            "digit_set",
            "any_digit_in_string",
            {cell for cell in CELLS if int(cell[0]) in digit_set or int(cell[1]) in digit_set},
            base_cost + 1.2,
        )
        add_rule(
            rules,
            lore_id,
            value,
            "endpoint_anchor",
            "contains_first_or_last",
            {cell for cell in CELLS if int(cell[0]) in {first, last} or int(cell[1]) in {first, last}},
            base_cost + 1.5,
        )
        for anchor in [first, last, min(digit_set), max(digit_set)]:
            add_rule(
                rules,
                lore_id,
                value,
                "endpoint_anchor",
                f"contains_{anchor}",
                {cell for cell in CELLS if int(cell[0]) == anchor or int(cell[1]) == anchor},
                base_cost + 1.9,
            )

        adjacent_pairs = {norm_pair(a, b) for a, b in zip(digits, digits[1:])}
        cyclic_pairs = set(adjacent_pairs)
        if len(digits) > 1:
            cyclic_pairs.add(norm_pair(digits[-1], digits[0]))
        all_position_pairs = {
            norm_pair(digits[i], digits[j])
            for i in range(len(digits))
            for j in range(i + 1, len(digits))
        }
        add_rule(rules, lore_id, value, "position_pairs", "adjacent_unordered_pairs", adjacent_pairs, base_cost + 2.0)
        add_rule(rules, lore_id, value, "position_pairs", "cyclic_adjacent_pairs", cyclic_pairs, base_cost + 2.2)
        add_rule(rules, lore_id, value, "position_pairs", "all_position_pairs", all_position_pairs, base_cost + 2.5)

        for modulus_source, residues in [
            ("digit_residues", digit_set),
            ("adjacent_sum_residues", {(a + b) % 10 for a, b in zip(digits, digits[1:])}),
            ("adjacent_diff_residues", {(b - a) % 10 for a, b in zip(digits, digits[1:])}),
        ]:
            add_rule(
                rules,
                lore_id,
                value,
                modulus_source,
                "sum_mod10_in_residues",
                {cell for cell in CELLS if (int(cell[0]) + int(cell[1])) % 10 in residues},
                base_cost + 2.4,
            )
            add_rule(
                rules,
                lore_id,
                value,
                modulus_source,
                "absdiff_in_residues",
                {cell for cell in CELLS if abs(int(cell[1]) - int(cell[0])) in residues},
                base_cost + 2.4,
            )
            add_rule(
                rules,
                lore_id,
                value,
                modulus_source,
                "product_mod10_in_residues",
                {cell for cell in CELLS if (int(cell[0]) * int(cell[1])) % 10 in residues},
                base_cost + 2.6,
            )

        vector_steps = {(b - a) % 10 for a, b in zip(digits, digits[1:])}
        undirected_steps = {min(step, (-step) % 10) for step in vector_steps}
        add_rule(
            rules,
            lore_id,
            value,
            "vector_steps",
            "undirected_step_in_adjacent_deltas",
            {cell for cell in CELLS if abs(int(cell[1]) - int(cell[0])) in undirected_steps},
            base_cost + 2.0,
        )
        add_rule(
            rules,
            lore_id,
            value,
            "quotient_6_9",
            "one_6_9_anchor_in_digits",
            {
                cell
                for cell in CELLS
                if ((cell[0] in "69") ^ (cell[1] in "69"))
                and (int(cell[0]) in digit_set or int(cell[1]) in digit_set)
            },
            base_cost + 2.0,
        )
        add_rule(
            rules,
            lore_id,
            value,
            "quotient_6_9",
            "one_6_9_anchor_adjacent_to_seed_digit",
            {
                cell
                for cell in CELLS
                if ((cell[0] in "69") ^ (cell[1] in "69"))
                and any(abs((int(cell[0]) if cell[1] in "69" else int(cell[1])) - d) <= 1 for d in digit_set)
            },
            base_cost + 2.6,
        )
        if unique_digits:
            index = int(value) % len(CELLS)
            add_rule(rules, lore_id, value, "index_anchor", "number_mod_55_cell", {CELLS[index]}, base_cost + 3.0)
            for offset in [sum(digits) % len(CELLS), math.prod([d + 1 for d in digits]) % len(CELLS)]:
                add_rule(rules, lore_id, value, "index_anchor", f"derived_index_{offset}", {CELLS[offset]}, base_cost + 3.2)

    dedup: dict[tuple[str, ...], dict[str, Any]] = {}
    for rule in rules:
        key = tuple(rule["cells"])
        old = dedup.get(key)
        if old is None or rule["cost"] < old["cost"] or (rule["cost"] == old["cost"] and rule["rule_id"] < old["rule_id"]):
            dedup[key] = rule
    return sorted(dedup.values(), key=lambda row: (row["cost"], row["rule_id"]))


def score_rule(rule: dict[str, Any], target: set[str], target_id: str) -> dict[str, Any]:
    selected = set(rule["cells"])
    tp = len(selected & target)
    fp = len(selected - target)
    fn = len(target - selected)
    precision = tp / len(selected) if selected else 0.0
    recall = tp / len(target) if target else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        **rule,
        "target_id": target_id,
        "target_size": len(target),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact": fp == 0 and fn == 0,
    }


def best_scores(rules: list[dict[str, Any]], targets: dict[str, set[str]]) -> dict[str, dict[str, Any]]:
    out = {}
    for target_id, target in targets.items():
        rows = [score_rule(rule, target, target_id) for rule in rules]
        rows.sort(key=lambda row: (-int(row["exact"]), -row["f1"], -row["tp"], row["fp"] + row["fn"], row["cost"], row["rule_id"]))
        out[target_id] = rows[0]
    return out


def summarize_high(values: list[float], observed: float) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "p_good_direction": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
    }


def permuted_lore_strings(rng: random.Random) -> dict[str, str]:
    out = {}
    for key, value in LORE_STRINGS.items():
        chars = list(value)
        rng.shuffle(chars)
        out[key] = "".join(chars)
    return out


def random_lore_strings(rng: random.Random) -> dict[str, str]:
    return {
        key: "".join(str(rng.randrange(10)) for _ in value)
        for key, value in LORE_STRINGS.items()
    }


def controls(observed_rules: list[dict[str, Any]], observed_best: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    out: dict[str, Any] = {"trials": CONTROL_TRIALS}
    cells = CELLS[:]
    perm_values: dict[str, list[float]] = {target_id: [] for target_id in TARGETS}
    random_values: dict[str, list[float]] = {target_id: [] for target_id in TARGETS}
    random_target_values: dict[str, list[float]] = {target_id: [] for target_id in TARGETS}
    for _ in range(CONTROL_TRIALS):
        perm_rules = build_rules(permuted_lore_strings(rng))
        random_rules = build_rules(random_lore_strings(rng))
        for target_id, target in TARGETS.items():
            perm_values[target_id].append(best_scores(perm_rules, {target_id: target})[target_id]["f1"])
            random_values[target_id].append(best_scores(random_rules, {target_id: target})[target_id]["f1"])
            random_target = set(rng.sample(cells, len(target)))
            random_target_values[target_id].append(best_scores(observed_rules, {target_id: random_target})[target_id]["f1"])

    for target_id, best in observed_best.items():
        out[target_id] = {
            "digit_multiset_permutation": summarize_high(perm_values[target_id], best["f1"]),
            "same_length_random_digits": summarize_high(random_values[target_id], best["f1"]),
            "same_size_random_target": summarize_high(random_target_values[target_id], best["f1"]),
        }
    return out


def classify(best_by_target: dict[str, dict[str, Any]], ctrl: dict[str, Any]) -> str:
    for target_id, best in best_by_target.items():
        p = max(
            ctrl[target_id]["digit_multiset_permutation"]["p_good_direction"],
            ctrl[target_id]["same_length_random_digits"]["p_good_direction"],
            ctrl[target_id]["same_size_random_target"]["p_good_direction"],
        )
        if best["exact"] and best["cost"] <= 8.0 and p <= 0.01:
            return "candidate_lore_anomaly_operator"
    if any(best["f1"] >= 0.75 for best in best_by_target.values()):
        return "weak_lore_anomaly_overlap_not_formula"
    return "rejected_control"


def write_report(result: dict[str, Any]) -> None:
    lines = [
        "# Lore Anomaly Operator Search",
        "",
        "Generated by `lore_anomaly_operator_search.py`.",
        "",
        "This pass tests lore digit strings only as selectors for known structural",
        "anomaly cells. It does not train or score a translation.",
        "",
        "## Summary",
        "",
        "| Target | Best rule | F1 | TP/target | Selected | Cost | p perm | p random | p target |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for target_id, best in result["best_by_target"].items():
        ctrl = result["controls"][target_id]
        lines.append(
            f"| `{target_id}` | `{best['rule_id']}` | {best['f1']:.3f} | {best['tp']}/{best['target_size']} | {best['selected_count']} | {best['cost']:.1f} | {ctrl['digit_multiset_permutation']['p_good_direction']:.4f} | {ctrl['same_length_random_digits']['p_good_direction']:.4f} | {ctrl['same_size_random_target']['p_good_direction']:.4f} |"
        )
    lines.extend(
        [
            "",
            f"Verdict: `{result['verdict']}`.",
            "",
            "## Target Cells",
            "",
        ]
    )
    for target_id, cells in result["targets"].items():
        lines.append(f"- `{target_id}`: `{', '.join(cells)}`")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Lore strings can be made to overlap some small anomaly sets, but the same",
            "overlaps are available to digit-multiset permutations, random digit strings,",
            "or random target subsets often enough that no lore operator is promoted.",
            "",
            f"Translation delta: `{result['translation_delta']}`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rules = build_rules(LORE_STRINGS)
    best_by_target = best_scores(rules, TARGETS)
    ctrl = controls(rules, best_by_target)
    result = {
        "schema": "lore_anomaly_operator_results.v1",
        "lore_strings": LORE_STRINGS,
        "targets": {key: sorted(value) for key, value in TARGETS.items()},
        "rule_count": len(rules),
        "best_by_target": best_by_target,
        "controls": ctrl,
        "verdict": classify(best_by_target, ctrl),
        "translation_delta": "NONE",
        "new_plaintext": False,
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"rules={len(rules)} verdict={result['verdict']}")
    for target_id, best in best_by_target.items():
        print(f"{target_id}: {best['rule_id']} f1={best['f1']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
