#!/usr/bin/env python3
"""Decision-tree formula search for the 469 pair table.

Previous grid passes tested single features, modular arithmetic, traversals,
source strings, seeds, and usage-driven orders. This pass tests another
plausible human construction:

    a small set of matrix-region rules over x/y/sum/diff/product/diagonal.

Example shape: "if diff <= 2 then use this subrule, else if product > 30...".
The script fits shallow greedy decision trees and compares the real table
against label-shuffled controls that preserve the exact primary symbol
inventory. If the real table is not easier to fit than controls, this class of
piecewise grid formula is rejected.

Mechanical only. No plaintext or glossary is promoted.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "decision_tree_pair_formula_results.json"
OUT_MD = HERE / "decision_tree_pair_formula_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260620
TRIALS = 3000
MAX_DEPTHS = [1, 2, 3, 4]


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


def pair_features(pair: str) -> dict[str, int | bool]:
    x, y = int(pair[0]), int(pair[1])
    return {
        "x": x,
        "y": y,
        "sum": x + y,
        "diff": y - x,
        "product": x * y,
        "triangular_index": y * (y + 1) // 2 + x,
        "numeric_pair": 10 * x + y,
        "min_digit": x,
        "max_digit": y,
        "diagonal": x == y,
        "border": x in {0, 9} or y in {0, 9},
        "corner": (x, y) in {(0, 0), (0, 9), (9, 9)},
        "has_zero": x == 0 or y == 0,
        "has_one": x == 1 or y == 1,
        "has_nine": x == 9 or y == 9,
        "center_band": x in {4, 5} or y in {4, 5},
        "same_parity": x % 2 == y % 2,
        "sum_mod2": (x + y) % 2,
        "sum_mod3": (x + y) % 3,
        "sum_mod4": (x + y) % 4,
        "diff_mod2": (y - x) % 2,
        "diff_mod3": (y - x) % 3,
        "product_mod3": (x * y) % 3,
        "product_mod5": (x * y) % 5,
        "center_distance": abs(x - 4.5) + abs(y - 4.5),
        "anti_diagonal_distance": abs((x + y) - 9),
    }


def build_predicates(features_by_pair: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    numeric = [
        "x",
        "y",
        "sum",
        "diff",
        "product",
        "triangular_index",
        "numeric_pair",
        "center_distance",
        "anti_diagonal_distance",
    ]
    categorical = [
        "min_digit",
        "max_digit",
        "diagonal",
        "border",
        "corner",
        "has_zero",
        "has_one",
        "has_nine",
        "center_band",
        "same_parity",
        "sum_mod2",
        "sum_mod3",
        "sum_mod4",
        "diff_mod2",
        "diff_mod3",
        "product_mod3",
        "product_mod5",
    ]
    predicates = []
    for feature in numeric:
        values = sorted({features_by_pair[pair][feature] for pair in features_by_pair})
        for threshold in values[:-1]:
            predicates.append(
                {
                    "id": f"{feature}<={threshold}",
                    "feature": feature,
                    "op": "<=",
                    "value": threshold,
                    "display": f"{feature} <= {threshold}",
                }
            )
    for feature in categorical:
        values = sorted({features_by_pair[pair][feature] for pair in features_by_pair}, key=str)
        for value in values:
            predicates.append(
                {
                    "id": f"{feature}=={value}",
                    "feature": feature,
                    "op": "==",
                    "value": value,
                    "display": f"{feature} == {value}",
                }
            )
    return predicates


def predicate_value(predicate: dict[str, Any], feature_row: dict[str, Any]) -> bool:
    value = feature_row[predicate["feature"]]
    if predicate["op"] == "<=":
        return value <= predicate["value"]
    if predicate["op"] == "==":
        return value == predicate["value"]
    raise ValueError(predicate)


def majority_label(pairs: list[str], labels: dict[str, str]) -> str:
    return Counter(labels[pair] for pair in pairs).most_common(1)[0][0]


def leaf_error(pairs: list[str], labels: dict[str, str]) -> int:
    if not pairs:
        return 0
    count = Counter(labels[pair] for pair in pairs).most_common(1)[0][1]
    return len(pairs) - count


def fit_tree(
    pairs: list[str],
    labels: dict[str, str],
    features_by_pair: dict[str, dict[str, Any]],
    predicates: list[dict[str, Any]],
    depth: int,
    min_leaf: int = 1,
) -> dict[str, Any]:
    prediction = majority_label(pairs, labels)
    base_error = leaf_error(pairs, labels)
    if depth == 0 or base_error == 0 or len(pairs) <= 2 * min_leaf:
        return {"kind": "leaf", "prediction": prediction, "pairs": len(pairs), "error": base_error}

    best = None
    for predicate in predicates:
        left = [pair for pair in pairs if predicate_value(predicate, features_by_pair[pair])]
        left_set = set(left)
        right = [pair for pair in pairs if pair not in left_set]
        if len(left) < min_leaf or len(right) < min_leaf:
            continue
        error = leaf_error(left, labels) + leaf_error(right, labels)
        balance = min(len(left), len(right))
        row = {"predicate": predicate, "left": left, "right": right, "error": error, "balance": balance}
        if best is None or (row["error"], -row["balance"], row["predicate"]["id"]) < (
            best["error"],
            -best["balance"],
            best["predicate"]["id"],
        ):
            best = row

    if best is None or best["error"] >= base_error:
        return {"kind": "leaf", "prediction": prediction, "pairs": len(pairs), "error": base_error}

    left_tree = fit_tree(best["left"], labels, features_by_pair, predicates, depth - 1, min_leaf)
    right_tree = fit_tree(best["right"], labels, features_by_pair, predicates, depth - 1, min_leaf)
    return {
        "kind": "split",
        "predicate": best["predicate"],
        "fallback_prediction": prediction,
        "pairs": len(pairs),
        "left": left_tree,
        "right": right_tree,
    }


def predict(tree: dict[str, Any], pair: str, features_by_pair: dict[str, dict[str, Any]]) -> str:
    node = tree
    while node["kind"] == "split":
        node = node["left"] if predicate_value(node["predicate"], features_by_pair[pair]) else node["right"]
    return node["prediction"]


def tree_stats(tree: dict[str, Any]) -> dict[str, int]:
    if tree["kind"] == "leaf":
        return {"leaves": 1, "splits": 0}
    left = tree_stats(tree["left"])
    right = tree_stats(tree["right"])
    return {
        "leaves": left["leaves"] + right["leaves"],
        "splits": left["splits"] + right["splits"] + 1,
    }


def tree_rules(tree: dict[str, Any], prefix: str = "") -> list[str]:
    if tree["kind"] == "leaf":
        condition = prefix or "TRUE"
        return [f"{condition} -> {tree['prediction']}"]
    pred = tree["predicate"]["display"]
    left_prefix = f"{prefix} AND {pred}" if prefix else pred
    right_prefix = f"{prefix} AND NOT ({pred})" if prefix else f"NOT ({pred})"
    return tree_rules(tree["left"], left_prefix) + tree_rules(tree["right"], right_prefix)


def evaluate_tree(tree: dict[str, Any], pairs: list[str], labels: dict[str, str], features_by_pair: dict[str, dict[str, Any]], predicate_count: int) -> dict:
    predictions = {pair: predict(tree, pair, features_by_pair) for pair in pairs}
    correct = sum(predictions[pair] == labels[pair] for pair in pairs)
    errors = len(pairs) - correct
    stats = tree_stats(tree)
    mdl_bits = (
        stats["splits"] * math.log2(predicate_count + 1)
        + stats["leaves"] * math.log2(len(SIGMA))
        + errors * (math.log2(len(pairs)) + math.log2(len(SIGMA)))
    )
    return {
        "correct": correct,
        "errors": errors,
        "total": len(pairs),
        "accuracy": correct / len(pairs),
        "leaves": stats["leaves"],
        "splits": stats["splits"],
        "mdl_bits_est": mdl_bits,
        "rules": tree_rules(tree)[:20],
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


def fit_and_score(labels: dict[str, str], max_depth: int, pairs: list[str], features_by_pair: dict[str, dict[str, Any]], predicates: list[dict[str, Any]]) -> tuple[dict, dict]:
    tree = fit_tree(pairs, labels, features_by_pair, predicates, max_depth)
    score = evaluate_tree(tree, pairs, labels, features_by_pair, len(predicates))
    return tree, score


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    pairs = all_pairs()
    features_by_pair = {pair: pair_features(pair) for pair in pairs}
    predicates = build_predicates(features_by_pair)
    labels = {pair: primary_pair_symbol(pair_table, pair) for pair in pairs}
    label_values = [labels[pair] for pair in pairs]
    rng = random.Random(RANDOM_SEED)

    rows = []
    for max_depth in MAX_DEPTHS:
        tree, score = fit_and_score(labels, max_depth, pairs, features_by_pair, predicates)
        acc_controls = []
        mdl_controls = []
        shuffled = label_values[:]
        for _trial in range(TRIALS):
            rng.shuffle(shuffled)
            shuffled_labels = {pair: symbol for pair, symbol in zip(pairs, shuffled)}
            _ctrl_tree, ctrl_score = fit_and_score(shuffled_labels, max_depth, pairs, features_by_pair, predicates)
            acc_controls.append(ctrl_score["accuracy"])
            mdl_controls.append(ctrl_score["mdl_bits_est"])
        acc_summary = summarize(acc_controls, score["accuracy"], True)
        mdl_summary = summarize(mdl_controls, score["mdl_bits_est"], False)
        rows.append(
            {
                "max_depth": max_depth,
                "tree": tree,
                "score": score,
                "accuracy_control": acc_summary,
                "mdl_control": mdl_summary,
            }
        )

    best_by_accuracy = max(rows, key=lambda row: (row["score"]["accuracy"], -row["score"]["mdl_bits_est"]))
    best_by_mdl = min(rows, key=lambda row: (row["score"]["mdl_bits_est"], -row["score"]["accuracy"]))
    strongest = min(
        rows,
        key=lambda row: min(row["accuracy_control"]["p_good_direction"], row["mdl_control"]["p_good_direction"]),
    )
    strongest_p = min(strongest["accuracy_control"]["p_good_direction"], strongest["mdl_control"]["p_good_direction"])
    verdict = "candidate_generator_decision_tree" if (
        best_by_accuracy["score"]["accuracy"] >= 0.70
        and strongest_p <= 0.01
        and strongest["score"]["splits"] <= 8
    ) else "rejected_control"

    result = {
        "schema": "decision_tree_pair_formula_results.v1",
        "random_seed": RANDOM_SEED,
        "trials": TRIALS,
        "predicate_count": len(predicates),
        "method_note": "Uses primary label for conflict cell {19}; controls preserve primary-label multiset.",
        "rows": rows,
        "best_by_accuracy": {
            "max_depth": best_by_accuracy["max_depth"],
            **best_by_accuracy["score"],
            "accuracy_p": best_by_accuracy["accuracy_control"]["p_good_direction"],
            "mdl_p": best_by_accuracy["mdl_control"]["p_good_direction"],
        },
        "best_by_mdl": {
            "max_depth": best_by_mdl["max_depth"],
            **best_by_mdl["score"],
            "accuracy_p": best_by_mdl["accuracy_control"]["p_good_direction"],
            "mdl_p": best_by_mdl["mdl_control"]["p_good_direction"],
        },
        "strongest_control_row": {
            "max_depth": strongest["max_depth"],
            **strongest["score"],
            "accuracy_p": strongest["accuracy_control"]["p_good_direction"],
            "mdl_p": strongest["mdl_control"]["p_good_direction"],
        },
        "verdict": verdict,
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Decision-Tree Pair Formula Search",
        "",
        "Generated by `decision_tree_pair_formula_search.py`.",
        "",
        "This pass tests whether the 55 pair cells can be generated by a small",
        "piecewise matrix-region formula over x/y/sum/diff/product/diagonal style",
        "features. Controls preserve the exact primary symbol inventory.",
        "",
        "## Results",
        "",
        "| Max depth | Accuracy | Splits | Leaves | MDL bits | p(acc) | p(MDL) |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        score = row["score"]
        lines.append(
            f"| {row['max_depth']} | {score['correct']}/{score['total']} ({score['accuracy']:.3f}) | "
            f"{score['splits']} | {score['leaves']} | {score['mdl_bits_est']:.1f} | "
            f"{row['accuracy_control']['p_good_direction']:.3f} | {row['mdl_control']['p_good_direction']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Best Rules By Accuracy",
            "",
        ]
    )
    for rule in best_by_accuracy["score"]["rules"][:12]:
        lines.append(f"- `{rule}`")
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"`{verdict}`.",
            "",
            "Shallow piecewise region rules do not recover the pair table better than",
            "label-shuffled controls. This rejects a compact decision-tree formula as",
            "the currently observable original placement rule.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} best_acc={best_by_accuracy['score']['accuracy']:.3f} "
        f"p={best_by_accuracy['accuracy_control']['p_good_direction']:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
