#!/usr/bin/env python3
"""Render-origin probe for the E-priority layer.

Zero omission and ordered-code orientation are real rendering signals, but the
existing broad zero/homophone probe asks them to recover the whole 55-cell pair
table. This narrower pass asks whether render/context features explain only the
15 E-priority claims, or the four high-block blockers, beyond the already-known
geometry strata.

No symbol is used as a feature. Symbols only define the frozen targets.
Mechanical only; no plaintext is inferred.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import zero_homophone_transition_origin_probe as zh


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT_JSON = HERE / "render_origin_e_priority_probe_results.json"
OUT_MD = HERE / "render_origin_e_priority_probe_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 5000
PRIORITY_CLAIMS = {
    "11",
    "15",
    "33",
    "44",
    "45",
    "47",
    "48",
    "55",
    "57",
    "58",
    "66",
    "77",
    "78",
    "88",
    "99",
}
HIGH_BLOCKERS = {"45", "55", "77", "88"}
HIGH_BLOCK_CLAIMS = {"44", "45", "47", "48", "55", "57", "58", "77", "78", "88"}


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_pairs() -> list[str]:
    return [f"{a}{b}" for a in range(10) for b in range(a, 10)]


def pair_key(code: str) -> str:
    return "".join(sorted(code))


def orientation(code: str) -> str:
    if code[0] < code[1]:
        return "asc"
    if code[0] > code[1]:
        return "desc"
    return "same"


def entropy(parts: list[float]) -> float:
    total = sum(parts)
    if not total:
        return 0.0
    out = 0.0
    for value in parts:
        if value:
            p = value / total
            out -= p * math.log2(p)
    return out


def geometry_stratum(pair: str) -> str:
    a, b = int(pair[0]), int(pair[1])
    return "|".join(
        [
            f"diag={a == b}",
            f"prod5={a * b == 5}",
            f"high4578={a in {4, 5, 7, 8} and b in {4, 5, 7, 8}}",
            f"both_ge4={a >= 4 and b >= 4}",
        ]
    )


def collect_render_features(rows_by_book: dict[str, list[dict[str, Any]]], train_books: set[str]) -> dict[str, dict[str, float]]:
    stats: dict[str, Counter[str]] = {pair: Counter() for pair in all_pairs()}
    for book in sorted(train_books, key=zh.numeric_key):
        rows = rows_by_book[book]
        for index, row in enumerate(rows):
            pair = row["pair"]
            code = row["code"]
            prev_row = rows[index - 1] if index else None
            next_row = rows[index + 1] if index + 1 < len(rows) else None
            stats[pair]["count"] += 1
            stats[pair][f"orient_{orientation(code)}"] += 1
            stats[pair]["current_zero_omitted"] += int(row["omitted_zero"])
            stats[pair]["has_zero_code"] += int("0" in code)
            stats[pair]["ordered_desc_or_same"] += int(int(code[0]) >= int(code[1]))
            stats[pair]["ordered_digit_gap_sum"] += abs(int(code[0]) - int(code[1]))

            if prev_row is None:
                stats[pair]["prev_boundary"] += 1
            else:
                stats[pair]["prev_zero_omitted"] += int(prev_row["omitted_zero"])
                stats[pair][f"prev_orient_{orientation(prev_row['code'])}"] += 1
                stats[pair]["prev_desc_or_same"] += int(int(prev_row["code"][0]) >= int(prev_row["code"][1]))
                stats[pair]["prev_same_pair"] += int(prev_row["pair"] == pair)
                stats[pair]["prev_digit_continuity"] += int(prev_row["code"][-1] == code[0])

            if next_row is None:
                stats[pair]["next_boundary"] += 1
            else:
                stats[pair]["next_zero_omitted"] += int(next_row["omitted_zero"])
                stats[pair][f"next_orient_{orientation(next_row['code'])}"] += 1
                stats[pair]["next_desc_or_same"] += int(int(next_row["code"][0]) >= int(next_row["code"][1]))
                stats[pair]["next_same_pair"] += int(next_row["pair"] == pair)
                stats[pair]["next_digit_continuity"] += int(code[-1] == next_row["code"][0])

    features = {}
    for pair, row in stats.items():
        count = row["count"]
        if not count:
            features[pair] = {"log_count": 0.0}
            continue
        orient_counts = [row["orient_asc"], row["orient_desc"], row["orient_same"]]
        vector = {
            "log_count": math.log1p(count),
            "orient_asc_rate": row["orient_asc"] / count,
            "orient_desc_rate": row["orient_desc"] / count,
            "orient_same_rate": row["orient_same"] / count,
            "orientation_entropy": entropy(orient_counts),
            "orientation_bias_abs": abs(row["orient_asc"] - row["orient_desc"]) / count,
            "current_zero_omit_rate": row["current_zero_omitted"] / count,
            "has_zero_code_rate": row["has_zero_code"] / count,
            "ordered_desc_or_same_rate": row["ordered_desc_or_same"] / count,
            "ordered_digit_gap_mean": row["ordered_digit_gap_sum"] / count,
            "prev_zero_omit_rate": row["prev_zero_omitted"] / count,
            "prev_desc_or_same_rate": row["prev_desc_or_same"] / count,
            "prev_same_pair_rate": row["prev_same_pair"] / count,
            "prev_digit_continuity_rate": row["prev_digit_continuity"] / count,
            "prev_boundary_rate": row["prev_boundary"] / count,
            "next_zero_omit_rate": row["next_zero_omitted"] / count,
            "next_desc_or_same_rate": row["next_desc_or_same"] / count,
            "next_same_pair_rate": row["next_same_pair"] / count,
            "next_digit_continuity_rate": row["next_digit_continuity"] / count,
            "next_boundary_rate": row["next_boundary"] / count,
        }
        features[pair] = vector
    return features


def zscores(features: dict[str, dict[str, float]], universe: list[str]) -> dict[str, dict[str, float]]:
    keys = sorted({key for pair in universe for key in features[pair]})
    means = {}
    sds = {}
    for key in keys:
        vals = [features[pair].get(key, 0.0) for pair in universe]
        means[key] = sum(vals) / len(vals)
        sd = (sum((value - means[key]) ** 2 for value in vals) / (len(vals) - 1)) ** 0.5
        sds[key] = sd or 1.0
    return {
        pair: {key: (features[pair].get(key, 0.0) - means[key]) / sds[key] for key in keys}
        for pair in universe
    }


def score_prediction(selected: set[str], target: set[str]) -> dict[str, float | int]:
    tp = len(selected & target)
    fp = len(selected - target)
    fn = len(target - selected)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def candidate_selections(features: dict[str, dict[str, float]], universe: list[str], size: int) -> list[dict[str, Any]]:
    normalized = zscores(features, universe)
    keys = sorted({key for pair in universe for key in features[pair]})
    rows: list[dict[str, Any]] = []

    def add(rule_id: str, values: dict[str, float], descending: bool) -> None:
        ordered = sorted(universe, key=lambda pair: (values[pair], pair), reverse=descending)
        rows.append(
            {
                "rule_id": rule_id,
                "selected": sorted(ordered[:size]),
                "selected_count": size,
                "feature_count": rule_id.count("+") + 1,
            }
        )

    for key in keys:
        values = {pair: features[pair].get(key, 0.0) for pair in universe}
        add(f"top:{key}", values, True)
        add(f"bottom:{key}", values, False)

    for left, right in itertools.combinations(keys, 2):
        values = {pair: normalized[pair][left] + normalized[pair][right] for pair in universe}
        add(f"top:{left}+{right}", values, True)
        add(f"bottom:{left}+{right}", values, False)

    unique = {}
    for row in rows:
        key = tuple(row["selected"])
        if key not in unique or row["feature_count"] < unique[key]["feature_count"]:
            unique[key] = row
    return list(unique.values())


def best_render_rule(features: dict[str, dict[str, float]], universe: list[str], target: set[str]) -> dict[str, Any]:
    rows = []
    for row in candidate_selections(features, universe, len(target)):
        score = score_prediction(set(row["selected"]), target)
        rows.append({**row, **score})
    rows.sort(key=lambda row: (-row["f1"], row["feature_count"], row["rule_id"]))
    return rows[0]


def shuffle_target_global(universe: list[str], target: set[str], rng: random.Random) -> set[str]:
    return set(rng.sample(universe, len(target)))


def shuffle_target_stratified(universe: list[str], target: set[str], rng: random.Random) -> set[str]:
    by_stratum: dict[str, list[str]] = defaultdict(list)
    target_counts = Counter()
    for pair in universe:
        stratum = geometry_stratum(pair)
        by_stratum[stratum].append(pair)
        if pair in target:
            target_counts[stratum] += 1
    out = set()
    for stratum, pairs in by_stratum.items():
        count = target_counts[stratum]
        if count:
            out.update(rng.sample(pairs, count))
    return out


def control_search(features: dict[str, dict[str, float]], universe: list[str], target: set[str], observed: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + len(universe) * 31 + len(target))
    global_f1 = []
    strat_f1 = []
    for _trial in range(CONTROL_TRIALS):
        global_target = shuffle_target_global(universe, target, rng)
        strat_target = shuffle_target_stratified(universe, target, rng)
        global_f1.append(best_render_rule(features, universe, global_target)["f1"])
        strat_f1.append(best_render_rule(features, universe, strat_target)["f1"])

    def summarize(vals: list[float]) -> dict[str, float]:
        mean = sum(vals) / len(vals)
        sd = (sum((value - mean) ** 2 for value in vals) / (len(vals) - 1)) ** 0.5
        return {
            "mean": mean,
            "sd": sd,
            "p_ge_observed": (sum(value >= observed["f1"] for value in vals) + 1) / (len(vals) + 1),
            "max": max(vals),
        }

    return {
        "global_target_shuffle": summarize(global_f1),
        "geometry_stratified_target_shuffle": summarize(strat_f1),
    }


def evaluate_target(name: str, features: dict[str, dict[str, float]], universe: list[str], target: set[str]) -> dict[str, Any]:
    best = best_render_rule(features, universe, target)
    controls = control_search(features, universe, target, best)
    return {
        "name": name,
        "universe_size": len(universe),
        "target_size": len(target),
        "target": sorted(target),
        "best": best,
        "controls": controls,
    }


def classify(priority: dict[str, Any], blockers: dict[str, Any]) -> str:
    priority_p = priority["controls"]["geometry_stratified_target_shuffle"]["p_ge_observed"]
    blocker_p = blockers["controls"]["geometry_stratified_target_shuffle"]["p_ge_observed"]
    if priority["best"]["f1"] >= 0.75 and priority_p <= 0.05:
        return "candidate_render_origin_e_priority_signal"
    if blocker_p <= 0.05:
        return "weak_render_blocker_signal"
    return "render_origin_e_priority_not_promoted"


def write_report(result: dict[str, Any]) -> None:
    lines = [
        "# Render-Origin E-Priority Probe",
        "",
        "Generated by `render_origin_e_priority_probe.py`.",
        "",
        "This tests whether zero/orientation/render-context features explain the",
        "15 E-priority claims or the 4 high-block blockers. Symbols are targets",
        "only, never features.",
        "",
        "## Summary",
        "",
        "| Target | Universe | Best rule | F1 | TP | Global p | Geometry-stratified p |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for key in ["priority_claims", "high_block_blockers"]:
        row = result[key]
        best = row["best"]
        lines.append(
            f"| `{row['name']}` | {row['universe_size']} | `{best['rule_id']}` | {best['f1']:.3f} | {best['tp']}/{row['target_size']} | {row['controls']['global_target_shuffle']['p_ge_observed']:.5f} | {row['controls']['geometry_stratified_target_shuffle']['p_ge_observed']:.5f} |"
        )
    lines += [
        "",
        f"Verdict: `{result['verdict']}`.",
        "",
        "## Interpretation",
        "",
        "A positive result would mean the render channel helps identify the",
        "E-priority sublayer beyond the known geometric predicates. If only global",
        "controls pass but geometry-stratified controls fail, the apparent signal",
        "is still just geometry leakage.",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = zh.load_json(zh.FORMULA_JSON)
    rows_by_book = zh.token_rows(formula)
    train_books = set(formula["book_recipes"]) - zh.holdout_books(formula)
    features = collect_render_features(rows_by_book, train_books)

    priority = evaluate_target("priority_claims", features, all_pairs(), PRIORITY_CLAIMS)
    blockers = evaluate_target("high_block_blockers", features, sorted(HIGH_BLOCK_CLAIMS), HIGH_BLOCKERS)
    result = {
        "schema": "render_origin_e_priority_probe_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "train_books": sorted(train_books, key=zh.numeric_key),
        "feature_names": sorted({key for row in features.values() for key in row}),
        "priority_claims": priority,
        "high_block_blockers": blockers,
        "verdict": classify(priority, blockers),
        "translation_delta": "NONE",
        "new_plaintext": False,
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "priority_f1={pf1:.3f} priority_p={pp:.5f} blockers_f1={bf1:.3f} blockers_p={bp:.5f} verdict={verdict}".format(
            pf1=priority["best"]["f1"],
            pp=priority["controls"]["geometry_stratified_target_shuffle"]["p_ge_observed"],
            bf1=blockers["best"]["f1"],
            bp=blockers["controls"]["geometry_stratified_target_shuffle"]["p_ge_observed"],
            verdict=result["verdict"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
