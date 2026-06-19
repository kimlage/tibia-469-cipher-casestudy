#!/usr/bin/env python3
"""Low-rank factor probe over the `6 <-> 9` quotient pair table.

The raw bilinear/SVD probe found a weak surface signal over the 55 unordered
pair cells. This follow-up asks whether the signal becomes more predictive when
the strongest current matrix clue, the `6 <-> 9` digit quotient, is applied.

The predictive target is the canonical/base label recorded for each of the 46
quotient orbits. That target is intentionally lossy: mixed orbits still require
secondary label and orientation metadata before the original 55-cell table can
be reconstructed. No plaintext is assigned.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ORBIT_JSON = HERE / "digit_orbit_quotient_results.json"
RAW_LOW_RANK_JSON = HERE / "bilinear_low_rank_pair_factor_results.json"
QUOTIENT_FORMULA_JSON = HERE / "quotient_pair_formula_results.json"

OUT_JSON = HERE / "quotient_low_rank_pair_factor_results.json"
OUT_MD = HERE / "quotient_low_rank_pair_factor_report.md"

RANDOM_SEED = 46920260622
LABEL_CONTROL_TRIALS = 100
STRATIFIED_CONTROL_TRIALS = 60
RANKS = (1, 2, 3, 4, 5)
FILL_MODES = ("prior", "zero")
CENTERED = (False, True)

# Coordinate nodes: 0..5, Q=(6/9 collapsed), 7, 8, Qx. Qx is used only to keep
# the fixed cross-pair 69 distinct from the {66,99} orbit.
NODE_COUNT = 10
Q_NODE = 6
QX_NODE = 9


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def qdigit(digit: int) -> int:
    if digit in {6, 9}:
        return Q_NODE
    return digit


def qcoord_for_orbit(pairs: list[str]) -> tuple[int, int]:
    if set(pairs) == {"69"}:
        return Q_NODE, QX_NODE
    coords = set()
    for pair in pairs:
        a, b = qdigit(int(pair[0])), qdigit(int(pair[1]))
        coords.add(tuple(sorted((a, b))))
    if len(coords) != 1:
        raise ValueError(f"orbit does not collapse to one quotient coordinate: {pairs}")
    return next(iter(coords))


def node_label(node: int) -> str:
    return "Q" if node == Q_NODE else ("Qx" if node == QX_NODE else str(node))


def build_targets(orbit_result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for orbit in orbit_result["swap_6_9"]["orbits"]:
        qa, qb = qcoord_for_orbit(orbit["pairs"])
        label_counts = orbit["label_counts"]
        label_pair = tuple(sorted(label_counts))
        rows.append(
            {
                "orbit": int(orbit["orbit"]),
                "pairs": list(orbit["pairs"]),
                "qa": qa,
                "qb": qb,
                "qcoord": f"{node_label(qa)}{node_label(qb)}",
                "primary_symbol": orbit["label"],
                "acceptable_symbols": sorted(label_counts),
                "label_counts": label_counts,
                "label_pair": list(label_pair),
                "orbit_size": int(orbit["size"]),
                "is_singleton": int(orbit["size"]) == 1,
                "is_non_singleton": int(orbit["size"]) > 1,
                "is_mixed_orbit": bool(orbit["is_mixed"]),
                "fixed_cross_69": set(orbit["pairs"]) == {"69"},
            }
        )
    rows.sort(key=lambda row: row["orbit"])
    return rows


def rank_approx(matrix: np.ndarray, rank: int) -> np.ndarray:
    u, s, vh = np.linalg.svd(matrix, full_matrices=False)
    return (u[:, :rank] * s[:rank]) @ vh[:rank, :]


def train_symbol_surface(
    targets: list[dict[str, Any]],
    labels: list[str],
    symbols: list[str],
    symbol: str,
    rank: int,
    fill_mode: str,
    centered: bool,
    exclude_index: int | None,
) -> np.ndarray:
    train_indexes = [idx for idx in range(len(targets)) if idx != exclude_index]
    train_count = len(train_indexes)
    prior = sum(labels[idx] == symbol for idx in train_indexes) / train_count if train_count else 0.0
    fill = prior if fill_mode == "prior" else 0.0
    matrix = np.full((NODE_COUNT, NODE_COUNT), fill, dtype=float)
    for idx in train_indexes:
        row = targets[idx]
        qa, qb = int(row["qa"]), int(row["qb"])
        value = 1.0 if labels[idx] == symbol else 0.0
        matrix[qa, qb] = value
        matrix[qb, qa] = value
    if centered:
        return rank_approx(matrix - prior, rank) + prior
    return rank_approx(matrix, rank)


def predict_scores(
    targets: list[dict[str, Any]],
    labels: list[str],
    symbols: list[str],
    rank: int,
    fill_mode: str,
    centered: bool,
    exclude_index: int | None,
) -> dict[int, list[float]]:
    surfaces = {
        symbol: train_symbol_surface(targets, labels, symbols, symbol, rank, fill_mode, centered, exclude_index)
        for symbol in symbols
    }
    target_indexes = [exclude_index] if exclude_index is not None else list(range(len(targets)))
    scores = {}
    for idx in target_indexes:
        row = targets[idx]
        qa, qb = int(row["qa"]), int(row["qb"])
        out = []
        for symbol in symbols:
            surface = surfaces[symbol]
            out.append(float(surface[qa, qb] if qa == qb else (surface[qa, qb] + surface[qb, qa]) / 2.0))
        scores[idx] = out
    return scores


def predict_one(scores: list[float], symbols: list[str]) -> str:
    best = max(range(len(symbols)), key=lambda idx: (scores[idx], -idx))
    return symbols[best]


def macro_recall(labels: list[str], predictions: list[str], symbols: list[str]) -> float:
    recalls = []
    for symbol in symbols:
        total = sum(label == symbol for label in labels)
        if total:
            correct = sum(label == symbol and pred == symbol for label, pred in zip(labels, predictions))
            recalls.append(correct / total)
    return sum(recalls) / len(recalls) if recalls else 0.0


def subgroup_accuracy(targets: list[dict[str, Any]], labels: list[str], predictions: list[str], key: str) -> dict[str, Any]:
    indexes = [idx for idx, row in enumerate(targets) if row[key]]
    if not indexes:
        return {"count": 0, "correct": 0, "accuracy": None}
    correct = sum(predictions[idx] == labels[idx] for idx in indexes)
    return {"count": len(indexes), "correct": correct, "accuracy": correct / len(indexes)}


def acceptable_accuracy(targets: list[dict[str, Any]], predictions: list[str], key: str | None = None) -> dict[str, Any]:
    indexes = [idx for idx, row in enumerate(targets) if key is None or row[key]]
    if not indexes:
        return {"count": 0, "correct": 0, "accuracy": None}
    correct = sum(predictions[idx] in set(targets[idx]["acceptable_symbols"]) for idx in indexes)
    return {"count": len(indexes), "correct": correct, "accuracy": correct / len(indexes)}


def lossless_diagnostics(targets: list[dict[str, Any]], labels: list[str], predictions: list[str]) -> dict[str, Any]:
    pure_indexes = [idx for idx, row in enumerate(targets) if not row["is_mixed_orbit"]]
    mixed_indexes = [idx for idx, row in enumerate(targets) if row["is_mixed_orbit"]]
    lossless_exact = sum(predictions[idx] == labels[idx] for idx in pure_indexes)
    raw_pair_hits = 0
    raw_pair_total = 0
    for idx, row in enumerate(targets):
        raw_pair_total += int(row["orbit_size"])
        if not row["is_mixed_orbit"]:
            raw_pair_hits += int(row["orbit_size"]) if predictions[idx] == labels[idx] else 0
        elif predictions[idx] in set(row["acceptable_symbols"]):
            raw_pair_hits += 1
    return {
        "lossless_orbit_exact_without_mixed_layer": {
            "correct": lossless_exact,
            "total": len(targets),
            "accuracy": lossless_exact / len(targets),
            "note": "mixed orbits cannot be exact because this probe predicts no secondary/orientation metadata",
        },
        "mixed_orbit_acceptable": acceptable_accuracy(targets, predictions, "is_mixed_orbit"),
        "raw_pair_hits_if_label_rendered_to_whole_orbit": {
            "correct": raw_pair_hits,
            "total": raw_pair_total,
            "accuracy": raw_pair_hits / raw_pair_total,
        },
        "mixed_orbit_count": len(mixed_indexes),
    }


def evaluate_config(
    targets: list[dict[str, Any]],
    labels: list[str],
    symbols: list[str],
    rank: int,
    fill_mode: str,
    centered: bool,
) -> dict[str, Any]:
    full_scores = predict_scores(targets, labels, symbols, rank, fill_mode, centered, None)
    in_sample_predictions = [predict_one(full_scores[idx], symbols) for idx in range(len(targets))]
    in_sample_correct = sum(pred == labels[idx] for idx, pred in enumerate(in_sample_predictions))

    loo_predictions = []
    special_predictions = {}
    for idx, row in enumerate(targets):
        scores = predict_scores(targets, labels, symbols, rank, fill_mode, centered, idx)[idx]
        predicted = predict_one(scores, symbols)
        loo_predictions.append(predicted)
        if row["fixed_cross_69"] or row["is_mixed_orbit"] or row["pairs"] in (["66", "99"],):
            special_predictions[str(row["orbit"])] = {
                "pairs": row["pairs"],
                "qcoord": row["qcoord"],
                "true": labels[idx],
                "acceptable_symbols": row["acceptable_symbols"],
                "predicted": predicted,
                "is_mixed_orbit": row["is_mixed_orbit"],
            }

    loo_correct = sum(pred == labels[idx] for idx, pred in enumerate(loo_predictions))
    diagnostics = lossless_diagnostics(targets, labels, loo_predictions)
    return {
        "rank": rank,
        "fill_mode": fill_mode,
        "centered": centered,
        "in_sample_correct": in_sample_correct,
        "in_sample_accuracy": in_sample_correct / len(targets),
        "in_sample_macro_recall": macro_recall(labels, in_sample_predictions, symbols),
        "loo_correct": loo_correct,
        "loo_accuracy": loo_correct / len(targets),
        "loo_macro_recall": macro_recall(labels, loo_predictions, symbols),
        "pure_orbit_accuracy": subgroup_accuracy(
            targets, labels, loo_predictions, "is_singleton"
        ),
        "non_singleton_orbit_accuracy": subgroup_accuracy(
            targets, labels, loo_predictions, "is_non_singleton"
        ),
        "mixed_orbit_primary_accuracy": subgroup_accuracy(
            targets, labels, loo_predictions, "is_mixed_orbit"
        ),
        "all_orbit_acceptable_accuracy": acceptable_accuracy(targets, loo_predictions),
        "lossless_diagnostics": diagnostics,
        "parameter_count": len(symbols) * (2 * NODE_COUNT * rank + 1),
        "special_predictions": special_predictions,
    }


def evaluate_all(targets: list[dict[str, Any]], labels: list[str], symbols: list[str]) -> list[dict[str, Any]]:
    rows = []
    for rank in RANKS:
        for fill_mode in FILL_MODES:
            for centered in CENTERED:
                rows.append(evaluate_config(targets, labels, symbols, rank, fill_mode, centered))
    rows.sort(key=lambda row: (-row["loo_accuracy"], row["parameter_count"], -row["in_sample_accuracy"]))
    return rows


def prior_baseline(targets: list[dict[str, Any]], labels: list[str], symbols: list[str]) -> dict[str, Any]:
    predictions = []
    for holdout in range(len(targets)):
        train = [label for idx, label in enumerate(labels) if idx != holdout]
        predictions.append(Counter(train).most_common(1)[0][0])
    correct = sum(pred == labels[idx] for idx, pred in enumerate(predictions))
    return {
        "correct": correct,
        "accuracy": correct / len(targets),
        "macro_recall": macro_recall(labels, predictions, symbols),
        "lossless_diagnostics": lossless_diagnostics(targets, labels, predictions),
    }


def endpoint_marginal_baseline(targets: list[dict[str, Any]], labels: list[str], symbols: list[str]) -> dict[str, Any]:
    predictions = []
    alpha = 0.75
    for holdout, target in enumerate(targets):
        symbol_counts = Counter()
        endpoint_counts = {symbol: Counter() for symbol in symbols}
        for idx, row in enumerate(targets):
            if idx == holdout:
                continue
            label = labels[idx]
            symbol_counts[label] += 1
            endpoint_counts[label][row["qa"]] += 1
            endpoint_counts[label][row["qb"]] += 1
        scores = []
        for symbol in symbols:
            prior = math.log((symbol_counts[symbol] + alpha) / (len(targets) - 1 + alpha * len(symbols)))
            total = 2 * symbol_counts[symbol]
            score = prior
            score += math.log((endpoint_counts[symbol][target["qa"]] + alpha) / (total + alpha * NODE_COUNT))
            score += math.log((endpoint_counts[symbol][target["qb"]] + alpha) / (total + alpha * NODE_COUNT))
            scores.append(score)
        predictions.append(predict_one(scores, symbols))
    correct = sum(pred == labels[idx] for idx, pred in enumerate(predictions))
    return {
        "correct": correct,
        "accuracy": correct / len(targets),
        "macro_recall": macro_recall(labels, predictions, symbols),
        "lossless_diagnostics": lossless_diagnostics(targets, labels, predictions),
    }


def neighbor_label_baseline(targets: list[dict[str, Any]], labels: list[str], symbols: list[str]) -> dict[str, Any]:
    predictions = []
    for holdout, row in enumerate(targets):
        endpoints = {row["qa"], row["qb"]}
        counts = Counter()
        for idx, train in enumerate(targets):
            if idx == holdout:
                continue
            if endpoints.intersection({train["qa"], train["qb"]}):
                counts[labels[idx]] += 1
        if not counts:
            counts = Counter(label for idx, label in enumerate(labels) if idx != holdout)
        predictions.append(counts.most_common(1)[0][0])
    correct = sum(pred == labels[idx] for idx, pred in enumerate(predictions))
    return {
        "correct": correct,
        "accuracy": correct / len(targets),
        "macro_recall": macro_recall(labels, predictions, symbols),
        "lossless_diagnostics": lossless_diagnostics(targets, labels, predictions),
    }


def control_summary(values: list[float], observed: float) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "p_ge_observed": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
    }


def label_shuffle_control(
    targets: list[dict[str, Any]],
    labels: list[str],
    symbols: list[str],
    observed_best: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    loo_values = []
    macro_values = []
    for _ in range(LABEL_CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        best = evaluate_all(targets, shuffled, symbols)[0]
        loo_values.append(best["loo_accuracy"])
        macro_values.append(best["loo_macro_recall"])
    return {
        "method": "quotient_base46_inventory_preserving_label_shuffle",
        "trials": LABEL_CONTROL_TRIALS,
        "best_config_selection": "best LOO accuracy over rank/fill/centering in each trial",
        "loo_accuracy": control_summary(loo_values, observed_best["loo_accuracy"]),
        "loo_macro_recall": control_summary(macro_values, observed_best["loo_macro_recall"]),
    }


def orbit_stratum(row: dict[str, Any]) -> str:
    if row["is_mixed_orbit"]:
        return "mixed_orbit"
    if row["is_non_singleton"]:
        return "non_singleton_pure_orbit"
    return "singleton_orbit"


def stratified_mixedness_control(
    targets: list[dict[str, Any]],
    labels: list[str],
    symbols: list[str],
    observed_best: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 1)
    strata: dict[str, list[int]] = {}
    for idx, row in enumerate(targets):
        strata.setdefault(orbit_stratum(row), []).append(idx)
    loo_values = []
    macro_values = []
    for _ in range(STRATIFIED_CONTROL_TRIALS):
        shuffled_labels = labels[:]
        for indexes in strata.values():
            stratum_labels = [labels[idx] for idx in indexes]
            rng.shuffle(stratum_labels)
            for idx, label in zip(indexes, stratum_labels):
                shuffled_labels[idx] = label
        best = evaluate_all(targets, shuffled_labels, symbols)[0]
        loo_values.append(best["loo_accuracy"])
        macro_values.append(best["loo_macro_recall"])
    return {
        "method": "quotient_primary_label_shuffle_stratified_by_orbit_mixedness",
        "trials": STRATIFIED_CONTROL_TRIALS,
        "best_config_selection": "best LOO accuracy over rank/fill/centering in each trial",
        "loo_accuracy": control_summary(loo_values, observed_best["loo_accuracy"]),
        "loo_macro_recall": control_summary(macro_values, observed_best["loo_macro_recall"]),
    }


def multinomial_inventory_bits(labels: list[str]) -> float:
    counts = Counter(labels)
    return math.lgamma(len(labels) + 1) / math.log(2) - sum(math.lgamma(count + 1) / math.log(2) for count in counts.values())


def mdl_context(best: dict[str, Any], labels: list[str], symbols: list[str], orbit_result: dict[str, Any]) -> dict[str, Any]:
    quotient_lookup_bits = len(labels) * math.log2(len(symbols))
    inventory_lookup_bits = multinomial_inventory_bits(labels)
    split_lossless_bits = orbit_result["swap_6_9"]["split_lossless_bits"]
    model_choice_bits = math.log2(len(RANKS) * len(FILL_MODES) * len(CENTERED))
    quotient_choice_bits_if_discovered = math.log2(45)
    fixed_cross_coordinate_bits = 1.0
    lower_bound_parameter_bits = best["parameter_count"] * 8
    residual_orbit_correction_bits = (len(labels) - best["loo_correct"]) * math.log2(len(symbols))
    conditioned_bits = lower_bound_parameter_bits + model_choice_bits + fixed_cross_coordinate_bits
    discovered_bits = conditioned_bits + quotient_choice_bits_if_discovered
    conditioned_lossless_lower_bound_bits = (
        conditioned_bits
        + residual_orbit_correction_bits
        + orbit_result["swap_6_9"]["split_mixed_selector_bits"]
        + orbit_result["swap_6_9"]["mixed_orbit_count"] * math.log2(len(symbols))
    )
    return {
        "quotient_lookup_bits": quotient_lookup_bits,
        "quotient_inventory_lookup_bits": inventory_lookup_bits,
        "existing_split_lossless_bits": split_lossless_bits,
        "parameter_count": best["parameter_count"],
        "lower_bound_parameter_bits": lower_bound_parameter_bits,
        "model_choice_bits": model_choice_bits,
        "fixed_cross_coordinate_bits": fixed_cross_coordinate_bits,
        "quotient_choice_bits_if_discovered": quotient_choice_bits_if_discovered,
        "conditioned_lower_bound_bits": conditioned_bits,
        "discovered_lower_bound_bits": discovered_bits,
        "residual_orbit_correction_bits": residual_orbit_correction_bits,
        "conditioned_lossless_lower_bound_bits": conditioned_lossless_lower_bound_bits,
        "conditioned_ratio_to_quotient_lookup": conditioned_bits / quotient_lookup_bits,
        "conditioned_ratio_to_inventory_lookup": conditioned_bits / inventory_lookup_bits,
        "conditioned_ratio_to_existing_split_lossless": conditioned_bits / split_lossless_bits,
        "lossless_lower_bound_ratio_to_existing_split_lossless": conditioned_lossless_lower_bound_bits / split_lossless_bits,
        "note": "8 bits/parameter is a favorable lower bound; continuous factors are not a deployable formula without quantization",
    }


def classify(best: dict[str, Any], controls: dict[str, Any], mdl: dict[str, Any], baselines: dict[str, Any]) -> str:
    label_p = controls["label_shuffle"]["loo_accuracy"]["p_ge_observed"]
    stratified_p = controls["stratified_mixedness_shuffle"]["loo_accuracy"]["p_ge_observed"]
    best_baseline = max(row["accuracy"] for row in baselines.values())
    if (
        best["loo_accuracy"] > best_baseline
        and label_p <= 0.01
        and stratified_p <= 0.01
        and mdl["lossless_lower_bound_ratio_to_existing_split_lossless"] < 1.0
        and best["lossless_diagnostics"]["mixed_orbit_acceptable"]["accuracy"] == 1.0
    ):
        return "candidate_quotient_low_rank_generator"
    if best["loo_accuracy"] > best_baseline and label_p <= 0.05 and stratified_p <= 0.05:
        return "weak_quotient_low_rank_signal_not_formula"
    if best["loo_accuracy"] > best_baseline:
        return "technical_gap_closed_rejected_control"
    return "rejected_control"


def write_report(result: dict[str, Any]) -> None:
    best = result["best_by_loo"]
    ctrl = result["controls"]["label_shuffle"]
    stratified = result["controls"]["stratified_mixedness_shuffle"]
    mdl = result["mdl_context"]
    raw = result["references"]["raw_low_rank"]
    qformula = result["references"]["quotient_pair_formula"]
    lines = [
        "# Quotient Low-Rank Pair Factor Search",
        "",
        "Generated by `quotient_low_rank_pair_factor_search.py`.",
        "",
        "This pass applies the continuous low-rank/SVD pair-label probe to the",
        "`6 <-> 9` quotient. The target is the canonical label of each of the",
        "46 quotient orbits. Mixed-orbit reconstruction remains a separate,",
        "charged lossless layer.",
        "",
        "## Summary",
        "",
        "| Best rank | Fill | Centered | Base46 LOO | Macro recall | Label-shuffle p | Stratified p | MDL lower bound | Lossless lower bound | Verdict |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
        f"| {best['rank']} | `{best['fill_mode']}` | `{best['centered']}` | "
        f"{best['loo_correct']}/46 ({best['loo_accuracy']:.3f}) | "
        f"{best['loo_macro_recall']:.3f} | "
        f"{ctrl['loo_accuracy']['p_ge_observed']:.5f} | "
        f"{stratified['loo_accuracy']['p_ge_observed']:.5f} | "
        f"{mdl['conditioned_ratio_to_inventory_lookup']:.3f}x quotient inventory lookup | "
        f"{mdl['lossless_lower_bound_ratio_to_existing_split_lossless']:.3f}x split-lossless | "
        f"`{result['verdict']}` |",
        "",
        "## Baselines",
        "",
        "| Baseline | LOO accuracy | Macro recall |",
        "|---|---:|---:|",
    ]
    for name, row in result["baselines"].items():
        lines.append(f"| `{name}` | {row['accuracy']:.3f} | {row['macro_recall']:.3f} |")
    lines.extend(
        [
            f"| raw low-rank 55-cell reference | {raw['loo_accuracy']:.3f} | {raw['loo_macro_recall']:.3f} |",
            f"| direct quotient formula reference | {qformula['primary_accuracy']:.3f} | n/a |",
            "",
            "## Subgroups",
            "",
            "| Subgroup | Correct | Accuracy |",
            "|---|---:|---:|",
        ]
    )
    for label, row in [
        ("singleton orbit primary", best["pure_orbit_accuracy"]),
        ("non-singleton orbit primary", best["non_singleton_orbit_accuracy"]),
        ("mixed orbit primary", best["mixed_orbit_primary_accuracy"]),
        ("mixed orbit acceptable", best["lossless_diagnostics"]["mixed_orbit_acceptable"]),
        (
            "lossless exact without mixed layer",
            best["lossless_diagnostics"]["lossless_orbit_exact_without_mixed_layer"],
        ),
        (
            "raw-pair hits if rendered to whole orbit",
            best["lossless_diagnostics"]["raw_pair_hits_if_label_rendered_to_whole_orbit"],
        ),
    ]:
        total = row.get("total", row.get("count"))
        correct = row["correct"]
        acc = row["accuracy"]
        lines.append(f"| {label} | {correct}/{total} | {acc:.3f} |")
    lines.extend(
        [
            "",
            "## Top Configurations",
            "",
            "| Rank | Fill | Centered | In-sample | LOO | Macro recall | Parameters |",
            "|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in result["rows"][:10]:
        lines.append(
            f"| {row['rank']} | `{row['fill_mode']}` | `{row['centered']}` | "
            f"{row['in_sample_accuracy']:.3f} | {row['loo_accuracy']:.3f} | "
            f"{row['loo_macro_recall']:.3f} | {row['parameter_count']} |"
        )
    lines.extend(
        [
            "",
            "## Special Orbit Leave-One-Out Predictions",
            "",
            "| Orbit | Pairs | Q-coordinate | True | Acceptable | Predicted | Mixed? |",
            "|---:|---|---|---|---|---|---:|",
        ]
    )
    for orbit, row in best["special_predictions"].items():
        lines.append(
            f"| {orbit} | `{','.join(row['pairs'])}` | `{row['qcoord']}` | `{row['true']}` | "
            f"`{','.join(row['acceptable_symbols'])}` | `{row['predicted']}` | {row['is_mixed_orbit']} |"
        )
    lines.extend(
        [
            "",
            "## Controls",
            "",
            "| Control | Trials | Mean best LOO | Max best LOO | p |",
            "|---|---:|---:|---:|---:|",
            f"| label shuffle | {ctrl['trials']} | {ctrl['loo_accuracy']['mean']:.3f} | "
            f"{ctrl['loo_accuracy']['max']:.3f} | {ctrl['loo_accuracy']['p_ge_observed']:.5f} |",
            f"| stratified mixedness shuffle | {stratified['trials']} | {stratified['loo_accuracy']['mean']:.3f} | "
            f"{stratified['loo_accuracy']['max']:.3f} | {stratified['loo_accuracy']['p_ge_observed']:.5f} |",
            "",
            "## Interpretation",
            "",
            "The test closes a narrow gap: the weak raw low-rank signal does not become",
            "a compact lossless quotient generator merely by applying the `6 <-> 9`",
            "orbit clue. The `base46` target is useful as a diagnostic surface only;",
            "the original pair table still needs mixed-orbit metadata and residual",
            "corrections, and the favorable parameter lower bound is more expensive",
            "than the existing compressed quotient accounting.",
            "",
            f"Translation delta: `{result['translation_delta']}`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    orbit_result = load_json(ORBIT_JSON)
    raw_low_rank = load_json(RAW_LOW_RANK_JSON)["best_by_loo"]
    quotient_formula = load_json(QUOTIENT_FORMULA_JSON)["observed"]["best"]
    targets = build_targets(orbit_result)
    labels = [row["primary_symbol"] for row in targets]
    symbols = sorted(set(labels))
    rows = evaluate_all(targets, labels, symbols)
    inventory = dict(Counter(labels))
    for row in rows:
        row["label_inventory"] = inventory
    best = rows[0]
    baselines = {
        "symbol_frequency_top": prior_baseline(targets, labels, symbols),
        "quotient_endpoint_marginal": endpoint_marginal_baseline(targets, labels, symbols),
        "quotient_neighbor_label": neighbor_label_baseline(targets, labels, symbols),
    }
    controls = {
        "label_shuffle": label_shuffle_control(targets, labels, symbols, best),
        "stratified_mixedness_shuffle": stratified_mixedness_control(targets, labels, symbols, best),
    }
    mdl = mdl_context(best, labels, symbols, orbit_result)
    result = {
        "schema": "quotient_low_rank_pair_factor_results.v1",
        "source": {
            "orbit_results": str(ORBIT_JSON.relative_to(ROOT)),
            "raw_low_rank_results": str(RAW_LOW_RANK_JSON.relative_to(ROOT)),
            "quotient_formula_results": str(QUOTIENT_FORMULA_JSON.relative_to(ROOT)),
        },
        "random_seed": RANDOM_SEED,
        "control_trials": {
            "label_shuffle": LABEL_CONTROL_TRIALS,
            "stratified_mixedness_shuffle": STRATIFIED_CONTROL_TRIALS,
        },
        "ranks": list(RANKS),
        "fill_modes": list(FILL_MODES),
        "centered_variants": list(CENTERED),
        "target": {
            "mode": "base46_predictive",
            "quotient_group": "swap_6_9",
            "orbit_count": len(targets),
            "mixed_orbit_count": sum(row["is_mixed_orbit"] for row in targets),
            "non_singleton_orbit_count": sum(row["is_non_singleton"] for row in targets),
            "coordinate_nodes": ["0", "1", "2", "3", "4", "5", "Q", "7", "8", "Qx"],
            "fixed_cross_collision_note": "`Qx` keeps orbit 69 distinct from orbit {66,99}; this is charged in MDL.",
            "rows": targets,
        },
        "baselines": baselines,
        "best_by_loo": best,
        "rows": rows,
        "controls": controls,
        "mdl_context": mdl,
        "references": {
            "raw_low_rank": {
                "loo_accuracy": raw_low_rank["loo_accuracy"],
                "loo_macro_recall": raw_low_rank["loo_macro_recall"],
                "verdict": load_json(RAW_LOW_RANK_JSON)["verdict"],
            },
            "quotient_pair_formula": {
                "primary_accuracy": quotient_formula["primary_accuracy"],
                "verdict": load_json(QUOTIENT_FORMULA_JSON)["verdict"],
            },
        },
        "verdict": classify(best, controls, mdl, baselines),
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "verdict={verdict} best_loo={acc:.3f} p={p:.5f}".format(
            verdict=result["verdict"],
            acc=best["loo_accuracy"],
            p=controls["label_shuffle"]["loo_accuracy"]["p_ge_observed"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
