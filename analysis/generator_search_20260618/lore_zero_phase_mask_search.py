#!/usr/bin/env python3
"""Lore-number phase/mirror mask search for leading-zero omission.

This pass tests a narrow renderer hypothesis: numbers such as 3478, 43153, or
74032/45331 might act as a cyclic mask for the final leading-zero omission
layer. It targets only zero omission (`J`), not translation or pair-table
semantics.
"""

from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import zero_omission_rule_explainer as zero_rules  # noqa: E402


OUT_JSON = HERE / "lore_zero_phase_mask_results.json"
OUT_MD = HERE / "lore_zero_phase_mask_report.md"

RANDOM_SEED = 46920260624
CONTROL_TRIALS = 120
LORE_NUMBERS = ["1", "3478", "43153", "34784", "74032", "45331", "7403245331"]
FEATURES = [
    "phase_eq_first",
    "phase_eq_second",
    "phase_eq_either",
    "phase_pair_eq_current",
    "phase_pair_eq_previous",
    "phase_boundary",
]
ACTIONS = ["omit_if_true", "keep_if_true"]
VIEWS = ["ab", "ba"]


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_code_only(train: list[dict[str, Any]]):
    by_code: dict[str, list[bool]] = defaultdict(list)
    for row in train:
        by_code[row["code"]].append(row["label"])
    default = Counter(row["label"] for row in train).most_common(1)[0][0]
    majority = {code: Counter(values).most_common(1)[0][0] for code, values in by_code.items()}
    return lambda row: majority.get(row["code"], default)


def code_for_view(code: str, view: str) -> str:
    return code if view == "ab" else code[::-1]


def prev_code_for_view(row: dict[str, Any], view: str) -> str:
    prev = row["prev_code"]
    if len(prev) == 2 and prev.isdigit():
        return code_for_view(prev, view)
    return prev


def phase_bits(row: dict[str, Any], number: str, shift: int, view: str) -> dict[str, bool]:
    idx = (int(row["token_index"]) + shift) % len(number)
    digit = number[idx]
    next_digit = number[(idx + 1) % len(number)]
    pair = digit + next_digit
    code = code_for_view(row["code"], view)
    prev = prev_code_for_view(row, view)
    return {
        "phase_eq_first": digit == code[0],
        "phase_eq_second": digit == code[1],
        "phase_eq_either": digit in code,
        "phase_pair_eq_current": pair == code,
        "phase_pair_eq_previous": pair == prev,
        "phase_boundary": idx == 0,
    }


def predict_row(row: dict[str, Any], baseline, spec: dict[str, Any]) -> bool:
    pred = baseline(row)
    flag = phase_bits(row, spec["number"], spec["shift"], spec["view"])[spec["feature"]]
    if flag and spec["action"] == "omit_if_true":
        return True
    if flag and spec["action"] == "keep_if_true":
        return False
    return pred


def score(rows: list[dict[str, Any]], preds: list[bool]) -> dict[str, Any]:
    y = [row["label"] for row in rows]
    errors = int(sum(left != right for left, right in zip(y, preds)))
    positives = sum(y)
    negatives = len(y) - positives
    tp = sum(bool(label) and bool(pred) for label, pred in zip(y, preds))
    tn = sum((not bool(label)) and (not bool(pred)) for label, pred in zip(y, preds))
    tpr = tp / positives if positives else 0.0
    tnr = tn / negatives if negatives else 0.0
    return {
        "accuracy": 1.0 - errors / len(y),
        "balanced_accuracy": (tpr + tnr) / 2.0,
        "errors": errors,
    }


def error_bits(errors: int, rows: int) -> float:
    return errors * math.log2(rows + 1)


def code_only_mdl(train: list[dict[str, Any]], test: list[dict[str, Any]], scored: dict[str, Any]) -> float:
    code_count = len({row["code"] for row in train})
    return code_count * (1.0 + math.log2(code_count + 1)) + error_bits(scored["errors"], len(test))


def mask_cost_bits(spec: dict[str, Any]) -> float:
    return (
        math.log2(len(LORE_NUMBERS))
        + math.log2(len(spec["number"]))
        + math.log2(len(VIEWS))
        + math.log2(len(FEATURES))
        + math.log2(len(ACTIONS))
    )


def evaluate_spec(train: list[dict[str, Any]], test: list[dict[str, Any]], baseline, code_mdl: float, spec: dict[str, Any]) -> dict[str, Any]:
    preds = [predict_row(row, baseline, spec) for row in test]
    scored = score(test, preds)
    mdl = code_mdl + mask_cost_bits(spec) + error_bits(scored["errors"], len(test)) - error_bits(
        spec["code_only_errors"], len(test)
    )
    return {
        **spec,
        **scored,
        "mdl_bits": mdl,
        "mdl_gain_vs_code_only_bits": code_mdl - mdl,
        "support_holdout": int(
            sum(phase_bits(row, spec["number"], spec["shift"], spec["view"])[spec["feature"]] for row in test)
        ),
    }


