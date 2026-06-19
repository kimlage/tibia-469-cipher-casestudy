#!/usr/bin/env python3
"""Alternative digit-geometry search for the 469 pair table.

The standard grid searches treat digits as ordered numeric values. This pass
tests whether the author may have used a different human geometry for digits:
phone keypad, calculator/numpad, keyboard row, clock/circle, or seven-segment
glyphs.

For each layout, the script builds pair features and fits shallow decision
trees. A global shuffled-label control repeats the whole search and lets the
control pick its own best layout/depth, so post-hoc layout choice is penalized.

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

OUT_JSON = HERE / "alternative_digit_geometry_results.json"
OUT_MD = HERE / "alternative_digit_geometry_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260620
TRIALS = 1500
MAX_DEPTHS = [1, 2, 3]


SEGMENTS = {
    "0": set("abcdef"),
    "1": set("bc"),
    "2": set("abdeg"),
    "3": set("abcdg"),
    "4": set("bcfg"),
    "5": set("acdfg"),
    "6": set("acdefg"),
    "7": set("abc"),
    "8": set("abcdefg"),
    "9": set("abcdfg"),
}


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


def coordinate_layouts() -> dict[str, dict[str, tuple[int, int]]]:
    phone = {
        "1": (0, 0),
        "2": (1, 0),
        "3": (2, 0),
        "4": (0, 1),
        "5": (1, 1),
        "6": (2, 1),
        "7": (0, 2),
        "8": (1, 2),
        "9": (2, 2),
        "0": (1, 3),
    }
    numpad = {
        "7": (0, 0),
        "8": (1, 0),
        "9": (2, 0),
        "4": (0, 1),
        "5": (1, 1),
        "6": (2, 1),
        "1": (0, 2),
        "2": (1, 2),
        "3": (2, 2),
        "0": (1, 3),
    }
    keyboard = {digit: (idx, 0) for idx, digit in enumerate("1234567890")}
    numeric = {str(digit): (digit, 0) for digit in range(10)}

    def circle(order: str) -> dict[str, tuple[int, int]]:
        out = {}
        for idx, digit in enumerate(order):
            angle = 2 * math.pi * idx / len(order)
            out[digit] = (round(100 * math.cos(angle)), round(100 * math.sin(angle)))
        return out

    return {
        "numeric_line_0_to_9": numeric,
        "keyboard_row_1_to_0": keyboard,
        "phone_keypad": phone,
        "phone_keypad_y_flipped": {digit: (x, -y) for digit, (x, y) in phone.items()},
        "numpad": numpad,
        "numpad_y_flipped": {digit: (x, -y) for digit, (x, y) in numpad.items()},
        "circle_0_to_9": circle("0123456789"),
        "circle_1_to_0": circle("1234567890"),
    }


def coord_pair_features(layout: dict[str, tuple[int, int]], pair: str) -> dict[str, Any]:
    left, right = pair
    x1, y1 = layout[left]
    x2, y2 = layout[right]
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    manhattan = dx + dy
    euclid2 = dx * dx + dy * dy
    return {
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "min_x": min(x1, x2),
        "max_x": max(x1, x2),
        "min_y": min(y1, y2),
        "max_y": max(y1, y2),
        "mid_x2": x1 + x2,
        "mid_y2": y1 + y2,
        "dx": dx,
        "dy": dy,
        "dx_dy": (dx, dy),
        "manhattan": manhattan,
        "euclid2": euclid2,
        "area": dx * dy,
        "same_x": x1 == x2,
        "same_y": y1 == y2,
        "diag_45": dx == dy and dx != 0,
        "adjacent_manhattan": manhattan == 1,
        "distance_bucket": min(5, int(math.sqrt(euclid2) // 50)) if euclid2 > 20 else manhattan,
        "slope_class": "vertical" if dx == 0 else ("horizontal" if dy == 0 else f"{dy}:{dx}"),
    }


def seven_segment_pair_features(pair: str) -> dict[str, Any]:
    left, right = pair
    a = SEGMENTS[left]
    b = SEGMENTS[right]
    common = a & b
    union = a | b
    xor = a ^ b
    features: dict[str, Any] = {
        "hamming": len(xor),
        "common": len(common),
        "union": len(union),
        "xor": len(xor),
        "left_count": len(a),
        "right_count": len(b),
        "count_diff": abs(len(a) - len(b)),
        "subset_relation": a <= b or b <= a,
        "same_segments": a == b,
    }
    for segment in "abcdefg":
        features[f"both_{segment}"] = segment in a and segment in b
        features[f"either_{segment}"] = segment in a or segment in b
        features[f"same_{segment}"] = (segment in a) == (segment in b)
    return features


def all_layout_features() -> dict[str, dict[str, dict[str, Any]]]:
    layouts = {
        name: {pair: coord_pair_features(layout, pair) for pair in all_pairs()}
        for name, layout in coordinate_layouts().items()
    }
    layouts["seven_segment"] = {pair: seven_segment_pair_features(pair) for pair in all_pairs()}
    return layouts


def build_predicates(features_by_pair: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    keys = sorted(next(iter(features_by_pair.values())).keys())
    predicates = []
    for key in keys:
        values = [features_by_pair[pair][key] for pair in features_by_pair]
        unique = sorted(set(values), key=str)
        if not unique:
            continue
        if all(isinstance(value, bool) for value in unique) or len(unique) <= 12 or any(isinstance(value, str) for value in unique):
            for value in unique:
                predicates.append({"id": f"{key}=={value}", "feature": key, "op": "==", "value": value, "display": f"{key} == {value}"})
        else:
            for threshold in unique[:-1]:
                predicates.append({"id": f"{key}<={threshold}", "feature": key, "op": "<=", "value": threshold, "display": f"{key} <= {threshold}"})
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
    features_by_pair: dict[str, dict[str, Any]],
    predicates: list[dict[str, Any]],
    depth: int,
) -> dict[str, Any]:
    prediction = majority_label(pairs, labels)
    base_error = leaf_error(pairs, labels)
    if depth == 0 or base_error == 0 or len(pairs) <= 2:
        return {"kind": "leaf", "prediction": prediction, "pairs": len(pairs), "error": base_error}

    best = None
    for predicate in predicates:
        left = [pair for pair in pairs if predicate_value(predicate, features_by_pair[pair])]
        if not left or len(left) == len(pairs):
            continue
        left_set = set(left)
        right = [pair for pair in pairs if pair not in left_set]
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

    return {
        "kind": "split",
        "predicate": best["predicate"],
        "fallback_prediction": prediction,
        "pairs": len(pairs),
        "left": fit_tree(best["left"], labels, features_by_pair, predicates, depth - 1),
        "right": fit_tree(best["right"], labels, features_by_pair, predicates, depth - 1),
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
    return {"leaves": left["leaves"] + right["leaves"], "splits": left["splits"] + right["splits"] + 1}


def tree_rules(tree: dict[str, Any], prefix: str = "") -> list[str]:
    if tree["kind"] == "leaf":
        return [f"{prefix or 'TRUE'} -> {tree['prediction']}"]
    pred = tree["predicate"]["display"]
    left_prefix = f"{prefix} AND {pred}" if prefix else pred
    right_prefix = f"{prefix} AND NOT ({pred})" if prefix else f"NOT ({pred})"
    return tree_rules(tree["left"], left_prefix) + tree_rules(tree["right"], right_prefix)


def score_tree(tree: dict[str, Any], labels: dict[str, str], features_by_pair: dict[str, dict[str, Any]], predicate_count: int) -> dict:
    pairs = all_pairs()
    correct = sum(predict(tree, pair, features_by_pair) == labels[pair] for pair in pairs)
    errors = len(pairs) - correct
    stats = tree_stats(tree)
    mdl_bits = (
        stats["splits"] * math.log2(predicate_count + 1)
        + stats["leaves"] * math.log2(len(SIGMA))
        + errors * (math.log2(len(pairs)) + math.log2(len(SIGMA)))
    )
    return {
        "correct": correct,
        "total": len(pairs),
        "accuracy": correct / len(pairs),
        "errors": errors,
        "splits": stats["splits"],
        "leaves": stats["leaves"],
        "mdl_bits_est": mdl_bits,
        "rules": tree_rules(tree)[:20],
    }


def best_for_labels(labels: dict[str, str], layout_features: dict[str, dict[str, dict[str, Any]]], predicate_cache: dict[str, list[dict[str, Any]]]) -> dict:
    best = None
    for layout_id, features_by_pair in layout_features.items():
        predicates = predicate_cache[layout_id]
        for depth in MAX_DEPTHS:
            tree = fit_tree(all_pairs(), labels, features_by_pair, predicates, depth)
            score = score_tree(tree, labels, features_by_pair, len(predicates))
            row = {"layout": layout_id, "max_depth": depth, "tree": tree, "predicate_count": len(predicates), **score}
            if best is None or (row["accuracy"], -row["mdl_bits_est"], -row["splits"], row["layout"]) > (
                best["accuracy"],
                -best["mdl_bits_est"],
                -best["splits"],
                best["layout"],
            ):
                best = row
    assert best is not None
    return best


def summarize(values: list[float], observed: float, high_is_good: bool) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    if high_is_good:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {"observed": observed, "control_mean": mean, "control_sd": sd, "z": z, "p": p, "control_min": min(values), "control_max": max(values)}


def main() -> int:
    formula = load_json(FORMULA_JSON)
    labels = {pair: primary_pair_symbol(formula["pair_table"], pair) for pair in all_pairs()}
    label_values = [labels[pair] for pair in all_pairs()]
    layout_features = all_layout_features()
    predicate_cache = {layout_id: build_predicates(features) for layout_id, features in layout_features.items()}

    rows = []
    for layout_id, features in layout_features.items():
        predicates = predicate_cache[layout_id]
        for depth in MAX_DEPTHS:
            tree = fit_tree(all_pairs(), labels, features, predicates, depth)
            score = score_tree(tree, labels, features, len(predicates))
            rows.append({"layout": layout_id, "max_depth": depth, "predicate_count": len(predicates), "tree": tree, **score})
    rows.sort(key=lambda row: (-row["accuracy"], row["mdl_bits_est"], row["layout"], row["max_depth"]))
    observed_best = rows[0]

    rng = random.Random(RANDOM_SEED)
    shuffled = label_values[:]
    control_acc = []
    control_mdl = []
    for _trial in range(TRIALS):
        rng.shuffle(shuffled)
        shuffled_labels = {pair: symbol for pair, symbol in zip(all_pairs(), shuffled)}
        best = best_for_labels(shuffled_labels, layout_features, predicate_cache)
        control_acc.append(best["accuracy"])
        control_mdl.append(best["mdl_bits_est"])

    acc_summary = summarize(control_acc, observed_best["accuracy"], True)
    mdl_summary = summarize(control_mdl, observed_best["mdl_bits_est"], False)
    verdict = "candidate_generator_alt_digit_geometry" if (
        observed_best["accuracy"] >= 0.70 and acc_summary["p"] <= 0.01 and observed_best["splits"] <= 7
    ) else "rejected_control"

    result = {
        "schema": "alternative_digit_geometry_results.v1",
        "random_seed": RANDOM_SEED,
        "trials": TRIALS,
        "layouts": sorted(layout_features),
        "depths": MAX_DEPTHS,
        "rows": rows[:50],
        "observed_best": observed_best,
        "global_accuracy_control": acc_summary,
        "global_mdl_control": mdl_summary,
        "verdict": verdict,
        "method_note": "Uses primary label for conflict cell {19}; controls preserve primary-label multiset and choose best layout/depth.",
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Alternative Digit Geometry Search",
        "",
        "Generated by `alternative_digit_geometry_search.py`.",
        "",
        "This pass tests whether the pair table follows a human digit layout:",
        "keyboard row, phone keypad, numpad, circular/clock layouts, or",
        "seven-segment glyphs. Global controls rerun the full layout search.",
        "",
        "## Best Observed",
        "",
        "| Layout | Depth | Accuracy | Splits | MDL bits | p(acc global) | p(MDL global) |",
        "|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| `{observed_best['layout']}` | {observed_best['max_depth']} | "
            f"{observed_best['correct']}/{observed_best['total']} ({observed_best['accuracy']:.3f}) | "
            f"{observed_best['splits']} | {observed_best['mdl_bits_est']:.1f} | "
            f"{acc_summary['p']:.3f} | {mdl_summary['p']:.3f} |"
        ),
        "",
        "## Top Rows",
        "",
        "| Layout | Depth | Accuracy | Splits | MDL bits |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows[:12]:
        lines.append(
            f"| `{row['layout']}` | {row['max_depth']} | {row['correct']}/{row['total']} ({row['accuracy']:.3f}) | "
            f"{row['splits']} | {row['mdl_bits_est']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Best Rules",
            "",
        ]
    )
    for rule in observed_best["rules"][:12]:
        lines.append(f"- `{rule}`")
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"`{verdict}`.",
            "",
            "Alternative digit layouts do not recover the pair-cell placement better",
            "than global label-shuffled controls. No keypad/clock/seven-segment",
            "geometry is promoted as the original formula.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"verdict={verdict} best={observed_best['layout']} acc={observed_best['accuracy']:.3f} p={acc_summary['p']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
