#!/usr/bin/env python3
"""Context/tape audit for the `6 <-> 9` digit-orbit exceptions.

`digit_orbit_quotient_search.py` found that swapping digits 6 and 9 compresses
the unordered pair table with four mixed two-cell orbits. This follow-up asks a
narrower question: do those four mixed orbits have an auditable mechanical
pattern, using only already-attested usage, raw-neighbourhood context, and tape
features?

Mechanical only. No plaintext, glossary, or translation is promoted.
"""

from __future__ import annotations

import itertools
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import pair_context_cluster_search as context_search  # noqa: E402
import tape_feature_pair_label_search as tape_feature_search  # noqa: E402


MECHANICAL_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
QUOTIENT_JSON = HERE / "digit_orbit_quotient_results.json"
TAPE_FORMULA_JSON = HERE / "tape_based_formula_469.json"

OUT_JSON = HERE / "digit_orbit_exception_context_results.json"
OUT_MD = HERE / "digit_orbit_exception_context_report.md"

EXPECTED_MIXED_ORBITS = [
    ("06", "09"),
    ("16", "19"),
    ("36", "39"),
    ("68", "89"),
]
EXPECTED_UNIFORM_ORBITS = [
    ("26", "29"),
    ("46", "49"),
    ("56", "59"),
    ("66", "99"),
    ("67", "79"),
]

