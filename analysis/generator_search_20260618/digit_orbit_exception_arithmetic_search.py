#!/usr/bin/env python3
"""Micro-search for arithmetic/lore rules over non-singleton 6<->9 orbits.

This pass follows `digit_orbit_quotient_search.py` but narrows the question:
given the nine non-singleton unordered-pair orbits induced by swapping digits
6 and 9, can a simple rule over the other digit x explain which orbits are
mixed, and can a simple side rule explain whether the 6-side or 9-side carries
the lower/canonical orbit label?

Mechanical only. No plaintext, glossary, or translation claim is produced.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "digit_orbit_exception_arithmetic_results.json"
OUT_MD = HERE / "digit_orbit_exception_arithmetic_report.md"

RANDOM_SEED = 46920260619
LABEL_SHUFFLE_TRIALS = 20000

SIGMA = list("*ABCEFILNORSTV")
SYMBOL_RANK = {symbol: index for index, symbol in enumerate(SIGMA)}
X_DOMAIN = tuple(range(9))


@dataclass(frozen=True)
class Rule:
    id: str
    family: str
    description: str
    predicted_x: frozenset[int]
    complexity: float
    status: str


@dataclass(frozen=True)
class SideRule:
    id: str
    family: str
    description: str
    complexity: float
    status: str
    side_for_x: tuple[str, ...]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pair_key(a: int, b: int) -> str:
    left, right = sorted((a, b))
    return f"{left}{right}"


def natural_pairs() -> list[str]:
    return [f"{a}{b}" for a in range(10) for b in range(a, 10)]


def symbol_sort_key(symbol: str) -> tuple[int, str]:
    return (SYMBOL_RANK.get(symbol, 999), symbol)


def primary_symbol(cell: dict[str, Any]) -> str:
    if cell["status"] == "pure":
        return str(cell["symbol_if_pure"])
    return sorted((str(symbol) for symbol in cell["symbols"]), key=symbol_sort_key)[0]


def cell_symbols(cell: dict[str, Any]) -> list[str]:
    return sorted((str(symbol) for symbol in cell["symbols"]), key=symbol_sort_key)


def pair_table_labels(formula: dict[str, Any]) -> dict[str, str]:
    return {pair: primary_symbol(formula["pair_table"][pair]) for pair in natural_pairs()}


def triangular_pair_index(pair: str) -> int:
    x, y = int(pair[0]), int(pair[1])
    return y * (y + 1) // 2 + x


def build_orbits(formula: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    pair_table = formula["pair_table"]
    for x in X_DOMAIN:
        if x == 6:
            side6_pair = "66"
            side9_pair = "99"
            orbit_kind = "diagonal_66_99"
        else:
            side6_pair = pair_key(x, 6)
            side9_pair = pair_key(x, 9)
            orbit_kind = "x6_x9"

        side6_cell = pair_table[side6_pair]
        side9_cell = pair_table[side9_pair]
        side6_label = primary_symbol(side6_cell)
        side9_label = primary_symbol(side9_cell)
        mixed = side6_label != side9_label

        lower_label = sorted([side6_label, side9_label], key=symbol_sort_key)[0]
        higher_label = sorted([side6_label, side9_label], key=symbol_sort_key)[-1]
        if not mixed:
            lower_side = "both"
            higher_side = "both"
        elif side6_label == lower_label:
            lower_side = "6"
            higher_side = "9"
        else:
            lower_side = "9"
            higher_side = "6"

        rows.append(
            {
                "x": x,
                "orbit_kind": orbit_kind,
                "side6_pair": side6_pair,
                "side9_pair": side9_pair,
                "side6_label": side6_label,
                "side9_label": side9_label,
                "side6_symbols": cell_symbols(side6_cell),
                "side9_symbols": cell_symbols(side9_cell),
                "mixed_primary": mixed,
                "lower_label": lower_label,
                "higher_label": higher_label,
                "lower_label_side": lower_side,
                "higher_label_side": higher_side,
                "notes": orbit_notes(x, side6_pair, side9_pair, side6_cell, side9_cell),
            }
        )
    return rows


def orbit_notes(
    x: int,
    side6_pair: str,
    side9_pair: str,
    side6_cell: dict[str, Any],
    side9_cell: dict[str, Any],
) -> list[str]:
    notes = []
    if x == 0:
        notes.append("zero-edge orbit")
    if x == 8:
        notes.append("upper-edge neighbor of 9")
    if side9_pair == "19" or side6_pair == "19":
        notes.append("19/91 directed conflict cell")
    if side9_pair == "39" or side6_pair == "39":
        notes.append("ordered 39 absent; unordered cell represented by 93")
    if x in {3, 6}:
        notes.append("33/66 lore-digit family projection")
    if x in {4, 6}:
        notes.append("469 digit-family projection")
    if side6_cell["status"] == "conflict" or side9_cell["status"] == "conflict":
        notes.append("cell has multiple internal labels")
    return notes


def features_for_x(x: int) -> dict[str, int | bool]:
    side6 = pair_key(x, 6) if x != 6 else "66"
    side9 = pair_key(x, 9) if x != 6 else "99"
    return {
        "x": x,
        "orbit_index": x,
        "x_even": x % 2 == 0,
        "x_odd": x % 2 == 1,
        "x_mod3": x % 3,
        "x_mod4": x % 4,
        "x_mod5": x % 5,
        "x_low_0_3": x <= 3,
        "x_high_6_8": x >= 6,
        "x_edge_0_8": x in {0, 8},
        "x_middle_2_6": 2 <= x <= 6,
        "x_prime": x in {2, 3, 5, 7},
        "x_fibonacci_digit": x in {0, 1, 2, 3, 5, 8},
        "x_triangular_digit": x in {0, 1, 3, 6},
        "x_square_digit": x in {0, 1, 4},
        "x_center_distance_x2": int(abs(2 * x - 8)),
        "sum_with_6": x + 6,
        "sum_with_9": x + 9,
        "double_x_plus_15": 2 * x + 15,
        "pair6_index": triangular_pair_index(side6),
        "pair9_index": triangular_pair_index(side9),
        "pair_index_gap": triangular_pair_index(side9) - triangular_pair_index(side6),
        "lore_469_projected": x in {4, 6},
        "lore_39_projected": x == 3,
        "lore_19_projected": x == 1,
        "lore_33_66_projected": x in {3, 6},
        "lore_exception_19_or_39": x in {1, 3},
        "lore_any_named_projected": x in {1, 3, 4, 6},
    }


def named_set_rules() -> list[Rule]:
    named_sets: list[tuple[str, str, set[int], str, float, str]] = [
        ("position_edge_0_8", "x in table-edge digits {0,8}", {0, 8}, "position", 3.0, "atomic"),
        ("position_low_0_3", "x <= 3", {0, 1, 2, 3}, "position", 2.0, "atomic"),
        ("position_high_6_8", "x >= 6", {6, 7, 8}, "position", 2.0, "atomic"),
        ("arithmetic_even", "x even", {0, 2, 4, 6, 8}, "arithmetic", 1.5, "atomic"),
        ("arithmetic_odd", "x odd", {1, 3, 5, 7}, "arithmetic", 1.5, "atomic"),
        (
            "arithmetic_fibonacci_digits",
            "x in decimal Fibonacci digits {0,1,2,3,5,8}",
            {0, 1, 2, 3, 5, 8},
            "arithmetic",
            4.0,
            "atomic",
        ),
        (
            "arithmetic_triangular_digits",
            "x in triangular digits {0,1,3,6}",
            {0, 1, 3, 6},
            "arithmetic",
            4.0,
            "atomic",
        ),
        ("arithmetic_square_digits", "x in square digits {0,1,4}", {0, 1, 4}, "arithmetic", 4.0, "atomic"),
        ("lore_469_projected", "x in projected lore digits of 469: {4,6}", {4, 6}, "lore", 3.0, "atomic"),
        ("lore_39_projected", "x in projected lore digits of 39: {3}", {3}, "lore", 3.0, "atomic"),
        ("lore_19_projected", "x in projected lore digits of 19: {1}", {1}, "lore", 3.0, "atomic"),
        ("lore_33_66_projected", "x in projected 33/66 digits: {3,6}", {3, 6}, "lore", 3.0, "atomic"),
        (
            "lore_exception_19_or_39",
            "x in known anomaly anchors {1,3}",
            {1, 3},
            "lore",
            4.0,
            "atomic",
        ),
        (
            "lore_any_named_projected",
            "x in any projected named lore digits {1,3,4,6}",
            {1, 3, 4, 6},
            "lore",
            5.0,
            "atomic",
        ),
        (
            "position_edge_or_lore_exception_19_39",
            "x in edge digits {0,8} OR known anomaly anchors {1,3}",
            {0, 1, 3, 8},
            "composite_lore_position",
            8.0,
            "posthoc_composite",
        ),
    ]
    rules = [
        Rule(
            id=f"set_{name}",
            family=family,
            description=description,
            predicted_x=frozenset(values),
            complexity=complexity,
            status=status,
        )
        for name, description, values, family, complexity, status in named_sets
    ]
    for name, description, values, family, complexity, status in named_sets:
        if status == "posthoc_composite":
            continue
        rules.append(
            Rule(
                id=f"not_set_{name}",
                family=f"not_{family}",
                description=f"NOT ({description})",
                predicted_x=frozenset(set(X_DOMAIN) - values),
                complexity=complexity + 1.0,
                status=status,
            )
        )
    return rules


def generated_feature_rules() -> list[Rule]:
    feature_rows = {x: features_for_x(x) for x in X_DOMAIN}
    rules: list[Rule] = []
    numeric_features = [
        "x",
        "orbit_index",
        "x_center_distance_x2",
        "sum_with_6",
        "sum_with_9",
        "double_x_plus_15",
        "pair6_index",
        "pair9_index",
        "pair_index_gap",
    ]
    bool_features = [
        "x_even",
        "x_odd",
        "x_low_0_3",
        "x_high_6_8",
        "x_edge_0_8",
        "x_middle_2_6",
        "x_prime",
        "x_fibonacci_digit",
        "x_triangular_digit",
        "x_square_digit",
        "lore_469_projected",
        "lore_39_projected",
        "lore_19_projected",
        "lore_33_66_projected",
        "lore_exception_19_or_39",
        "lore_any_named_projected",
    ]
    for feature in bool_features:
        predicted = {x for x, row in feature_rows.items() if bool(row[feature])}
        rules.append(
            Rule(
                id=f"bool_{feature}",
                family="boolean_feature",
                description=f"{feature} is true",
                predicted_x=frozenset(predicted),
                complexity=2.0,
                status="atomic",
            )
        )
    for feature in numeric_features:
        values = sorted({int(row[feature]) for row in feature_rows.values()})
        for value in values:
            predicted_eq = {x for x, row in feature_rows.items() if int(row[feature]) == value}
            rules.append(
                Rule(
                    id=f"{feature}_eq_{value}",
                    family="numeric_equality",
                    description=f"{feature} == {value}",
                    predicted_x=frozenset(predicted_eq),
                    complexity=math.log2(len(values)) + 2.0,
                    status="atomic",
                )
            )
        for value in values[:-1]:
            predicted_le = {x for x, row in feature_rows.items() if int(row[feature]) <= value}
            rules.append(
                Rule(
                    id=f"{feature}_le_{value}",
                    family="numeric_threshold",
                    description=f"{feature} <= {value}",
                    predicted_x=frozenset(predicted_le),
                    complexity=math.log2(len(values)) + 1.0,
                    status="atomic",
                )
            )
        for value in values[1:]:
            predicted_ge = {x for x, row in feature_rows.items() if int(row[feature]) >= value}
            rules.append(
                Rule(
                    id=f"{feature}_ge_{value}",
                    family="numeric_threshold",
                    description=f"{feature} >= {value}",
                    predicted_x=frozenset(predicted_ge),
                    complexity=math.log2(len(values)) + 1.0,
                    status="atomic",
                )
            )
        for modulus in (2, 3, 4, 5):
            for residue in range(modulus):
                predicted_mod = {x for x, row in feature_rows.items() if int(row[feature]) % modulus == residue}
                rules.append(
                    Rule(
                        id=f"{feature}_mod_{modulus}_eq_{residue}",
                        family="numeric_mod",
                        description=f"{feature} mod {modulus} == {residue}",
                        predicted_x=frozenset(predicted_mod),
                        complexity=math.log2(modulus) + 2.0,
                        status="atomic",
                    )
                )
    return dedupe_rules(rules + named_set_rules())


def dedupe_rules(rules: list[Rule]) -> list[Rule]:
    best_by_key: dict[tuple[frozenset[int], str], Rule] = {}
    for rule in rules:
        key = (rule.predicted_x, rule.status)
        current = best_by_key.get(key)
        if current is None or (rule.complexity, len(rule.id), rule.id) < (current.complexity, len(current.id), current.id):
            best_by_key[key] = rule
    return sorted(best_by_key.values(), key=lambda rule: (rule.status != "atomic", rule.complexity, rule.id))


def score_rule(rule: Rule, target_x: set[int]) -> dict[str, Any]:
    predicted = set(rule.predicted_x)
    all_x = set(X_DOMAIN)
    tp = len(predicted & target_x)
    fp = len(predicted - target_x)
    fn = len(target_x - predicted)
    tn = len(all_x - predicted - target_x)
    accuracy = (tp + tn) / len(all_x)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    errors = fp + fn
    correction_bits = 0.0 if errors == 0 else math.log2(math.comb(len(all_x), errors)) + errors
    lossless_bits = rule.complexity + correction_bits
    return {
        "id": rule.id,
        "family": rule.family,
        "description": rule.description,
        "status": rule.status,
        "predicted_x": sorted(predicted),
        "target_x": sorted(target_x),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "errors": errors,
        "complexity_bits": rule.complexity,
        "lossless_bits_rough": lossless_bits,
    }


def best_rule_scores(rules: list[Rule], target_x: set[int], include_posthoc: bool = True) -> list[dict[str, Any]]:
    scoped = rules if include_posthoc else [rule for rule in rules if rule.status == "atomic"]
    rows = [score_rule(rule, target_x) for rule in scoped]
    rows.sort(
        key=lambda row: (
            -row["accuracy"],
            -row["f1"],
            row["lossless_bits_rough"],
            row["status"] != "atomic",
            row["id"],
        )
    )
    return rows


def summarize(values: list[float], observed: float, high_is_good: bool = True) -> dict[str, Any]:
    avg = mean(values)
    sd = pstdev(values)
    if high_is_good:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - avg) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (avg - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "trials": len(values),
        "control_mean": avg,
        "control_sd_population": sd,
        "control_min": min(values),
        "control_max": max(values),
        "p_value_good_direction": p,
        "z_good_direction": z,
    }


def same_size_subset_control(rules: list[Rule], observed_target: set[int], include_posthoc: bool) -> dict[str, Any]:
    scoped = rules if include_posthoc else [rule for rule in rules if rule.status == "atomic"]
    observed_best = best_rule_scores(scoped, observed_target, include_posthoc=True)[0]
    values = []
    exact_hits = 0
    for subset in itertools.combinations(X_DOMAIN, len(observed_target)):
        target = set(subset)
        best = best_rule_scores(scoped, target, include_posthoc=True)[0]
        values.append(best["accuracy"])
        if best["accuracy"] == 1.0:
            exact_hits += 1
    summary = summarize(values, observed_best["accuracy"])
    summary.update(
        {
            "null": f"all x-subsets of size {len(observed_target)} scored against the same rule family",
            "candidate_rule_count": len(scoped),
            "exact_subset_hits": exact_hits,
            "exact_subset_rate": exact_hits / len(values),
        }
    )
    return summary


def shuffled_mixed_target(labels: dict[str, str], orbit_rows: list[dict[str, Any]]) -> set[int]:
    target = set()
    for row in orbit_rows:
        if labels[row["side6_pair"]] != labels[row["side9_pair"]]:
            target.add(int(row["x"]))
    return target


def label_shuffle_control(
    rules: list[Rule],
    observed_target: set[int],
    orbit_rows: list[dict[str, Any]],
    labels: dict[str, str],
    include_posthoc: bool,
) -> dict[str, Any]:
    scoped = rules if include_posthoc else [rule for rule in rules if rule.status == "atomic"]
    observed_best = best_rule_scores(scoped, observed_target, include_posthoc=True)[0]
    rng = random.Random(RANDOM_SEED + (17 if include_posthoc else 31))
    pairs = natural_pairs()
    values = []
    target_sizes = []
    same_size_values = []
    label_values = [labels[pair] for pair in pairs]
    for _trial in range(LABEL_SHUFFLE_TRIALS):
        shuffled = label_values[:]
        rng.shuffle(shuffled)
        shuffled_labels = dict(zip(pairs, shuffled))
        target = shuffled_mixed_target(shuffled_labels, orbit_rows)
        best = best_rule_scores(scoped, target, include_posthoc=True)[0]
        values.append(best["accuracy"])
        target_sizes.append(len(target))
        if len(target) == len(observed_target):
            same_size_values.append(best["accuracy"])
    out = summarize(values, observed_best["accuracy"])
    out.update(
        {
            "null": "inventory-preserving shuffle of 55 unordered pair labels, then recompute mixed 6<->9 orbits",
            "candidate_rule_count": len(scoped),
            "observed_mixed_count": len(observed_target),
            "shuffle_mixed_count_mean": mean(target_sizes),
            "shuffle_mixed_count_distribution": dict(sorted(Counter(target_sizes).items())),
        }
    )
    if same_size_values:
        out["same_mixed_count_only"] = summarize(same_size_values, observed_best["accuracy"])
    else:
        out["same_mixed_count_only"] = None
    return out


def build_side_rules() -> list[SideRule]:
    feature_rows = {x: features_for_x(x) for x in X_DOMAIN}
    rules = [
        SideRule("always_6", "constant", "lower/canonical label side is always 6", 1.0, "atomic", tuple("6" for _ in X_DOMAIN)),
        SideRule("always_9", "constant", "lower/canonical label side is always 9", 1.0, "atomic", tuple("9" for _ in X_DOMAIN)),
        SideRule(
            "parity_even_6_odd_9",
            "arithmetic",
            "lower/canonical label side is 6 for even x, 9 for odd x",
            2.0,
            "atomic",
            tuple("6" if x % 2 == 0 else "9" for x in X_DOMAIN),
        ),
        SideRule(
            "parity_even_9_odd_6",
            "arithmetic",
            "lower/canonical label side is 9 for even x, 6 for odd x",
            2.0,
            "atomic",
            tuple("9" if x % 2 == 0 else "6" for x in X_DOMAIN),
        ),
    ]
    named_sets = {
        "position_edge_0_8": {0, 8},
        "lore_exception_19_or_39": {1, 3},
        "lore_any_named_projected": {1, 3, 4, 6},
        "arithmetic_fibonacci_digits": {0, 1, 2, 3, 5, 8},
        "arithmetic_triangular_digits": {0, 1, 3, 6},
        "position_edge_or_lore_exception_19_39": {0, 1, 3, 8},
    }
    for name, values in named_sets.items():
        status = "posthoc_composite" if name == "position_edge_or_lore_exception_19_39" else "atomic"
        for side_in, side_out in [("6", "9"), ("9", "6")]:
            rules.append(
                SideRule(
                    id=f"{name}_in_{side_in}_else_{side_out}",
                    family="membership_side",
                    description=f"if x in {sorted(values)} then side {side_in}, else side {side_out}",
                    complexity=4.0 if status == "atomic" else 8.0,
                    status=status,
                    side_for_x=tuple(side_in if x in values else side_out for x in X_DOMAIN),
                )
            )
    for feature in ["x", "orbit_index", "sum_with_6", "sum_with_9", "pair6_index", "pair9_index"]:
        values = sorted({int(row[feature]) for row in feature_rows.values()})
        for value in values[:-1]:
            for side_in, side_out in [("6", "9"), ("9", "6")]:
                rules.append(
                    SideRule(
                        id=f"{feature}_le_{value}_in_{side_in}_else_{side_out}",
                        family="threshold_side",
                        description=f"if {feature} <= {value} then side {side_in}, else side {side_out}",
                        complexity=math.log2(len(values)) + 2.0,
                        status="atomic",
                        side_for_x=tuple(side_in if int(feature_rows[x][feature]) <= value else side_out for x in X_DOMAIN),
                    )
                )
        for modulus in (2, 3, 4):
            for residue in range(modulus):
                for side_in, side_out in [("6", "9"), ("9", "6")]:
                    rules.append(
                        SideRule(
                            id=f"{feature}_mod_{modulus}_eq_{residue}_in_{side_in}_else_{side_out}",
                            family="mod_side",
                            description=f"if {feature} mod {modulus} == {residue} then side {side_in}, else side {side_out}",
                            complexity=math.log2(modulus) + 3.0,
                            status="atomic",
                            side_for_x=tuple(
                                side_in if int(feature_rows[x][feature]) % modulus == residue else side_out for x in X_DOMAIN
                            ),
                        )
                    )
    return dedupe_side_rules(rules)


def dedupe_side_rules(rules: list[SideRule]) -> list[SideRule]:
    best_by_key: dict[tuple[tuple[str, ...], str], SideRule] = {}
    for rule in rules:
        key = (rule.side_for_x, rule.status)
        current = best_by_key.get(key)
        if current is None or (rule.complexity, len(rule.id), rule.id) < (current.complexity, len(current.id), current.id):
            best_by_key[key] = rule
    return sorted(best_by_key.values(), key=lambda rule: (rule.status != "atomic", rule.complexity, rule.id))


def score_side_rule(rule: SideRule, targets: dict[int, str]) -> dict[str, Any]:
    correct = sum(rule.side_for_x[x] == side for x, side in targets.items())
    total = len(targets)
    errors = [
        {"x": x, "actual_side": side, "predicted_side": rule.side_for_x[x]}
        for x, side in sorted(targets.items())
        if rule.side_for_x[x] != side
    ]
    return {
        "id": rule.id,
        "family": rule.family,
        "description": rule.description,
        "status": rule.status,
        "correct": correct,
        "total": total,
        "accuracy": correct / total if total else 0.0,
        "errors": errors,
        "complexity_bits": rule.complexity,
    }


def best_side_scores(side_rules: list[SideRule], targets: dict[int, str], include_posthoc: bool = True) -> list[dict[str, Any]]:
    scoped = side_rules if include_posthoc else [rule for rule in side_rules if rule.status == "atomic"]
    rows = [score_side_rule(rule, targets) for rule in scoped]
    rows.sort(key=lambda row: (-row["accuracy"], row["complexity_bits"], row["status"] != "atomic", row["id"]))
    return rows


def side_same_shape_control(side_rules: list[SideRule], observed_targets: dict[int, str], include_posthoc: bool) -> dict[str, Any]:
    scoped = side_rules if include_posthoc else [rule for rule in side_rules if rule.status == "atomic"]
    observed = best_side_scores(scoped, observed_targets, include_posthoc=True)[0]
    side6_count = sum(side == "6" for side in observed_targets.values())
    values = []
    exact_hits = 0
    total_assignments = 0
    for subset in itertools.combinations(X_DOMAIN, len(observed_targets)):
        for side6_x in itertools.combinations(subset, side6_count):
            side6_set = set(side6_x)
            targets = {x: ("6" if x in side6_set else "9") for x in subset}
            best = best_side_scores(scoped, targets, include_posthoc=True)[0]
            values.append(best["accuracy"])
            exact_hits += int(best["accuracy"] == 1.0)
            total_assignments += 1
    out = summarize(values, observed["accuracy"])
    out.update(
        {
            "null": "all same-size mixed-x subsets and same 6/9 side-count assignments",
            "candidate_rule_count": len(scoped),
            "mixed_count": len(observed_targets),
            "side6_count": side6_count,
            "exact_assignment_hits": exact_hits,
            "exact_assignment_rate": exact_hits / total_assignments,
        }
    )
    return out


def observed_side_targets(orbit_rows: list[dict[str, Any]]) -> dict[int, str]:
    return {
        int(row["x"]): str(row["lower_label_side"])
        for row in orbit_rows
        if row["mixed_primary"] and row["lower_label_side"] in {"6", "9"}
    }


def verdict(result: dict[str, Any]) -> str:
    best_atomic = result["mixed_rule_search"]["best_atomic"]
    best_all = result["mixed_rule_search"]["best_all"]
    best_side = result["side_rule_search"]["best_atomic"]
    if best_all["errors"] == 0 and best_all["status"] == "posthoc_composite" and best_atomic["errors"] > 0:
        if best_side["accuracy"] == 1.0:
            return "posthoc_descriptive_exception_rule_side_parity_weak"
        return "posthoc_descriptive_exception_rule_weak"
    if best_atomic["errors"] == 0 and best_side["accuracy"] == 1.0:
        return "candidate_simple_exception_rule_requires_external_validation"
    if best_atomic["errors"] == 0:
        return "candidate_simple_mixed_orbit_rule_requires_external_validation"
    return "no_simple_atomic_rule_found"


def write_report(result: dict[str, Any]) -> None:
    observed = result["observed"]
    mixed = result["mixed_rule_search"]
    side = result["side_rule_search"]
    controls = result["controls"]
    lines = [
        "# Digit Orbit Exception Arithmetic Search",
        "",
        "Generated by `digit_orbit_exception_arithmetic_search.py`.",
        "",
        "Scope: non-singleton unordered-pair orbits under the quotient `6<->9`.",
        "This is mechanical-only analysis: no plaintext, glossary, or translation",
        "claim is introduced. `translation_delta=NONE`.",
        "",
        "## Answer",
        "",
        "Atomic arithmetic/lore/position predicates do not isolate the four mixed",
        "`6<->9` orbits. The best exact description is a two-part exception",
        "description: mixed iff `x` is a table edge digit `{0,8}` or one of the",
        "known anomaly anchors `{1,3}` from `19`/`39`. Because that rule is a",
        "composite selected in this micro-search over only nine orbits, this report",
        "treats it as descriptive bookkeeping, not as the recovered original",
        "generator.",
        "",
        "For the side question, among the four mixed orbits the lower/canonical",
        "internal label is on the `6` side for even `x` and on the `9` side for",
        "odd `x`. This is exact on `x={0,1,3,8}` but has only four observations,",
        "so it is a weak side-pattern, not a promotion gate.",
        "",
        "## Observed Orbits",
        "",
        "| x | 6-side pair | 6-side label(s) | 9-side pair | 9-side label(s) | Mixed? | Lower-label side | Notes |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for row in observed["orbit_rows"]:
        lines.append(
            "| {x} | `{p6}` | `{l6}` | `{p9}` | `{l9}` | {mixed} | `{side}` | {notes} |".format(
                x=row["x"],
                p6=row["side6_pair"],
                l6="/".join(row["side6_symbols"]),
                p9=row["side9_pair"],
                l9="/".join(row["side9_symbols"]),
                mixed="yes" if row["mixed_primary"] else "no",
                side=row["lower_label_side"],
                notes=", ".join(row["notes"]) if row["notes"] else "-",
            )
        )
    lines.extend(
        [
            "",
            "## Mixed-Orbit Rule Search",
            "",
            f"- Observed mixed x-set: `{observed['mixed_x']}`.",
            f"- Best atomic rule: `{mixed['best_atomic']['id']}` with accuracy `{mixed['best_atomic']['accuracy']:.3f}` and errors `{mixed['best_atomic']['errors']}`.",
            f"- Best overall rule: `{mixed['best_all']['id']}` with accuracy `{mixed['best_all']['accuracy']:.3f}` and errors `{mixed['best_all']['errors']}`.",
            "",
            "| Rule | Status | Predicted x | Accuracy | TP | FP | FN | Description |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in mixed["top_rules"][:12]:
        lines.append(
            f"| `{row['id']}` | `{row['status']}` | `{row['predicted_x']}` | {row['accuracy']:.3f} | {row['tp']} | {row['fp']} | {row['fn']} | {row['description']} |"
        )
    lines.extend(
        [
            "",
            "## Side Rule Search",
            "",
            "Target: for mixed orbits only, which side carries the lower/canonical",
            "internal label under the fixed symbol order used by the quotient pass.",
            "",
            f"- Observed side targets: `{side['observed_targets']}`.",
            f"- Best atomic side rule: `{side['best_atomic']['id']}` with accuracy `{side['best_atomic']['accuracy']:.3f}`.",
            "",
            "| Rule | Status | Accuracy | Description |",
            "|---|---|---:|---|",
        ]
    )
    for row in side["top_rules"][:8]:
        lines.append(f"| `{row['id']}` | `{row['status']}` | {row['accuracy']:.3f} | {row['description']} |")
    lines.extend(
        [
            "",
            "## Controls",
            "",
            "| Control | Rule family | Observed | Mean | Max | p(good) | Notes |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for key, label, family in [
        ("mixed_same_size_atomic", "same-size x-subsets", "atomic"),
        ("mixed_same_size_all", "same-size x-subsets", "all incl. composite"),
        ("mixed_label_shuffle_atomic", "55-cell label shuffle", "atomic"),
        ("mixed_label_shuffle_all", "55-cell label shuffle", "all incl. composite"),
        ("side_same_shape_atomic", "same-shape side assignments", "atomic"),
        ("side_same_shape_all", "same-shape side assignments", "all incl. composite"),
    ]:
        row = controls[key]
        lines.append(
            f"| {label} | {family} | {row['observed']:.3f} | {row['control_mean']:.3f} | {row['control_max']:.3f} | {row['p_value_good_direction']:.5f} | {row['null']} |"
        )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"`{result['verdict']}`.",
            "",
            "Conservative reading: the edge-or-anomaly rule is useful as a compact",
            "exception ledger for the `6<->9` quotient, and parity exactly describes",
            "the side split inside the four mixed rows. Neither result is sufficient",
            "to promote a formula origin, a translation, or a glossary entry. The",
            "next admissible upgrade would need to predict these exceptions from an",
            "independent mechanical source rather than from this tiny observed set.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    orbit_rows = build_orbits(formula)
    mixed_x = {int(row["x"]) for row in orbit_rows if row["mixed_primary"]}
    pure_x = set(X_DOMAIN) - mixed_x

    rules = generated_feature_rules()
    atomic_scores = best_rule_scores(rules, mixed_x, include_posthoc=False)
    all_scores = best_rule_scores(rules, mixed_x, include_posthoc=True)

    side_rules = build_side_rules()
    side_targets = observed_side_targets(orbit_rows)
    side_atomic = best_side_scores(side_rules, side_targets, include_posthoc=False)
    side_all = best_side_scores(side_rules, side_targets, include_posthoc=True)

    labels = pair_table_labels(formula)
    controls = {
        "mixed_same_size_atomic": same_size_subset_control(rules, mixed_x, include_posthoc=False),
        "mixed_same_size_all": same_size_subset_control(rules, mixed_x, include_posthoc=True),
        "mixed_label_shuffle_atomic": label_shuffle_control(rules, mixed_x, orbit_rows, labels, include_posthoc=False),
        "mixed_label_shuffle_all": label_shuffle_control(rules, mixed_x, orbit_rows, labels, include_posthoc=True),
        "side_same_shape_atomic": side_same_shape_control(side_rules, side_targets, include_posthoc=False),
        "side_same_shape_all": side_same_shape_control(side_rules, side_targets, include_posthoc=True),
    }

    result: dict[str, Any] = {
        "schema": "digit_orbit_exception_arithmetic_results.v1",
        "translation_delta": "NONE",
        "random_seed": RANDOM_SEED,
        "label_shuffle_trials": LABEL_SHUFFLE_TRIALS,
        "inputs": {
            "formula_json": str(FORMULA_JSON.relative_to(ROOT)),
            "scope": "nine non-singleton unordered-pair orbits under digit swap 6<->9",
        },
        "observed": {
            "mixed_x": sorted(mixed_x),
            "pure_x": sorted(pure_x),
            "orbit_rows": orbit_rows,
        },
        "mixed_rule_search": {
            "candidate_rule_count": len(rules),
            "atomic_rule_count": sum(rule.status == "atomic" for rule in rules),
            "best_atomic": atomic_scores[0],
            "best_all": all_scores[0],
            "top_rules": all_scores[:30],
        },
        "side_rule_search": {
            "candidate_rule_count": len(side_rules),
            "atomic_rule_count": sum(rule.status == "atomic" for rule in side_rules),
            "observed_targets": dict(sorted(side_targets.items())),
            "best_atomic": side_atomic[0],
            "best_all": side_all[0],
            "top_rules": side_all[:20],
        },
        "controls": controls,
    }
    result["verdict"] = verdict(result)
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "mixed_x={mixed} best_atomic={atomic}:{aerr}err best_all={best}:{berr}err side={side}:{sacc:.3f} verdict={verdict}".format(
            mixed=sorted(mixed_x),
            atomic=atomic_scores[0]["id"],
            aerr=atomic_scores[0]["errors"],
            best=all_scores[0]["id"],
            berr=all_scores[0]["errors"],
            side=side_atomic[0]["id"],
            sacc=side_atomic[0]["accuracy"],
            verdict=result["verdict"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