def search_specs(numbers: list[str], train: list[dict[str, Any]], test: list[dict[str, Any]]) -> dict[str, Any]:
    baseline = make_code_only(train)
    code_preds = [baseline(row) for row in test]
    code_scored = score(test, code_preds)
    code_mdl = code_only_mdl(train, test, code_scored)
    rows = []
    for number in numbers:
        for shift in range(len(number)):
            for view in VIEWS:
                for feature in FEATURES:
                    for action in ACTIONS:
                        spec = {
                            "number": number,
                            "shift": shift,
                            "view": view,
                            "feature": feature,
                            "action": action,
                            "code_only_errors": code_scored["errors"],
                        }
                        rows.append(evaluate_spec(train, test, baseline, code_mdl, spec))
    rows.sort(key=lambda row: (-row["balanced_accuracy"], -row["mdl_gain_vs_code_only_bits"], row["number"], row["shift"]))
    by_mdl = sorted(rows, key=lambda row: (-row["mdl_gain_vs_code_only_bits"], -row["balanced_accuracy"]))
    return {
        "code_only": {**code_scored, "mdl_bits": code_mdl},
        "best_by_balanced_accuracy": rows[0],
        "best_by_mdl_gain": by_mdl[0],
        "top_rows": rows[:25],
    }


def summarize(values: list[float], observed: float, high_is_good: bool = True) -> dict[str, Any]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    if high_is_good:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "z_good": z,
        "p_good": p,
    }


def random_digit_string(rng: random.Random, length: int) -> str:
    return "".join(rng.choice("0123456789") for _ in range(length))


def permute_digits(rng: random.Random, number: str) -> str:
    chars = list(number)
    rng.shuffle(chars)
    return "".join(chars)


