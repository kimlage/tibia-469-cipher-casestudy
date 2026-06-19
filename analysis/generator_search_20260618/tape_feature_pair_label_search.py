#!/usr/bin/env python3
"""Pair-label search using tape/literal features.

The reusable tape layer explains much of the book assembly. This pass asks if
the remaining unsolved pair-table placement becomes easier to explain when each
pair cell is described by tape/literal usage features rather than only matrix
coordinates.

Mechanical only. No plaintext is promoted.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import tape_tokenization_analysis as tape_tokens


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TAPE_FORMULA_JSON = HERE / "tape_based_formula_469.json"

OUT_JSON = HERE / "tape_feature_pair_label_results.json"
OUT_MD = HERE / "tape_feature_pair_label_report.md"

RANDOM_SEED = 46920260624
CONTROL_TRIALS = 3000


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


def grid_features(pair: str) -> dict[str, int | bool]:
    x, y = int(pair[0]), int(pair[1])
    return {
        "x": x,
        "y": y,
        "sum": x + y,
        "diff": y - x,
        "product": x * y,
        "triangular_index": y * (y + 1) // 2 + x,
        "numeric_pair": int(pair),
        "diagonal": x == y,
        "has_zero": x == 0 or y == 0,
        "has_one": x == 1 or y == 1,
        "has_nine": x == 9 or y == 9,
        "same_parity": x % 2 == y % 2,
        "sum_mod2": (x + y) % 2,
        "sum_mod3": (x + y) % 3,
        "diff_mod2": (y - x) % 2,
        "diff_mod3": (y - x) % 3,
        "center_distance_x2": int(2 * (abs(x - 4.5) + abs(y - 4.5))),
    }


def project(formula: dict) -> list[dict]:
    books, segment_maps = tape_tokens.reconstruct_books(formula)
    token_maps = tape_tokens.align_tokens(books)
    return tape_tokens.project_tokens(token_maps, segment_maps)


def tape_features_by_pair(formula: dict, projected: list[dict]) -> dict[str, dict[str, Any]]:
    component_order = {row["id"]: index for index, row in enumerate(formula["tape_components"])}
    rows_by_pair: dict[str, list[dict]] = defaultdict(list)
    for row in projected:
        rows_by_pair[row["pair_key"]].append(row)

    features = {}
    for pair in all_pairs():
        rows = rows_by_pair[pair]
        tape = [row for row in rows if row["mapped_to_tape"]]
        outside = [row for row in rows if not row["mapped_to_tape"]]
        literal_only = [row for row in outside if row.get("unmapped_reason") == "literal_only"]
        boundary = [row for row in outside if row.get("unmapped_reason") == "crosses_recipe_segment_boundary"]
        components = sorted({row["component_id"] for row in tape}, key=lambda cid: component_order[cid])
        first_key = None
        for row in tape:
            key = (component_order[row["component_id"]], row["component_start"], row["component_end"], int(row["book"]), row["token_index"])
            if first_key is None or key < first_key:
                first_key = key
        features[pair] = {
            "total_tokens": len(rows),
            "tape_tokens": len(tape),
            "outside_tokens": len(outside),
            "literal_only_tokens": len(literal_only),
            "boundary_cross_tokens": len(boundary),
            "tape_fraction_pct": round(100 * len(tape) / len(rows)) if rows else 0,
            "outside_fraction_pct": round(100 * len(outside) / len(rows)) if rows else 0,
            "unique_components": len(components),
            "first_component": first_key[0] if first_key is not None else 99,
            "first_component_start_bin": (first_key[1] // 25) if first_key is not None else 99,
            "first_tape_position": first_key[1] if first_key is not None else 9999,
            "only_outside": bool(rows and not tape),
            "tape_only": bool(tape and not outside),
            "mixed_tape_literal": bool(tape and outside),
            "omitted_zero_tape": sum(1 for row in tape if row["omitted_zero"]),
            "omitted_zero_outside": sum(1 for row in outside if row["omitted_zero"]),
        }
        for idx in range(len(formula["tape_components"])):
            features[pair][f"in_component_{idx:02d}"] = any(component_order[row["component_id"]] == idx for row in tape)
    return features


def build_predicates(features: dict[str, dict[str, Any]], feature_names: list[str]) -> list[dict[str, Any]]:
    predicates = []
    for feature in feature_names:
        values = sorted({features[pair][feature] for pair in features}, key=lambda value: (str(type(value)), value))
        if all(isinstance(value, bool) for value in values):
            predicates.append({"id": f"{feature}==True", "feature": feature, "op": "==", "value": True})
        elif all(isinstance(value, int) for value in values):
            for value in values[:-1]:
                predicates.append({"id": f"{feature}<={value}", "feature": feature, "op": "<=", "value": value})
        else:
            for value in values:
                predicates.append({"id": f"{feature}=={value}", "feature": feature, "op": "==", "value": value})
    return predicates


def predicate_value(predicate: dict[str, Any], row: dict[str, Any]) -> bool:
    value = row[predicate["feature"]]
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
    return len(pairs) - Counter(labels[pair] for pair in pairs).most_common(1)[0][1]


def fit_tree(
    pairs: list[str],
    labels: dict[str, str],
    features: dict[str, dict[str, Any]],
    predicates: list[dict[str, Any]],
    depth: int,
) -> dict[str, Any]:
    prediction = majority_label(pairs, labels)
    base_error = leaf_error(pairs, labels)
    if depth == 0 or base_error == 0 or len(pairs) <= 2:
        return {"kind": "leaf", "prediction": prediction, "pairs": len(pairs), "error": base_error}
    best = None
    for predicate in predicates:
        left = [pair for pair in pairs if predicate_value(predicate, features[pair])]
        if not left or len(left) == len(pairs):
            continue
        left_set = set(left)
        right = [pair for pair in pairs if pair not in left_set]
        error = leaf_error(left, labels) + leaf_error(right, labels)
        balance = min(len(left), len(right))
        row = {"predicate": predicate, "left": left, "right": right, "error": error, "balance": balance}
        if best is None or (error, -balance, predicate["id"]) < (best["error"], -best["balance"], best["predicate"]["id"]):
            best = row
    if best is None or best["error"] >= base_error:
        return {"kind": "leaf", "prediction": prediction, "pairs": len(pairs), "error": base_error}
    left_tree = fit_tree(best["left"], labels, features, predicates, depth - 1)
    right_tree = fit_tree(best["right"], labels, features, predicates, depth - 1)
    return {
        "kind": "split",
        "predicate": best["predicate"],
        "pairs": len(pairs),
        "left": left_tree,
        "right": right_tree,
    }


def predict(tree: dict[str, Any], pair: str, features: dict[str, dict[str, Any]]) -> str:
    node = tree
    while node["kind"] == "split":
        node = node["left"] if predicate_value(node["predicate"], features[pair]) else node["right"]
    return node["prediction"]


def tree_depth(tree: dict[str, Any]) -> int:
    if tree["kind"] == "leaf":
        return 0
    return 1 + max(tree_depth(tree["left"]), tree_depth(tree["right"]))


def leaf_count(tree: dict[str, Any]) -> int:
    if tree["kind"] == "leaf":
        return 1
    return leaf_count(tree["left"]) + leaf_count(tree["right"])


def tree_rules(tree: dict[str, Any], prefix: list[str] | None = None) -> list[str]:
    prefix = prefix or []
    if tree["kind"] == "leaf":
        condition = " AND ".join(prefix) if prefix else "TRUE"
        return [f"{condition} => {tree['prediction']} ({tree['pairs']} cells, {tree['error']} err)"]
    display = tree["predicate"]["id"]
    return tree_rules(tree["left"], prefix + [display]) + tree_rules(tree["right"], prefix + [f"NOT {display}"])


def score_tree(tree: dict[str, Any], pairs: list[str], labels: dict[str, str], features: dict[str, dict[str, Any]]) -> dict[str, Any]:
    correct = sum(1 for pair in pairs if predict(tree, pair, features) == labels[pair])
    return {
        "correct": correct,
        "total": len(pairs),
        "accuracy": correct / len(pairs),
        "errors": len(pairs) - correct,
        "depth": tree_depth(tree),
        "leaf_count": leaf_count(tree),
    }


def stump_score(predicate: dict[str, Any], pairs: list[str], labels: dict[str, str], features: dict[str, dict[str, Any]]) -> dict[str, Any]:
    left = [pair for pair in pairs if predicate_value(predicate, features[pair])]
    left_set = set(left)
    right = [pair for pair in pairs if pair not in left_set]
    if not left or not right:
        return {"accuracy": 0.0, "correct": 0, "errors": len(pairs), "leaf_count": 1, "rules": []}
    left_label = majority_label(left, labels)
    right_label = majority_label(right, labels)
    correct = sum(labels[pair] == left_label for pair in left) + sum(labels[pair] == right_label for pair in right)
    return {
        "correct": correct,
        "total": len(pairs),
        "accuracy": correct / len(pairs),
        "errors": len(pairs) - correct,
        "leaf_count": 2,
        "rules": [
            f"{predicate['id']} => {left_label} ({len(left)} cells, {leaf_error(left, labels)} err)",
            f"NOT {predicate['id']} => {right_label} ({len(right)} cells, {leaf_error(right, labels)} err)",
        ],
        "predicate": predicate,
    }


def run_search(feature_set_id: str, feature_names: list[str], pairs: list[str], labels: dict[str, str], features: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    predicates = build_predicates(features, feature_names)
    baseline_label = majority_label(pairs, labels)
    baseline_correct = sum(labels[pair] == baseline_label for pair in pairs)
    rows = [
        {
            "feature_set": feature_set_id,
            "rule_class": "global_majority",
            "accuracy": baseline_correct / len(pairs),
            "correct": baseline_correct,
            "total": len(pairs),
            "errors": len(pairs) - baseline_correct,
            "leaf_count": 1,
            "rules": [f"TRUE => {baseline_label} ({len(pairs)} cells, {len(pairs) - baseline_correct} err)"],
        }
    ]
    for predicate in predicates:
        row = stump_score(predicate, pairs, labels, features)
        row.update({"feature_set": feature_set_id, "rule_class": "stump"})
        rows.append(row)
    rows.sort(key=lambda row: (-row["accuracy"], row["leaf_count"], row["rules"][0] if row["rules"] else ""))
    return rows[:10]


def controls(feature_sets: dict[str, list[str]], pairs: list[str], labels: dict[str, str], features: dict[str, dict[str, Any]], observed_rows: list[dict[str, Any]]) -> dict:
    rng = random.Random(RANDOM_SEED)
    symbols = [labels[pair] for pair in pairs]
    observed_best_by_set = {}
    for row in observed_rows:
        key = row["feature_set"]
        if key not in observed_best_by_set or row["accuracy"] > observed_best_by_set[key]:
            observed_best_by_set[key] = row["accuracy"]
    control_values = {feature_set: [] for feature_set in feature_sets}
    for _trial in range(CONTROL_TRIALS):
        shuffled = symbols[:]
        rng.shuffle(shuffled)
        shuffled_labels = dict(zip(pairs, shuffled))
        for feature_set, names in feature_sets.items():
            best = max(row["accuracy"] for row in run_search(feature_set, names, pairs, shuffled_labels, features))
            control_values[feature_set].append(best)
    out = {}
    for feature_set, values in control_values.items():
        observed = observed_best_by_set[feature_set]
        mean = sum(values) / len(values)
        sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        out[feature_set] = {
            "observed": observed,
            "control_mean": mean,
            "control_sd": sd,
            "p_good_direction": p,
            "control_min": min(values),
            "control_max": max(values),
        }
    return out


def write_report(result: dict) -> None:
    lines = [
        "# Tape Feature Pair-Label Search",
        "",
        "Generated by `tape_feature_pair_label_search.py`.",
        "",
        "This pass tests whether tape/literal usage features explain the exact",
        "symbol placement over the 55 unordered pair cells. It does not translate",
        "469.",
        "",
        "## Best Rows",
        "",
        "| Feature set | Rule | Accuracy | Leaves | Control mean | p | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    controls_by_set = result["controls"]
    for row in result["rows"][:12]:
        ctl = controls_by_set[row["feature_set"]]
        verdict = "candidate" if row["feature_set"] == result["best"]["feature_set"] and result["verdict"].startswith("candidate") else "rejected_control"
        lines.append(
            f"| `{row['feature_set']}` | `{row['rule_class']}` | {row['accuracy']:.3f} | {row['leaf_count']} | "
            f"{ctl['control_mean']:.3f} | {ctl['p_good_direction']:.5f} | `{verdict}` |"
        )
    lines += [
        "",
        "## Best Rules",
        "",
    ]
    for rule in result["best"]["rules"][:16]:
        lines.append(f"- `{rule}`")
    lines += ["", "## Verdict", ""]
    if result["verdict"] == "candidate_tape_feature_pair_label_formula":
        lines.append(
            "Tape/literal features explain pair-label placement better than inventory-preserving "
            "controls. Treat as a mechanical candidate only."
        )
    else:
        lines.append(
            "Tape/literal usage features do not explain exact pair-label placement better than "
            "symbol-inventory-preserving controls. The tape layer explains book assembly, not the "
            "original pair-table cell assignment."
        )
    lines += ["", f"Translation delta: `{result['translation_delta']}`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(TAPE_FORMULA_JSON)
    projected = project(formula)
    tape_features = tape_features_by_pair(formula, projected)
    features = {pair: {**tape_features[pair], **grid_features(pair)} for pair in all_pairs()}
    labels = {pair: primary_pair_symbol(formula["pair_table"], pair) for pair in all_pairs()}
    pairs = all_pairs()
    tape_feature_names = sorted(next(iter(tape_features.values())).keys())
    grid_feature_names = sorted(grid_features("00").keys())
    feature_sets = {
        "tape_only": tape_feature_names,
        "tape_plus_grid": tape_feature_names + grid_feature_names,
    }
    rows = []
    for feature_set, names in feature_sets.items():
        rows.extend(run_search(feature_set, names, pairs, labels, features))
    ctl = controls(feature_sets, pairs, labels, features, rows)
    rows.sort(key=lambda row: (-row["accuracy"], row["leaf_count"], row["rule_class"], row["feature_set"]))
    best = rows[0]
    best_p = ctl[best["feature_set"]]["p_good_direction"]
    verdict = "candidate_tape_feature_pair_label_formula" if best_p <= 0.01 else "rejected_control"
    result = {
        "schema": "tape_feature_pair_label_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "rows": rows,
        "best": best,
        "controls": ctl,
        "feature_sets": feature_sets,
        "verdict": verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} best={best['feature_set']} rule={best['rule_class']} "
        f"accuracy={best['accuracy']:.3f} p={best_p:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
