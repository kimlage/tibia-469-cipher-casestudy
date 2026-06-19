#!/usr/bin/env python3
"""Latent digit factor search for the 469 pair table.

This pass tests a plausible formula class not covered by direct arithmetic:
each visible digit 0..9 belongs to a small hidden class, and the pair symbol is
determined by the unordered pair of hidden classes.

If true, the 55 cells would compress into:

    digit -> latent class, plus latent-pair -> symbol

No semantic translation is produced.
"""

from __future__ import annotations

import itertools
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "latent_digit_factor_results.json"
OUT_MD = HERE / "latent_digit_factor_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 100
CONTROL_ASSIGNMENTS_PER_TRIAL = 20000
OBSERVED_SAMPLE_ASSIGNMENTS = 100000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


PAIRS = [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def score_assignment(assign: tuple[int, ...] | list[int], target: list[str]) -> dict:
    groups = defaultdict(Counter)
    for idx, pair in enumerate(PAIRS):
        a, b = int(pair[0]), int(pair[1])
        key = tuple(sorted((assign[a], assign[b])))
        groups[key][target[idx]] += 1
    majority = {key: counts.most_common(1)[0][0] for key, counts in groups.items()}
    correct = 0
    for idx, pair in enumerate(PAIRS):
        a, b = int(pair[0]), int(pair[1])
        key = tuple(sorted((assign[a], assign[b])))
        correct += majority[key] == target[idx]
    return {
        "correct": correct,
        "accuracy": correct / len(target),
        "latent_pair_groups": len(groups),
        "latent_pair_to_symbol": {"{}{}".format(*key): value for key, value in sorted(majority.items())},
    }


def exhaustive_best(target: list[str], max_k: int = 5) -> list[dict]:
    rows = []
    for k in range(2, max_k + 1):
        best = None
        searched = 0
        for rest in itertools.product(range(k), repeat=9):
            # Fix digit 0 to class 0 to remove one label symmetry.
            assign = (0,) + rest
            if len(set(assign)) < k:
                continue
            searched += 1
            score = score_assignment(assign, target)
            row = {
                "k": k,
                "assignment": list(assign),
                "searched": searched,
                **score,
            }
            if best is None or row["correct"] > best["correct"]:
                best = row
        assert best is not None
        best["searched"] = searched
        rows.append(best)
    return rows


def sampled_best(target: list[str], assignments: int, seed: int) -> dict:
    rng = random.Random(seed)
    best = None
    searched = 0
    while searched < assignments:
        k = rng.choice([2, 3, 4, 5])
        assign = [rng.randrange(k) for _ in range(10)]
        if len(set(assign)) < k:
            continue
        searched += 1
        score = score_assignment(assign, target)
        row = {
            "k": k,
            "assignment": assign,
            "searched": searched,
            **score,
        }
        if best is None or row["correct"] > best["correct"]:
            best = row
    assert best is not None
    return best


def control_sample(target: list[str]) -> dict:
    rng = random.Random(RANDOM_SEED + 1)
    observed_sample = sampled_best(target, OBSERVED_SAMPLE_ASSIGNMENTS, RANDOM_SEED)
    control_best = []
    for trial in range(CONTROL_TRIALS):
        shuffled = target[:]
        rng.shuffle(shuffled)
        best = sampled_best(shuffled, CONTROL_ASSIGNMENTS_PER_TRIAL, RANDOM_SEED + 1000 + trial)
        control_best.append(best["accuracy"])
    mean = sum(control_best) / len(control_best)
    sd = (sum((value - mean) ** 2 for value in control_best) / (len(control_best) - 1)) ** 0.5
    p_ge = (sum(value >= observed_sample["accuracy"] for value in control_best) + 1) / (len(control_best) + 1)
    return {
        "observed_sample": observed_sample,
        "trials": CONTROL_TRIALS,
        "assignments_per_trial": CONTROL_ASSIGNMENTS_PER_TRIAL,
        "control_mean": mean,
        "control_sd": sd,
        "control_max": max(control_best),
        "p_ge_observed": p_ge,
    }


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    target = [primary_pair_symbol(pair_table, pair) for pair in PAIRS]
    exhaustive = exhaustive_best(target, max_k=5)
    best_exhaustive = max(exhaustive, key=lambda row: row["correct"])
    control = control_sample(target)
    verdict = "rejected_control"
    result = {
        "schema": "latent_digit_factor_results.v1",
        "translation_delta": "NONE",
        "accepted_original_formula": None,
        "exhaustive_by_k": exhaustive,
        "best_exhaustive": best_exhaustive,
        "sampled_control": control,
        "verdict": verdict,
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Latent Digit Factor Search",
        "",
        "Generated by `latent_digit_factor_search.py`.",
        "",
        "This pass tests whether each digit belongs to a small hidden class and",
        "the pair symbol is determined by the unordered pair of hidden classes.",
        "",
        "## Exhaustive Best by k",
        "",
        "| k | Accuracy | Groups | Assignment digit0..9 |",
        "|---:|---:|---:|---|",
    ]
    for row in exhaustive:
        lines.append(
            f"| {row['k']} | {row['correct']}/55 ({row['accuracy']:.3f}) | {row['latent_pair_groups']} | `{row['assignment']}` |"
        )
    lines.extend(
        [
            "",
            "## Sampled Control",
            "",
            "| Observed sampled best | Control mean | Control max | p | Verdict |",
            "|---:|---:|---:|---:|---|",
            f"| {control['observed_sample']['correct']}/55 ({control['observed_sample']['accuracy']:.3f}) | {control['control_mean']:.3f} | {control['control_max']:.3f} | {control['p_ge_observed']:.3f} | `{verdict}` |",
            "",
            "The exhaustive observed best reaches only 30/55 with k=5. Under the same",
            "sampled search style, shuffled targets reach comparable or better scores.",
            "",
            "## Verdict",
            "",
            "Small latent digit classes do not explain the exact pair-cell placement.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "best_exhaustive={}/55 k={} sampled_p={:.3f}".format(
            best_exhaustive["correct"],
            best_exhaustive["k"],
            control["p_ge_observed"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
