#!/usr/bin/env python3
"""Shared utilities for eye/blink arity probes.

These probes test mechanism-origin hypotheses only. They never assign
plaintext, word meanings, or CipSoft-attested semantic claims.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from itertools import combinations, permutations
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
DIGITS = "0123456789"
RANDOM_SEED = 46920260619
TRIALS = 50

E_CELLS = {"11", "15", "33", "44", "47", "48", "57", "58", "66", "78", "99"}
ANOMALY_CELLS = ["19", "39", "33", "66", "06", "09", "69", "99"]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def unordered_pair(code: str) -> str:
    return "".join(sorted(code))


def pair_cells() -> list[str]:
    return [f"{a}{b}" for a in range(10) for b in range(a, 10)]


def load_pair_labels() -> dict[str, str]:
    formula = load_json(FORMULA_JSON)
    out = {}
    for cell, row in formula["pair_table"].items():
        out[cell] = "+".join(sorted(row["symbols"]))
    return out


CELLS = pair_cells()
LOOKUP_SYMBOLS = sorted(set(load_pair_labels().values())) if FORMULA_JSON.exists() else []


def entropy_lookup_bits(labels: dict[str, str]) -> float:
    counts = Counter(labels.values())
    n = sum(counts.values())
    if n == 0:
        return 0.0
    return -sum(count * math.log2(count / n) for count in counts.values())


def rule_predict_labels(labels: dict[str, str], features: dict[str, str]) -> dict[str, Any]:
    by_feature: dict[str, list[str]] = defaultdict(list)
    for cell in CELLS:
        by_feature[features[cell]].append(labels[cell])

    majority = {}
    hits = 0
    exceptions = []
    for feature, rows in by_feature.items():
        winner, _ = Counter(rows).most_common(1)[0]
        majority[feature] = winner
    for cell in CELLS:
        predicted = majority[features[cell]]
        if predicted == labels[cell]:
            hits += 1
        else:
            exceptions.append({"cell": cell, "feature": features[cell], "actual": labels[cell], "predicted": predicted})
    return {
        "hits": hits,
        "accuracy": hits / len(CELLS),
        "feature_majority_labels": majority,
        "exceptions": exceptions,
    }


def binary_score(targets: set[str], selected: set[str]) -> dict[str, Any]:
    tp = len(targets & selected)
    fp = len(selected - targets)
    fn = len(targets - selected)
    tn = len(set(CELLS) - targets - selected)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "selected": sorted(selected),
    }


def best_binary_feature_rule(targets: set[str], features: dict[str, str]) -> dict[str, Any]:
    values = sorted(set(features.values()))
    best: dict[str, Any] | None = None
    for mask in range(1, 1 << len(values)):
        selected_values = {values[idx] for idx in range(len(values)) if mask & (1 << idx)}
        selected = {cell for cell, feature in features.items() if feature in selected_values}
        score = binary_score(targets, selected)
        score["selected_feature_values"] = sorted(selected_values)
        # Primary key: F1; secondary: fewer false positives; tertiary: smaller rule.
        key = (score["f1"], -score["fp"], -len(selected_values), score["tp"])
        if best is None or key > best["_key"]:
            score["_key"] = key
            best = score
    assert best is not None
    best.pop("_key", None)
    return best


def rough_rule_bits(label_result: dict[str, Any], feature_count: int, mapping_bits: float) -> dict[str, float]:
    labels = LOOKUP_SYMBOLS or ["?"]
    label_bits = math.log2(max(2, len(labels)))
    lookup_bits = 55 * label_bits
    rule_bits = feature_count * label_bits
    exception_bits = len(label_result["exceptions"]) * (math.log2(55) + label_bits)
    total = mapping_bits + rule_bits + exception_bits
    return {
        "lookup_bits": lookup_bits,
        "mapping_bits": mapping_bits,
        "rule_bits": rule_bits,
        "exception_bits": exception_bits,
        "total_bits": total,
        "gain_vs_lookup": lookup_bits - total,
    }


def rough_binary_bits(score: dict[str, Any], feature_count: int, mapping_bits: float) -> dict[str, float]:
    # A binary rule stores selected feature values plus explicit error cells.
    lookup_bits = 55.0
    selected_bits = feature_count
    error_count = score["fp"] + score["fn"]
    exception_bits = error_count * (math.log2(55) + 1)
    total = mapping_bits + selected_bits + exception_bits
    return {
        "lookup_bits": lookup_bits,
        "mapping_bits": mapping_bits,
        "rule_bits": selected_bits,
        "exception_bits": exception_bits,
        "total_bits": total,
        "gain_vs_lookup": lookup_bits - total,
    }


def shuffle_labels(labels: dict[str, str], rng: random.Random) -> dict[str, str]:
    values = list(labels.values())
    rng.shuffle(values)
    return dict(zip(CELLS, values, strict=True))


def shuffle_targets(targets: set[str], rng: random.Random) -> set[str]:
    cells = list(CELLS)
    rng.shuffle(cells)
    return set(cells[: len(targets)])


def control_pvalue(observed: float, controls: list[float]) -> float:
    return (1 + sum(value >= observed for value in controls)) / (len(controls) + 1)


def evaluate_family(
    labels: dict[str, str],
    feature_rows: list[dict[str, Any]],
    mapping_bits: float,
    family_name: str,
    trials: int = TRIALS,
    control_rows_limit: int = 2000,
) -> dict[str, Any]:
    best_label: dict[str, Any] | None = None
    best_e: dict[str, Any] | None = None

    for row in feature_rows:
        label_result = rule_predict_labels(labels, row["features"])
        label_bits = rough_rule_bits(label_result, row["feature_count"], mapping_bits)
        label_eval = {**row["meta"], **label_result, "mdl": label_bits}
        label_key = (label_bits["gain_vs_lookup"], label_result["hits"])
        if best_label is None or label_key > best_label["_key"]:
            label_eval["_key"] = label_key
            best_label = label_eval

        e_result = best_binary_feature_rule(E_CELLS, row["features"])
        e_bits = rough_binary_bits(e_result, row["feature_count"], mapping_bits)
        e_eval = {**row["meta"], **e_result, "mdl": e_bits}
        e_key = (e_result["f1"], e_bits["gain_vs_lookup"], -e_result["fp"])
        if best_e is None or e_key > best_e["_key"]:
            e_eval["_key"] = e_key
            best_e = e_eval

    assert best_label and best_e
    best_label.pop("_key", None)
    best_e.pop("_key", None)

    rng = random.Random(RANDOM_SEED)
    if len(feature_rows) > control_rows_limit:
        control_rows = rng.sample(feature_rows, control_rows_limit)
        control_mode = "sampled_feature_rows"
    else:
        control_rows = feature_rows
        control_mode = "all_feature_rows"
    label_control_gains = []
    e_control_f1 = []
    e_control_gains = []
    for _ in range(trials):
        shuffled_labels = shuffle_labels(labels, rng)
        shuffled_targets = shuffle_targets(E_CELLS, rng)
        control_best_label_gain = -10**9
        control_best_e_f1 = -1.0
        control_best_e_gain = -10**9
        for row in control_rows:
            label_result = rule_predict_labels(shuffled_labels, row["features"])
            label_bits = rough_rule_bits(label_result, row["feature_count"], mapping_bits)
            control_best_label_gain = max(control_best_label_gain, label_bits["gain_vs_lookup"])

            e_result = best_binary_feature_rule(shuffled_targets, row["features"])
            e_bits = rough_binary_bits(e_result, row["feature_count"], mapping_bits)
            control_best_e_f1 = max(control_best_e_f1, e_result["f1"])
            control_best_e_gain = max(control_best_e_gain, e_bits["gain_vs_lookup"])
        label_control_gains.append(control_best_label_gain)
        e_control_f1.append(control_best_e_f1)
        e_control_gains.append(control_best_e_gain)

    return {
        "family": family_name,
        "feature_rows": len(feature_rows),
        "mapping_bits_charged": mapping_bits,
        "best_label_rule": best_label,
        "best_e_rule": best_e,
        "controls": {
            "trials": trials,
            "mode": control_mode,
            "feature_rows_per_trial": len(control_rows),
            "label_gain_p": control_pvalue(best_label["mdl"]["gain_vs_lookup"], label_control_gains),
            "label_gain_control_mean": sum(label_control_gains) / len(label_control_gains),
            "label_gain_control_max": max(label_control_gains),
            "e_f1_p": control_pvalue(best_e["f1"], e_control_f1),
            "e_f1_control_mean": sum(e_control_f1) / len(e_control_f1),
            "e_f1_control_max": max(e_control_f1),
            "e_gain_p": control_pvalue(best_e["mdl"]["gain_vs_lookup"], e_control_gains),
            "e_gain_control_mean": sum(e_control_gains) / len(e_control_gains),
            "e_gain_control_max": max(e_control_gains),
        },
    }


def edge_relation_features(digit_to_edge: dict[str, tuple[int, int]]) -> dict[str, str]:
    features = {}
    for cell in CELLS:
        if cell[0] == cell[1]:
            features[cell] = "same_edge"
            continue
        left = set(digit_to_edge[cell[0]])
        right = set(digit_to_edge[cell[1]])
        features[cell] = "adjacent_edges" if left & right else "disjoint_edges"
    return features


def k5_feature_rows() -> list[dict[str, Any]]:
    edges = list(combinations(range(5), 2))
    fixed_edge = edges[0]
    remaining_edges = [edge for edge in edges if edge != fixed_edge]
    remaining_digits = DIGITS[1:]
    seen = set()
    rows = []
    for perm in permutations(remaining_edges):
        mapping = {DIGITS[0]: fixed_edge}
        mapping.update(dict(zip(remaining_digits, perm, strict=True)))
        features = edge_relation_features(mapping)
        relation_bits = tuple(features[cell] for cell in CELLS)
        if relation_bits in seen:
            continue
        seen.add(relation_bits)
        relation_69 = features["69"]
        rows.append(
            {
                "features": features,
                "feature_count": 3,
                "meta": {
                    "digit_to_edge": {digit: list(edge) for digit, edge in mapping.items()},
                    "relation_6_9": relation_69,
                    "anomaly_relations": {
                        cell: relation_bits[CELLS.index(cell)] for cell in ANOMALY_CELLS if cell in CELLS
                    },
                },
            }
        )
    return rows


def perfect_matchings(items: tuple[str, ...]) -> list[list[tuple[str, str]]]:
    if not items:
        return [[]]
    first = items[0]
    out = []
    for idx in range(1, len(items)):
        second = items[idx]
        rest = items[1:idx] + items[idx + 1 :]
        for matching in perfect_matchings(rest):
            out.append([(first, second), *matching])
    return out


def state_5x2_feature_rows() -> list[dict[str, Any]]:
    seen = set()
    rows = []
    for matching in perfect_matchings(tuple(DIGITS)):
        # Assign the lower digit in the first eye to state 0; global state flip is redundant.
        for mask in range(1 << (len(matching) - 1)):
            mapping: dict[str, tuple[int, int]] = {}
            for eye, pair in enumerate(matching):
                left, right = pair
                if eye == 0:
                    left_state = 0
                else:
                    left_state = (mask >> (eye - 1)) & 1
                mapping[left] = (eye, left_state)
                mapping[right] = (eye, 1 - left_state)
            features = {}
            for cell in CELLS:
                left = mapping[cell[0]]
                right = mapping[cell[1]]
                if cell[0] == cell[1]:
                    feature = "same_token"
                elif left[0] == right[0]:
                    feature = "same_eye_opposite_state"
                elif left[1] == right[1]:
                    feature = "same_state_different_eye"
                else:
                    feature = "different_eye_different_state"
                features[cell] = feature
            bits = tuple(features[cell] for cell in CELLS)
            if bits in seen:
                continue
            seen.add(bits)
            rows.append(
                {
                    "features": features,
                    "feature_count": 4,
                    "meta": {
                        "digit_to_eye_state": {digit: list(token) for digit, token in mapping.items()},
                        "relation_6_9": features["69"],
                        "anomaly_relations": {cell: features[cell] for cell in ANOMALY_CELLS if cell in CELLS},
                    },
                }
            )
    return rows