NUMERIC_EPS = 1e-12


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def primary_pair_symbol(pair_table: dict[str, dict[str, Any]], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def display_pair_symbol(pair_table: dict[str, dict[str, Any]], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return "/".join(sorted(row["symbols"]))


def side_pairs(pairs: list[str]) -> tuple[str, str]:
    """Return the 6-side and 9-side cells for a non-singleton `6 <-> 9` orbit."""

    if set(pairs) == {"66", "99"}:
        return "66", "99"
    six_side = [pair for pair in pairs if "6" in pair and "9" not in pair]
    nine_side = [pair for pair in pairs if "9" in pair and "6" not in pair]
    if len(six_side) != 1 or len(nine_side) != 1:
        raise ValueError(f"cannot orient orbit pairs={pairs}")
    return six_side[0], nine_side[0]


def load_target_orbits(quotient: dict[str, Any], pair_table: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    swap = quotient["swap_6_9"]
    rows = [row for row in swap["orbits"] if row["size"] == 2]
    observed_mixed = [tuple(row["pairs"]) for row in rows if row["is_mixed"]]
    observed_uniform = [tuple(row["pairs"]) for row in rows if not row["is_mixed"]]
    if observed_mixed != EXPECTED_MIXED_ORBITS:
        raise ValueError(f"mixed orbit drift: {observed_mixed}")
    if observed_uniform != EXPECTED_UNIFORM_ORBITS:
        raise ValueError(f"uniform orbit drift: {observed_uniform}")

    out = []
    for row in rows:
        six_pair, nine_pair = side_pairs(row["pairs"])
        out.append(
            {
                "orbit": row["orbit"],
                "pairs": row["pairs"],
                "six_side_pair": six_pair,
                "nine_side_pair": nine_pair,
                "label_counts": row["label_counts"],
                "is_mixed": bool(row["is_mixed"]),
                "primary_symbols": {
                    pair: primary_pair_symbol(pair_table, pair)
                    for pair in row["pairs"]
                },
                "display_symbols": {
                    pair: display_pair_symbol(pair_table, pair)
                    for pair in row["pairs"]
                },
            }
        )
    return out


def entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    value = 0.0
    for count in counter.values():
        p = count / total
        value -= p * math.log2(p)
    return value


def counter_jaccard(left: Counter[str], right: Counter[str]) -> float:
    left_keys = {key for key, value in left.items() if value}
    right_keys = {key for key, value in right.items() if value}
    union = left_keys | right_keys
    if not union:
        return 1.0
    return len(left_keys & right_keys) / len(union)


def ordered_code_stats(mechanical: dict[str, Any], pair: str) -> dict[str, float]:
    codes = mechanical["pair_table"][pair]["codes"]
    counts = Counter({code: int(mechanical["code_counts"].get(code, 0)) for code in codes})
    total = sum(counts.values())
    dominant = max(counts.values()) if counts else 0
    return {
        "ordered_code_count": float(len(codes)),
        "usage_total": float(total),
        "orientation_entropy": entropy(counts),
        "dominant_order_fraction": dominant / total if total else 0.0,
    }


def tape_component_set(tape_features: dict[str, Any]) -> set[str]:
    return {
        key.removeprefix("in_component_")
        for key, value in tape_features.items()
        if key.startswith("in_component_") and bool(value)
    }


def pair_feature_rows(
    mechanical: dict[str, Any],
    tape_formula: dict[str, Any],
    contexts: dict[str, dict[str, Counter[str]]],
    context_counts: Counter[str],
) -> dict[str, dict[str, Any]]:
    projected = tape_feature_search.project(tape_formula)
    tape_features = tape_feature_search.tape_features_by_pair(tape_formula, projected)
    rows = {}
    for pair in all_pairs():
        tape = tape_features[pair]
        component_set = tape_component_set(tape)
        ordered = ordered_code_stats(mechanical, pair)
        row: dict[str, Any] = {
            "pair": pair,
            "primary_symbol": primary_pair_symbol(mechanical["pair_table"], pair),
            "display_symbol": display_pair_symbol(mechanical["pair_table"], pair),
            "context_token_count": float(context_counts[pair]),
            "component_set": sorted(component_set),
            "component_count": float(len(component_set)),
            **ordered,
        }
        for key, value in tape.items():
            if key.startswith("in_component_"):
                continue
            if isinstance(value, bool):
                row[key] = float(int(value))
            elif isinstance(value, int):
                row[key] = float(value)
        for feature, by_pair in contexts.items():
            row[f"{feature}_entropy"] = entropy(by_pair[pair])
            row[f"{feature}_distinct"] = float(len(by_pair[pair]))
        rows[pair] = row
    return rows


def numeric(value: Any) -> float:
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    raise TypeError(value)


def add_delta_features(out: dict[str, float], prefix: str, left: float, right: float) -> None:
    out[f"{prefix}_six"] = left
    out[f"{prefix}_nine"] = right
    out[f"{prefix}_sum"] = left + right
    out[f"{prefix}_min"] = min(left, right)
    out[f"{prefix}_max"] = max(left, right)
    out[f"{prefix}_abs_delta"] = abs(right - left)
    out[f"{prefix}_signed_9minus6"] = right - left
    out[f"{prefix}_ratio_9_over_6_smooth"] = (right + 1.0) / (left + 1.0)


def orbit_feature_row(
    orbit: dict[str, Any],
    pair_rows: dict[str, dict[str, Any]],
    pair_index: dict[str, int],
    context_matrices: dict[str, list[list[float]]],
    contexts: dict[str, dict[str, Counter[str]]],
) -> dict[str, Any]:
    six_pair = orbit["six_side_pair"]
    nine_pair = orbit["nine_side_pair"]
    six = pair_rows[six_pair]
    nine = pair_rows[nine_pair]
    features: dict[str, float] = {}

    scalar_features = [
        "usage_total",
        "context_token_count",
        "orientation_entropy",
        "dominant_order_fraction",
        "total_tokens",
        "tape_tokens",
        "outside_tokens",
        "literal_only_tokens",
        "boundary_cross_tokens",
        "tape_fraction_pct",
        "outside_fraction_pct",
        "unique_components",
        "first_component",
        "first_component_start_bin",
        "first_tape_position",
        "only_outside",
        "tape_only",
        "mixed_tape_literal",
        "omitted_zero_tape",
        "omitted_zero_outside",
        "component_count",
    ]
    for key in scalar_features:
        add_delta_features(features, key, numeric(six.get(key, 0.0)), numeric(nine.get(key, 0.0)))

    six_components = set(six["component_set"])
    nine_components = set(nine["component_set"])
    union = six_components | nine_components
    features["component_shared_count"] = float(len(six_components & nine_components))
    features["component_symdiff_count"] = float(len(six_components ^ nine_components))
    features["component_jaccard"] = float(len(six_components & nine_components) / len(union)) if union else 1.0

    left_index = pair_index[six_pair]
    right_index = pair_index[nine_pair]
    for feature, matrix in context_matrices.items():
        features[f"context_{feature}_jsd"] = matrix[left_index][right_index]
        features[f"context_{feature}_support_jaccard"] = counter_jaccard(contexts[feature][six_pair], contexts[feature][nine_pair])
        add_delta_features(
            features,
            f"context_{feature}_entropy",
            numeric(six[f"{feature}_entropy"]),
            numeric(nine[f"{feature}_entropy"]),
        )
        add_delta_features(
            features,
            f"context_{feature}_distinct",
            numeric(six[f"{feature}_distinct"]),
            numeric(nine[f"{feature}_distinct"]),
        )

    return {
        "orbit": orbit["orbit"],
        "pairs": orbit["pairs"],
        "six_side_pair": six_pair,
        "nine_side_pair": nine_pair,
        "is_mixed": orbit["is_mixed"],
        "primary_symbols": orbit["primary_symbols"],
        "display_symbols": orbit["display_symbols"],
        "label_counts": orbit["label_counts"],
        "features": dict(sorted(features.items())),
    }


def feature_families(feature_ids: list[str]) -> dict[str, list[str]]:
    usage = [
        feature
        for feature in feature_ids
        if feature.startswith("usage_total_")
        or feature.startswith("context_token_count_")
        or feature.startswith("orientation_entropy_")
        or feature.startswith("dominant_order_fraction_")
    ]
    tape = [
        feature
        for feature in feature_ids
        if feature.startswith(
            (
                "total_tokens_",
                "tape_tokens_",
                "outside_tokens_",
                "literal_only_tokens_",
                "boundary_cross_tokens_",
                "tape_fraction_pct_",
                "outside_fraction_pct_",
                "unique_components_",
                "first_component_",
                "first_tape_position_",
                "only_outside_",
                "tape_only_",
                "mixed_tape_literal_",
                "omitted_zero_",
                "component_",
            )
        )
    ]
    context = [
        feature
        for feature in feature_ids
        if feature.startswith("context_prev_")
        or feature.startswith("context_next_")
        or feature.startswith("context_pair_window_")
    ]
    return {
        "usage_only": sorted(usage),
        "tape_only": sorted(tape),
        "context_only": sorted(context),
        "context_usage_tape": sorted(set(usage + tape + context)),
    }


def build_predicates(orbit_rows: list[dict[str, Any]], feature_ids: list[str]) -> list[dict[str, Any]]:
    predicates: list[dict[str, Any]] = []
    for feature in feature_ids:
        values = sorted({numeric(row["features"][feature]) for row in orbit_rows})
        if len(values) < 2:
            continue
        if set(values) <= {0.0, 1.0}:
            predicates.append({"id": f"{feature}==1", "feature": feature, "op": "==", "value": 1.0})
            predicates.append({"id": f"{feature}==0", "feature": feature, "op": "==", "value": 0.0})
            continue
        thresholds = [(left + right) / 2.0 for left, right in zip(values, values[1:]) if abs(left - right) > NUMERIC_EPS]
        for threshold in thresholds:
            predicates.append({"id": f"{feature}<={threshold:.6g}", "feature": feature, "op": "<=", "value": threshold})
            predicates.append({"id": f"{feature}>={threshold:.6g}", "feature": feature, "op": ">=", "value": threshold})
    return predicates


def predicate_matches(predicate: dict[str, Any], row: dict[str, Any]) -> bool:
    value = numeric(row["features"][predicate["feature"]])
    if predicate["op"] == "<=":
        return value <= predicate["value"]
    if predicate["op"] == ">=":
        return value >= predicate["value"]
    if predicate["op"] == "==":
        return abs(value - predicate["value"]) <= NUMERIC_EPS
    raise ValueError(predicate)


def score_predictions(predicted: list[bool], actual: list[bool]) -> dict[str, Any]:
    tp = sum(p and a for p, a in zip(predicted, actual))
    fp = sum(p and not a for p, a in zip(predicted, actual))
    tn = sum((not p) and (not a) for p, a in zip(predicted, actual))
    fn = sum((not p) and a for p, a in zip(predicted, actual))
    total = len(actual)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "accuracy": (tp + tn) / total,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "balanced_accuracy": (recall + specificity) / 2.0,
        "f1": f1,
        "predicted_positive_count": sum(predicted),
    }


def row_for_predicate(
    predicate: dict[str, Any],
    orbit_rows: list[dict[str, Any]],
    actual: list[bool],
    family: str,
) -> dict[str, Any]:
    predicted = [predicate_matches(predicate, row) for row in orbit_rows]
    score = score_predictions(predicted, actual)
    return {
        "family": family,
        "rule_class": "stump",
        "predicate": predicate,
        "positive_orbits": [
            {"orbit": row["orbit"], "pairs": row["pairs"]}
            for row, pred in zip(orbit_rows, predicted)
            if pred
        ],
        **score,
    }


def best_rule_for_labels(
    orbit_rows: list[dict[str, Any]],
    predicates: list[dict[str, Any]],
    labels: list[bool],
    family: str,
) -> dict[str, Any]:
    scored = [row_for_predicate(predicate, orbit_rows, labels, family) for predicate in predicates]
    scored.sort(
        key=lambda row: (
            -row["balanced_accuracy"],
            -row["f1"],
            -row["accuracy"],
            row["predicted_positive_count"],
            row["predicate"]["id"],
        )
    )
    return scored[0]


def summarize(values: list[float], observed: float) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "control_min": min(values),
        "control_max": max(values),
        "p_good_direction": sum(value >= observed - NUMERIC_EPS for value in values) / len(values),
        "z_good_direction": (observed - mean) / sd if sd else 0.0,
    }


def exact_label_controls(
    orbit_rows: list[dict[str, Any]],
    predicates: list[dict[str, Any]],
    observed: dict[str, Any],
    family: str,
) -> dict[str, Any]:
    n = len(orbit_rows)
    positive_count = sum(row["is_mixed"] for row in orbit_rows)
    balanced_values = []
    f1_values = []
    accuracy_values = []
    exact_values = []
    for positive_indices in itertools.combinations(range(n), positive_count):
        positive_set = set(positive_indices)
        labels = [index in positive_set for index in range(n)]
        best = best_rule_for_labels(orbit_rows, predicates, labels, family)
        balanced_values.append(best["balanced_accuracy"])
        f1_values.append(best["f1"])
        accuracy_values.append(best["accuracy"])
        exact_values.append(1.0 if best["accuracy"] == 1.0 else 0.0)
    return {
        "control_type": "exhaustive_label_shuffle_preserve_4_of_9",
        "control_labelings": len(balanced_values),
        "balanced_accuracy": summarize(balanced_values, observed["balanced_accuracy"]),
        "f1": summarize(f1_values, observed["f1"]),
        "accuracy": summarize(accuracy_values, observed["accuracy"]),
        "exact_separation_rate": sum(exact_values) / len(exact_values),
    }


def leave_one_out(
    orbit_rows: list[dict[str, Any]],
    predicates: list[dict[str, Any]],
    family: str,
) -> dict[str, Any]:
    actual = [row["is_mixed"] for row in orbit_rows]
    predictions = []
    details = []
    for holdout_index, holdout in enumerate(orbit_rows):
        train_rows = [row for index, row in enumerate(orbit_rows) if index != holdout_index]
        train_labels = [label for index, label in enumerate(actual) if index != holdout_index]
        best = best_rule_for_labels(train_rows, predicates, train_labels, family)
        pred = predicate_matches(best["predicate"], holdout)
        predictions.append(pred)
        details.append(
            {
                "heldout_orbit": holdout["orbit"],
                "heldout_pairs": holdout["pairs"],
                "actual_mixed": holdout["is_mixed"],
                "predicted_mixed": pred,
                "train_predicate": best["predicate"],
            }
        )
    return {
        "accuracy": sum(pred == truth for pred, truth in zip(predictions, actual)) / len(actual),
        "correct": sum(pred == truth for pred, truth in zip(predictions, actual)),
        "total": len(actual),
        "details": details,
    }


def evaluate_families(orbit_rows: list[dict[str, Any]]) -> dict[str, Any]:
    feature_ids = sorted(next(iter(orbit_rows))["features"])
    families = feature_families(feature_ids)
    actual = [row["is_mixed"] for row in orbit_rows]
    family_rows = []
    top_rules_by_family = {}
    for family, features in families.items():
        predicates = build_predicates(orbit_rows, features)
        best = best_rule_for_labels(orbit_rows, predicates, actual, family)
        controls = exact_label_controls(orbit_rows, predicates, best, family)
        loocv = leave_one_out(orbit_rows, predicates, family)
        best["controls"] = controls
        best["leave_one_out"] = loocv
        best["feature_count"] = len(features)
        best["predicate_count"] = len(predicates)
        top_rules_by_family[family] = [
            row_for_predicate(predicate, orbit_rows, actual, family)
            for predicate in predicates
        ]
        top_rules_by_family[family].sort(
            key=lambda row: (
                -row["balanced_accuracy"],
                -row["f1"],
                -row["accuracy"],
                row["predicted_positive_count"],
                row["predicate"]["id"],
            )
        )
        family_rows.append(best)
    family_rows.sort(
        key=lambda row: (
            row["controls"]["balanced_accuracy"]["p_good_direction"],
            -row["balanced_accuracy"],
            row["family"],
        )
    )
    for row in family_rows:
        row["bonferroni_p_balanced_accuracy"] = min(
            1.0,
            row["controls"]["balanced_accuracy"]["p_good_direction"] * len(family_rows),
        )
        if row["accuracy"] == 1.0 and row["bonferroni_p_balanced_accuracy"] <= 0.01 and row["leave_one_out"]["accuracy"] >= 7 / 9:
            row["verdict"] = "candidate_exception_context_rule"
        elif row["bonferroni_p_balanced_accuracy"] <= 0.05 and row["leave_one_out"]["accuracy"] >= 6 / 9:
            row["verdict"] = "weak_exception_context_hint"
        else:
            row["verdict"] = "rejected_control"
    return {
        "family_rows": family_rows,
        "top_rules_by_family": {
            family: rows[:10]
            for family, rows in top_rules_by_family.items()
        },
        "feature_families": families,
    }


def compact_orbit_rows(orbit_rows: list[dict[str, Any]], top_feature_ids: list[str]) -> list[dict[str, Any]]:
    rows = []
    for row in orbit_rows:
        rows.append(
            {
                "orbit": row["orbit"],
                "pairs": row["pairs"],
                "six_side_pair": row["six_side_pair"],
                "nine_side_pair": row["nine_side_pair"],
                "is_mixed": row["is_mixed"],
                "display_symbols": row["display_symbols"],
                "feature_slice": {
                    feature: row["features"][feature]
                    for feature in top_feature_ids
                    if feature in row["features"]
                },
            }
        )
    return rows


def verdict(family_rows: list[dict[str, Any]]) -> str:
    best = family_rows[0]
    if best["verdict"] == "candidate_exception_context_rule":
        return "candidate_exception_context_rule_not_translation"
    if best["verdict"] == "weak_exception_context_hint":
        return "weak_exception_context_hint_not_promoted"
    return "rejected_control_no_auditable_exception_pattern"


def write_report(result: dict[str, Any]) -> None:
    lines = [
        "# Digit-Orbit Exception Context Search",
        "",
        "Generated by `digit_orbit_exception_context_search.py`.",
        "",
        "This pass tests whether the four mixed `6 <-> 9` quotient orbits have",
        "an auditable mechanical pattern against the five uniform non-singleton",
        "orbits. Features are restricted to already-derived usage counts, raw",
        "token-neighbourhood context, and tape-placement signals. It does not",
        "assign plaintext.",
        "",
        "## Target Orbits",
        "",
        "| Class | Orbits |",
        "|---|---|",
        f"| mixed | `{', '.join('/'.join(row['pairs']) for row in result['target_orbits'] if row['is_mixed'])}` |",
        f"| uniform | `{', '.join('/'.join(row['pairs']) for row in result['target_orbits'] if not row['is_mixed'])}` |",
        "",
        "## Controlled Rule Search",
        "",
        "| Feature family | Best predicate | Balanced acc. | Accuracy | F1 | LOOCV | Exact-control p | Bonferroni p | Verdict |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["family_rows"]:
        ctl = row["controls"]["balanced_accuracy"]
        lines.append(
            f"| `{row['family']}` | `{row['predicate']['id']}` | {row['balanced_accuracy']:.3f} | "
            f"{row['accuracy']:.3f} | {row['f1']:.3f} | {row['leave_one_out']['accuracy']:.3f} | "
            f"{ctl['p_good_direction']:.5f} | {row['bonferroni_p_balanced_accuracy']:.5f} | `{row['verdict']}` |"
        )
    best = result["best"]
    lines += [
        "",
        "## Best Auditable Pattern",
        "",
        f"- Family: `{best['family']}`.",
        f"- Predicate: `{best['predicate']['id']}`.",
        f"- Positive side selected by predicate: `{', '.join('/'.join(item['pairs']) for item in best['positive_orbits'])}`.",
        f"- Confusion matrix: TP `{best['tp']}`, FP `{best['fp']}`, TN `{best['tn']}`, FN `{best['fn']}`.",
        f"- Exhaustive 4-of-9 label-shuffle control p: `{best['controls']['balanced_accuracy']['p_good_direction']:.5f}` for balanced accuracy.",
        f"- Leave-one-out accuracy: `{best['leave_one_out']['correct']}/{best['leave_one_out']['total']}`.",
        "",
        "## Orbit Feature Slice",
        "",
        "| Orbit | Class | Symbols | Feature slice |",
        "|---|---|---|---|",
    ]
    feature_slice_ids = result["feature_slice_ids"]
    for row in result["orbit_feature_slice"]:
        cls = "mixed" if row["is_mixed"] else "uniform"
        symbols = ", ".join(f"{pair}:{symbol}" for pair, symbol in row["display_symbols"].items())
        features = ", ".join(
            f"{feature}={row['feature_slice'][feature]:.6g}"
            for feature in feature_slice_ids
            if feature in row["feature_slice"]
        )
        lines.append(f"| `{'/'.join(row['pairs'])}` | `{cls}` | `{symbols}` | `{features}` |")
    lines += [
        "",
        "## Verdict",
        "",
    ]
    if result["verdict"].startswith("candidate"):
        lines.append(
            "The mixed orbits are separable by the controlled context/tape rule, but this remains a mechanical exception rule only."
        )
    elif result["verdict"].startswith("weak"):
        lines.append(
            "The best rule is suggestive after controls, but the sample is only nine orbits and leave-one-out stability is not strong enough for promotion."
        )
    else:
        lines.append(
            "No context/usage/tape rule earns promotion. The four mixed `6 <-> 9` orbits remain explicit exceptions to the quotient, not an explained layer."
        )
    lines += [
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    mechanical = load_json(MECHANICAL_JSON)
    quotient = load_json(QUOTIENT_JSON)
    tape_formula = load_json(TAPE_FORMULA_JSON)

    pairs = all_pairs()
    contexts, context_counts = context_search.build_context_counters(pairs)
    context_matrices = context_search.distance_matrices(pairs, contexts)
    pair_index = {pair: index for index, pair in enumerate(pairs)}
    pair_rows = pair_feature_rows(mechanical, tape_formula, contexts, context_counts)
    target_orbits = load_target_orbits(quotient, mechanical["pair_table"])
    orbit_rows = [
        orbit_feature_row(orbit, pair_rows, pair_index, context_matrices, contexts)
        for orbit in target_orbits
    ]

    evaluation = evaluate_families(orbit_rows)
    family_rows = evaluation["family_rows"]
    best = family_rows[0]
    feature_slice_ids = sorted(
        {
            best["predicate"]["feature"],
            "context_pair_window_jsd",
            "usage_total_abs_delta",
            "outside_tokens_abs_delta",
            "boundary_cross_tokens_sum",
            "component_jaccard",
            "tape_fraction_pct_abs_delta",
        }
    )
    result = {
        "schema": "digit_orbit_exception_context_results.v1",
        "translation_delta": "NONE",
        "source_files": {
            "mechanical_formula": str(MECHANICAL_JSON.relative_to(ROOT)),
            "digit_orbit_quotient": str(QUOTIENT_JSON.relative_to(ROOT)),
            "tape_formula": str(TAPE_FORMULA_JSON.relative_to(ROOT)),
            "context_source": str(context_search.OCC_STREAMS.relative_to(ROOT)),
        },
        "target_orbits": [
            {
                "orbit": row["orbit"],
                "pairs": row["pairs"],
                "six_side_pair": row["six_side_pair"],
                "nine_side_pair": row["nine_side_pair"],
                "is_mixed": row["is_mixed"],
                "display_symbols": row["display_symbols"],
                "label_counts": row["label_counts"],
            }
            for row in orbit_rows
        ],
        "family_rows": family_rows,
        "best": best,
        "top_rules_by_family": evaluation["top_rules_by_family"],
        "feature_family_sizes": {
            family: len(features)
            for family, features in evaluation["feature_families"].items()
        },
        "feature_slice_ids": feature_slice_ids,
        "orbit_feature_slice": compact_orbit_rows(orbit_rows, feature_slice_ids),
        "orbit_rows_full": orbit_rows,
        "verdict": verdict(family_rows),
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(
        "verdict={verdict} best={family} predicate={predicate} "
        "balanced_accuracy={ba:.3f} p={p:.5f} loocv={loocv:.3f}".format(
            verdict=result["verdict"],
            family=best["family"],
            predicate=best["predicate"]["id"],
            ba=best["balanced_accuracy"],
            p=best["controls"]["balanced_accuracy"]["p_good_direction"],
            loocv=best["leave_one_out"]["accuracy"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
