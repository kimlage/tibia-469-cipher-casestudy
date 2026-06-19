#!/usr/bin/env python3
"""Endpoint-affinity assignment search for the 469 pair table.

This pass tests a remaining process hypothesis: after choosing the homophone
inventory, perhaps each symbol had preferences for digit endpoints, and the
55 cells were assigned by a compact score:

    score(symbol, {a,b}) = prior(symbol) + u_symbol[a] + u_symbol[b]
                         + small binary feature affinities

This is not a translation. It is a mechanical pair-label placement test. The
main evidence is leave-one-pair-out prediction and inventory-preserving label
shuffle controls. A high in-sample exact-inventory assignment alone is not
promotable because it can become a smooth lookup.
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

OUT_JSON = HERE / "endpoint_affinity_assignment_results.json"
OUT_MD = HERE / "endpoint_affinity_assignment_report.md"

SIGMA = tuple("*ABCEFILNORSTV")
RANDOM_SEED = 46920260620
CONTROL_TRIALS = 500
ALPHA = 0.75


try:
    from scipy.optimize import linear_sum_assignment
except Exception:  # pragma: no cover - fallback documented in results.
    linear_sum_assignment = None


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[str]:
    return [f"{a}{b}" for a in range(10) for b in range(a, 10)]


def primary_pair_symbol(pair_table: dict[str, Any], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def pair_features(pair: str) -> list[str]:
    a, b = int(pair[0]), int(pair[1])
    features = []
    if a == b:
        features.append("diag")
    if a == 0 or b == 0:
        features.append("contains_0")
    if a in {6, 9} or b in {6, 9}:
        features.append("contains_6_or_9")
    if abs(a - b) >= 6:
        features.append("wide_diff")
    if (a + b) % 2 == 0:
        features.append("even_sum")
    if a + b >= 12:
        features.append("high_sum")
    if a * b == 0:
        features.append("zero_product")
    return features


BINARY_FEATURES = sorted({feature for pair in natural_pairs() for feature in pair_features(pair)})


def train_model(pairs: list[str], labels: list[str], exclude_index: int | None = None) -> dict[str, Any]:
    symbol_counts = Counter()
    endpoint_counts = {symbol: Counter() for symbol in SIGMA}
    feature_counts = {symbol: Counter() for symbol in SIGMA}
    total_cells = 0
    for index, (pair, label) in enumerate(zip(pairs, labels)):
        if index == exclude_index:
            continue
        symbol_counts[label] += 1
        total_cells += 1
        endpoint_counts[label][pair[0]] += 1
        endpoint_counts[label][pair[1]] += 1
        for feature in pair_features(pair):
            feature_counts[label][feature] += 1
    return {
        "symbol_counts": symbol_counts,
        "endpoint_counts": endpoint_counts,
        "feature_counts": feature_counts,
        "total_cells": total_cells,
    }


def log_prob(count: float, total: float, classes: int) -> float:
    return math.log((count + ALPHA) / (total + ALPHA * classes))


def score_pair_symbol(pair: str, symbol: str, model: dict[str, Any], use_binary_features: bool) -> float:
    symbol_counts: Counter[str] = model["symbol_counts"]
    endpoint_counts: dict[str, Counter[str]] = model["endpoint_counts"]
    feature_counts: dict[str, Counter[str]] = model["feature_counts"]
    total_cells = model["total_cells"]
    score = log_prob(symbol_counts[symbol], total_cells, len(SIGMA))
    endpoint_total = 2 * symbol_counts[symbol]
    score += log_prob(endpoint_counts[symbol][pair[0]], endpoint_total, 10)
    score += log_prob(endpoint_counts[symbol][pair[1]], endpoint_total, 10)
    if use_binary_features:
        pair_feature_set = set(pair_features(pair))
        for feature in BINARY_FEATURES:
            count = feature_counts[symbol][feature]
            total = symbol_counts[symbol]
            # Bernoulli with symmetric smoothing.
            p = (count + ALPHA) / (total + 2 * ALPHA)
            score += math.log(p if feature in pair_feature_set else 1 - p)
    return score


def score_matrix(pairs: list[str], model: dict[str, Any], use_binary_features: bool) -> list[list[float]]:
    return [[score_pair_symbol(pair, symbol, model, use_binary_features) for symbol in SIGMA] for pair in pairs]


def leave_one_pair_out(pairs: list[str], labels: list[str], use_binary_features: bool) -> dict[str, Any]:
    predictions = {}
    correct = 0
    for index, pair in enumerate(pairs):
        model = train_model(pairs, labels, exclude_index=index)
        scores = score_matrix([pair], model, use_binary_features)[0]
        best_idx = max(range(len(SIGMA)), key=lambda idx: (scores[idx], -idx))
        predicted = SIGMA[best_idx]
        predictions[pair] = {
            "true": labels[index],
            "predicted": predicted,
            "score": scores[best_idx],
        }
        correct += int(predicted == labels[index])
    return {"correct": correct, "total": len(pairs), "accuracy": correct / len(pairs), "predictions": predictions}


def exact_inventory_assignment(pairs: list[str], labels: list[str], use_binary_features: bool) -> dict[str, Any]:
    model = train_model(pairs, labels)
    scores = score_matrix(pairs, model, use_binary_features)
    inventory = Counter(labels)
    slots = []
    for symbol in SIGMA:
        slots.extend([symbol] * inventory[symbol])
    if len(slots) != len(pairs):
        raise ValueError("slot inventory mismatch")

    if linear_sum_assignment is not None:
        cost = [[-scores[row][SIGMA.index(symbol)] for symbol in slots] for row in range(len(pairs))]
        row_ind, col_ind = linear_sum_assignment(cost)
        assigned = [None] * len(pairs)
        total_score = 0.0
        for row, col in zip(row_ind, col_ind):
            symbol = slots[col]
            assigned[row] = symbol
            total_score += scores[row][SIGMA.index(symbol)]
        solver = "scipy_linear_sum_assignment"
    else:
        remaining = Counter(inventory)
        assigned = [None] * len(pairs)
        total_score = 0.0
        margins = []
        for row, pair in enumerate(pairs):
            ranked = sorted(((scores[row][idx], SIGMA[idx]) for idx in range(len(SIGMA))), reverse=True)
            margin = ranked[0][0] - ranked[1][0]
            margins.append((margin, row, ranked))
        for _, row, ranked in sorted(margins, reverse=True):
            for score, symbol in ranked:
                if remaining[symbol]:
                    assigned[row] = symbol
                    remaining[symbol] -= 1
                    total_score += score
                    break
        solver = "greedy_margin_fallback"
    correct = sum(1 for observed, predicted in zip(labels, assigned) if observed == predicted)
    return {
        "solver": solver,
        "correct": correct,
        "total": len(pairs),
        "accuracy": correct / len(pairs),
        "total_score": total_score,
        "assignments": {pair: assigned[index] for index, pair in enumerate(pairs)},
    }


def shuffled_labels(labels: list[str], rng: random.Random) -> list[str]:
    out = labels[:]
    rng.shuffle(out)
    return out


def summarize(values: list[float], observed: float, higher_is_better: bool = True) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    if higher_is_better:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {"observed": observed, "mean": mean, "sd": sd, "min": min(values), "max": max(values), "p": p, "z": z}


def evaluate_variant(pairs: list[str], labels: list[str], use_binary_features: bool) -> dict[str, Any]:
    loo = leave_one_pair_out(pairs, labels, use_binary_features)
    assignment = exact_inventory_assignment(pairs, labels, use_binary_features)
    rng = random.Random(RANDOM_SEED + (1 if use_binary_features else 0))
    loo_controls = []
    assignment_controls = []
    for _ in range(CONTROL_TRIALS):
        ctrl = shuffled_labels(labels, rng)
        loo_controls.append(leave_one_pair_out(pairs, ctrl, use_binary_features)["accuracy"])
        assignment_controls.append(exact_inventory_assignment(pairs, ctrl, use_binary_features)["accuracy"])
    return {
        "model": "endpoint_plus_binary_features" if use_binary_features else "endpoint_only",
        "leave_one_pair_out": {key: value for key, value in loo.items() if key != "predictions"},
        "exact_inventory_assignment": {key: value for key, value in assignment.items() if key != "assignments"},
        "controls": {
            "inventory_label_shuffle": {
                "leave_one_pair_out_accuracy": summarize(loo_controls, loo["accuracy"], True),
                "exact_inventory_assignment_accuracy": summarize(assignment_controls, assignment["accuracy"], True),
            }
        },
        "special_predictions": {
            pair: loo["predictions"][pair]
            for pair in ["19", "39", "33", "66", "06", "09", "16", "36", "68", "89"]
            if pair in loo["predictions"]
        },
    }


def verdict(variants: list[dict[str, Any]]) -> str:
    best_loo = max(variants, key=lambda row: row["leave_one_pair_out"]["accuracy"])
    loo_p = best_loo["controls"]["inventory_label_shuffle"]["leave_one_pair_out_accuracy"]["p"]
    assign_p = min(row["controls"]["inventory_label_shuffle"]["exact_inventory_assignment_accuracy"]["p"] for row in variants)
    if best_loo["leave_one_pair_out"]["accuracy"] >= 0.45 and loo_p <= 0.01:
        return "candidate_endpoint_affinity_generator"
    if loo_p <= 0.05 or assign_p <= 0.05:
        return "weak_endpoint_affinity_signal_not_formula"
    return "rejected_endpoint_affinity"


def write_report(result: dict[str, Any]) -> None:
    lines = [
        "# Endpoint Affinity Assignment Search",
        "",
        "Generated by `endpoint_affinity_assignment_search.py`.",
        "",
        "This pass tests whether pair labels can be generated by symbol-specific",
        "digit endpoint affinities plus small binary features, optionally with",
        "the exact observed homophone inventory. It assigns no plaintext.",
        "",
        "## Summary",
        "",
        "| Model | LOO accuracy | LOO p | Inventory assignment | Assignment p | Solver | Verdict |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in result["variants"]:
        ctrl = row["controls"]["inventory_label_shuffle"]
        lines.append(
            f"| `{row['model']}` | {row['leave_one_pair_out']['accuracy']:.3f} | {ctrl['leave_one_pair_out_accuracy']['p']:.5f} | {row['exact_inventory_assignment']['accuracy']:.3f} | {ctrl['exact_inventory_assignment_accuracy']['p']:.5f} | `{row['exact_inventory_assignment']['solver']}` | `{result['verdict']}` |"
        )
    lines += [
        "",
        "## Special Pair Leave-One-Out Predictions",
        "",
        "| Model | Pair | True | Predicted |",
        "|---|---|---|---|",
    ]
    for row in result["variants"]:
        for pair, pred in row["special_predictions"].items():
            lines.append(f"| `{row['model']}` | `{pair}` | `{pred['true']}` | `{pred['predicted']}` |")
    lines += [
        "",
        "## Interpretation",
        "",
        "The exact-inventory assignment is treated as diagnostic only because it",
        "learns affinities from the full table. Promotion would require strong",
        "leave-one-pair-out prediction and separation from label-shuffled controls.",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pairs = natural_pairs()
    labels = [primary_pair_symbol(formula["pair_table"], pair) for pair in pairs]
    variants = [evaluate_variant(pairs, labels, False), evaluate_variant(pairs, labels, True)]
    result = {
        "schema": "endpoint_affinity_assignment_results.v1",
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "binary_features": BINARY_FEATURES,
        "variants": variants,
        "verdict": verdict(variants),
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    best = max(variants, key=lambda row: row["leave_one_pair_out"]["accuracy"])
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"verdict={result['verdict']} best={best['model']} loo={best['leave_one_pair_out']['accuracy']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