def control_numbers(train: list[dict[str, Any]], test: list[dict[str, Any]], observed: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    perm_bal = []
    perm_mdl = []
    rand_bal = []
    rand_mdl = []
    lengths = [len(number) for number in LORE_NUMBERS]
    for _ in range(CONTROL_TRIALS):
        permuted = [permute_digits(rng, number) for number in LORE_NUMBERS]
        perm_result = search_specs(permuted, train, test)
        perm_bal.append(perm_result["best_by_balanced_accuracy"]["balanced_accuracy"])
        perm_mdl.append(perm_result["best_by_mdl_gain"]["mdl_gain_vs_code_only_bits"])
        randoms = [random_digit_string(rng, length) for length in lengths]
        rand_result = search_specs(randoms, train, test)
        rand_bal.append(rand_result["best_by_balanced_accuracy"]["balanced_accuracy"])
        rand_mdl.append(rand_result["best_by_mdl_gain"]["mdl_gain_vs_code_only_bits"])
    return {
        "digit_multiset_permutation": {
            "trials": CONTROL_TRIALS,
            "best_balanced_accuracy": summarize(
                perm_bal, observed["best_by_balanced_accuracy"]["balanced_accuracy"], True
            ),
            "best_mdl_gain": summarize(
                perm_mdl, observed["best_by_mdl_gain"]["mdl_gain_vs_code_only_bits"], True
            ),
        },
        "random_same_length_digits": {
            "trials": CONTROL_TRIALS,
            "best_balanced_accuracy": summarize(
                rand_bal, observed["best_by_balanced_accuracy"]["balanced_accuracy"], True
            ),
            "best_mdl_gain": summarize(
                rand_mdl, observed["best_by_mdl_gain"]["mdl_gain_vs_code_only_bits"], True
            ),
        },
    }


def code_preserving_label_shuffle(train: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    shuffled = [dict(row) for row in train]
    by_code: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(train):
        by_code[row["code"]].append(index)
    for indices in by_code.values():
        labels = [train[index]["label"] for index in indices]
        rng.shuffle(labels)
        for index, label in zip(indices, labels):
            shuffled[index]["label"] = label
    return shuffled


def label_shuffle_control(train: list[dict[str, Any]], test: list[dict[str, Any]], observed: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 1)
    values = []
    for _ in range(CONTROL_TRIALS):
        shuffled = code_preserving_label_shuffle(train, rng)
        result = search_specs(LORE_NUMBERS, shuffled, test)
        values.append(result["best_by_balanced_accuracy"]["balanced_accuracy"])
    return {
        "method": "code_preserving_train_label_shuffle",
        "trials": CONTROL_TRIALS,
        "best_balanced_accuracy": summarize(
            values, observed["best_by_balanced_accuracy"]["balanced_accuracy"], True
        ),
    }


def classify(observed: dict[str, Any], controls: dict[str, Any]) -> str:
    best = observed["best_by_balanced_accuracy"]
    code = observed["code_only"]
    best_mdl = observed["best_by_mdl_gain"]
    p_perm = controls["digit_multiset_permutation"]["best_balanced_accuracy"]["p_good"]
    p_rand = controls["random_same_length_digits"]["best_balanced_accuracy"]["p_good"]
    p_label = controls["label_shuffle"]["best_balanced_accuracy"]["p_good"]
    if (
        best["balanced_accuracy"] > code["balanced_accuracy"]
        and best_mdl["mdl_gain_vs_code_only_bits"] > 0
        and max(p_perm, p_rand, p_label) <= 0.05
    ):
        return "candidate_lore_zero_phase_mask"
    if best["balanced_accuracy"] > code["balanced_accuracy"] and max(p_perm, p_rand, p_label) <= 0.10:
        return "weak_lore_zero_phase_signal_not_formula"
    return "rejected_control"


def write_report(result: dict[str, Any]) -> None:
    observed = result["observed"]
    best = observed["best_by_balanced_accuracy"]
    best_mdl = observed["best_by_mdl_gain"]
    code = observed["code_only"]
    controls = result["controls"]
    lines = [
        "# Lore Zero Phase Mask Search",
        "",
        "Generated by `lore_zero_phase_mask_search.py`.",
        "",
        "This pass tests lore-number cyclic masks against leading-zero omission",
        "only. It creates no translation or glossary.",
        "",
        "## Summary",
        "",
        "| Model | Number | Feature | Action | Shift | View | Bal acc | Errors | MDL gain | Verdict |",
        "|---|---|---|---|---:|---|---:|---:|---:|---|",
        f"| code_only | n/a | n/a | n/a | n/a | n/a | {code['balanced_accuracy']:.3f} | {code['errors']} | 0.0 | `baseline` |",
        f"| best_accuracy | `{best['number']}` | `{best['feature']}` | `{best['action']}` | {best['shift']} | `{best['view']}` | {best['balanced_accuracy']:.3f} | {best['errors']} | {best['mdl_gain_vs_code_only_bits']:.1f} | `{result['verdict']}` |",
        f"| best_mdl | `{best_mdl['number']}` | `{best_mdl['feature']}` | `{best_mdl['action']}` | {best_mdl['shift']} | `{best_mdl['view']}` | {best_mdl['balanced_accuracy']:.3f} | {best_mdl['errors']} | {best_mdl['mdl_gain_vs_code_only_bits']:.1f} | `{result['verdict']}` |",
        "",
        "## Controls",
        "",
        "| Control | Trials | Observed | Mean | Max | p |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in ["digit_multiset_permutation", "random_same_length_digits"]:
        row = controls[name]["best_balanced_accuracy"]
        lines.append(
            f"| `{name}` | {controls[name]['trials']} | {row['observed']:.3f} | {row['mean']:.3f} | {row['max']:.3f} | {row['p_good']:.5f} |"
        )
    label = controls["label_shuffle"]["best_balanced_accuracy"]
    lines.append(
        f"| `code_preserving_train_label_shuffle` | {controls['label_shuffle']['trials']} | {label['observed']:.3f} | {label['mean']:.3f} | {label['max']:.3f} | {label['p_good']:.5f} |"
    )
    lines.extend(
        [
            "",
            "## Top Rows",
            "",
            "| Number | Shift | View | Feature | Action | Bal acc | Errors | MDL gain | Support |",
            "|---|---:|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in observed["top_rows"][:12]:
        lines.append(
            f"| `{row['number']}` | {row['shift']} | `{row['view']}` | `{row['feature']}` | `{row['action']}` | "
            f"{row['balanced_accuracy']:.3f} | {row['errors']} | {row['mdl_gain_vs_code_only_bits']:.1f} | {row['support_holdout']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The lore-number phase family is intentionally small, but it is still a",
            "post-hoc renderer search. A candidate must beat digit-permutation,",
            "same-length random-number, and code-preserving label controls before",
            "it can be treated as more than a coincidental zero-render overlay.",
            "",
            f"Translation delta: `{result['translation_delta']}`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    train, test = zero_rules.build_dataset()
    observed = search_specs(LORE_NUMBERS, train, test)
    controls = control_numbers(train, test, observed)
    controls["label_shuffle"] = label_shuffle_control(train, test, observed)
    result = {
        "schema": "lore_zero_phase_mask_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "lore_numbers": LORE_NUMBERS,
        "features": FEATURES,
        "views": VIEWS,
        "actions": ACTIONS,
        "train_examples": len(train),
        "holdout_examples": len(test),
        "observed": observed,
        "controls": controls,
        "verdict": classify(observed, controls),
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "verdict={verdict} best_bal={bal:.3f} p_perm={p:.5f}".format(
            verdict=result["verdict"],
            bal=observed["best_by_balanced_accuracy"]["balanced_accuracy"],
            p=controls["digit_multiset_permutation"]["best_balanced_accuracy"]["p_good"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
