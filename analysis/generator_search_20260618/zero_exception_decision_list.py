#!/usr/bin/env python3
"""Sparse decision-list search for leading-zero omission.

The ML probe and the first explainer showed that leading-zero omission has a
real local-context signal, but the strongest explicit group rule is too table-
like. This pass asks whether the same signal can be compressed into a short
human-readable exception list on top of the `code_only` renderer.

No semantic translation is produced.
"""

from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable

from sklearn.metrics import accuracy_score, balanced_accuracy_score


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import zero_omission_rule_explainer as zero_rules  # noqa: E402


OUT_JSON = HERE / "zero_exception_decision_list_results.json"
OUT_MD = HERE / "zero_exception_decision_list_report.md"

RANDOM_SEED = 46920260622
CONTROL_TRIALS = 200
MAX_RULES = 20
MIN_SUPPORT = 3

FEATURES = [
    "prev_code",
    "prev_symbol",
    "next_symbol",
    "token_mod2",
    "token_mod3",
    "raw_mod2",
    "raw_mod3",
    "raw_mod5",
    "position_tenth",
]

CONJUNCTIVE_FEATURES = ["prev_code", "prev_symbol", "next_symbol"]


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def feature_value(row: dict, feature: str):
    return zero_rules.feature_value(row, feature)


def make_baseline(train: list[dict]):
    majority, default = zero_rules.group_rule(train, ("code",))

    def predict(row: dict) -> bool:
        return zero_rules.predict_group(row, ("code",), majority, default)

    return predict, majority, default


def baseline_description_bits(train: list[dict]) -> float:
    cardinality = zero_rules.feature_cardinality(train, "code")
    return len({row["code"] for row in train}) * (1.0 + math.log2(cardinality + 1))


def error_bits(error_count: int, row_count: int) -> float:
    return error_count * math.log2(row_count + 1)


def condition_text(name) -> str:
    if isinstance(name[0], tuple):
        left, right = name
        return f"{left[0]}={left[1]} & {right[0]}={right[1]}"
    feature, value = name
    return f"{feature}={value}"


def candidate_atoms(train: list[dict]) -> list[dict]:
    atoms = []
    for feature in FEATURES:
        values = sorted({feature_value(row, feature) for row in train}, key=str)
        for value in values:
            atoms.append(
                {
                    "name": (feature, value),
                    "feature_count": 1,
                    "fn": lambda row, feature=feature, value=value: feature_value(row, feature) == value,
                }
            )
    for feature in CONJUNCTIVE_FEATURES:
        values = sorted({(row["code"], feature_value(row, feature)) for row in train}, key=str)
        for code, value in values:
            atoms.append(
                {
                    "name": (("code", code), (feature, value)),
                    "feature_count": 2,
                    "fn": (
                        lambda row, code=code, feature=feature, value=value: row["code"] == code
                        and feature_value(row, feature) == value
                    ),
                }
            )
    filtered = []
    for atom in atoms:
        support = sum(1 for row in train if atom["fn"](row))
        if support >= MIN_SUPPORT:
            filtered.append({**atom, "support": support})
    return filtered


def rule_cost_bits(atom_count: int) -> float:
    # Encode one predicate from the preregistered atom inventory plus the
    # forced output label. This is intentionally conservative for short rules.
    return math.log2(atom_count * 2 + 1)


def apply_rules(row: dict, baseline: Callable[[dict], bool], rules: list[dict]) -> bool:
    prediction = baseline(row)
    for rule in rules:
        if rule["fn"](row):
            return rule["prediction"]
    return prediction


def predictions(rows: list[dict], baseline: Callable[[dict], bool], rules: list[dict]) -> list[bool]:
    return [apply_rules(row, baseline, rules) for row in rows]


def score(rows: list[dict], baseline: Callable[[dict], bool], rules: list[dict]) -> dict:
    y = [row["label"] for row in rows]
    pred = predictions(rows, baseline, rules)
    return {
        "accuracy": accuracy_score(y, pred),
        "balanced_accuracy": balanced_accuracy_score(y, pred),
        "errors": sum(left != right for left, right in zip(y, pred)),
    }


def mdl_bits(train: list[dict], rows: list[dict], baseline: Callable[[dict], bool], rules: list[dict], atom_count: int) -> float:
    scored = score(rows, baseline, rules)
    return baseline_description_bits(train) + len(rules) * rule_cost_bits(atom_count) + error_bits(scored["errors"], len(rows))


def greedy_path(train: list[dict], labels_override: list[bool] | None = None) -> dict:
    if labels_override is not None:
        train = [{**row, "label": label} for row, label in zip(train, labels_override)]
    baseline, _majority, _default = make_baseline(train)
    atoms = []
    for atom in candidate_atoms(train):
        indices = [index for index, row in enumerate(train) if atom["fn"](row)]
        atoms.append({**atom, "indices": indices})
    rules: list[dict] = []
    path = []
    labels = [row["label"] for row in train]
    current_predictions = [baseline(row) for row in train]

    for _step in range(MAX_RULES + 1):
        current_score = score(train, baseline, rules)
        path.append(
            {
                "rule_count": len(rules),
                **current_score,
                "train_mdl_bits": mdl_bits(train, train, baseline, rules, len(atoms)),
                "rules": [
                    {
                        "condition": condition_text(rule["name"]),
                        "prediction": bool(rule["prediction"]),
                        "support": rule["support"],
                        "train_gain": rule["train_gain"],
                    }
                    for rule in rules
                ],
            }
        )
        if len(rules) >= MAX_RULES:
            break
        best = None
        used = {(rule["name"], rule["prediction"]) for rule in rules}
        for atom in atoms:
            for prediction in [False, True]:
                if (atom["name"], prediction) in used:
                    continue
                gain = 0
                for index in atom["indices"]:
                    before = current_predictions[index] == labels[index]
                    after = prediction == labels[index]
                    gain += int(after) - int(before)
                if gain <= 0:
                    continue
                key = (gain, -atom["support"], condition_text(atom["name"]), prediction)
                if best is None or key > best[0]:
                    best = (key, {**atom, "prediction": prediction, "train_gain": gain})
        if best is None:
            break
        selected_rule = best[1]
        rules.append(selected_rule)
        for index in selected_rule["indices"]:
            current_predictions[index] = selected_rule["prediction"]

    selected_index, selected = min(
        enumerate(path),
        key=lambda item: (item[1]["train_mdl_bits"], item[1]["rule_count"]),
    )
    return {
        "baseline": baseline,
        "atom_count": len(atoms),
        "path": path,
        "selected_index": selected_index,
        "selected_rules_internal": rules[: selected["rule_count"]],
        "selected_train": selected,
    }


def code_preserving_label_shuffle(train: list[dict], rng: random.Random) -> list[bool]:
    labels = [row["label"] for row in train]
    by_code = defaultdict(list)
    for index, row in enumerate(train):
        by_code[row["code"]].append(index)
    shuffled = labels[:]
    for indices in by_code.values():
        values = [labels[index] for index in indices]
        rng.shuffle(values)
        for index, value in zip(indices, values):
            shuffled[index] = value
    return shuffled


def summarize(values: list[float], observed: float) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
    z = (observed - mean) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "z_good_direction": z,
        "p_good_direction": p,
        "control_min": min(values),
        "control_max": max(values),
    }


def write_report(result: dict) -> None:
    selected = result["selected"]
    baseline = result["baseline_holdout"]
    lines = [
        "# Zero Exception Decision List",
        "",
        "Generated by `zero_exception_decision_list.py`.",
        "",
        "This pass asks whether zero omission can be written as a short ordered",
        "exception list on top of `code_only`. It does not translate 469.",
        "",
        "## Selected Rule",
        "",
        "| Model | Rules | Holdout balanced acc | Holdout accuracy | Holdout errors | Holdout MDL bits | Control p | Verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
        (
            f"| `code_only` | 0 | {baseline['balanced_accuracy']:.3f} | {baseline['accuracy']:.3f} | "
            f"{baseline['errors']} | {result['baseline_holdout_mdl_bits']:.1f} | n/a | `baseline` |"
        ),
        (
            f"| `decision_list` | {selected['rule_count']} | {selected['holdout']['balanced_accuracy']:.3f} | "
            f"{selected['holdout']['accuracy']:.3f} | {selected['holdout']['errors']} | "
            f"{selected['holdout_mdl_bits']:.1f} | {result['shuffle_control']['p_good_direction']:.5f} | "
            f"`{result['verdict']}` |"
        ),
        "",
        "Selection used train MDL only; holdout numbers are not used to choose the rule count.",
        "",
        "## Ordered Exceptions",
        "",
        "| # | Condition | Output | Train support | Train gain |",
        "|---:|---|---|---:|---:|",
    ]
    for index, rule in enumerate(selected["rules"], start=1):
        output = "omit" if rule["prediction"] else "keep"
        lines.append(
            f"| {index} | `{rule['condition']}` | `{output}` | {rule['support']} | {rule['train_gain']} |"
        )
    lines += [
        "",
        "## Train Path",
        "",
        "| Rules | Train balanced acc | Train accuracy | Train MDL bits | Holdout balanced acc | Holdout accuracy |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["path"][:21]:
        lines.append(
            f"| {row['rule_count']} | {row['train']['balanced_accuracy']:.3f} | {row['train']['accuracy']:.3f} | "
            f"{row['train_mdl_bits']:.1f} | {row['holdout']['balanced_accuracy']:.3f} | {row['holdout']['accuracy']:.3f} |"
        )
    lines += ["", "## Verdict", ""]
    if result["holdout_mdl_gain_vs_code_only_bits"] > 0:
        lines.append(
            "The exception list improves holdout prediction and rough MDL versus code-only. "
            "Treat as a candidate mechanical zero-rendering rule only."
        )
    else:
        lines.append(
            "The exception list confirms a compact local-context signal, but its rough "
            "holdout MDL remains worse than code-only. Keep it as a render-layer clue, "
            "not an accepted formula."
        )
    lines += ["", f"Translation delta: `{result['translation_delta']}`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    train, test = zero_rules.build_dataset()
    path_result = greedy_path(train)
    baseline = path_result["baseline"]
    atom_count = path_result["atom_count"]
    selected_rules = path_result["selected_rules_internal"]

    baseline_holdout = score(test, baseline, [])
    baseline_holdout_mdl = mdl_bits(train, test, baseline, [], atom_count)
    path = []
    all_rules = []
    for rule in selected_rules:
        all_rules.append(rule)
    # Reconstruct a path with holdout metrics for the rules selected by the
    # train-only greedy path.
    selected_full_rules = path_result["selected_rules_internal"]
    for row in path_result["path"]:
        rules = selected_full_rules[: row["rule_count"]]
        path.append(
            {
                "rule_count": row["rule_count"],
                "train": {
                    "accuracy": row["accuracy"],
                    "balanced_accuracy": row["balanced_accuracy"],
                    "errors": row["errors"],
                },
                "train_mdl_bits": row["train_mdl_bits"],
                "holdout": score(test, baseline, rules),
                "holdout_mdl_bits": mdl_bits(train, test, baseline, rules, atom_count),
            }
        )

    selected = path[path_result["selected_index"]]
    selected_rules_public = [
        {
            "condition": condition_text(rule["name"]),
            "prediction": bool(rule["prediction"]),
            "support": rule["support"],
            "train_gain": rule["train_gain"],
        }
        for rule in selected_full_rules[: selected["rule_count"]]
    ]

    rng = random.Random(RANDOM_SEED)
    control_scores = []
    for _trial in range(CONTROL_TRIALS):
        shuffled_labels = code_preserving_label_shuffle(train, rng)
        shuffled_result = greedy_path(train, labels_override=shuffled_labels)
        shuffled_baseline = shuffled_result["baseline"]
        shuffled_rules = shuffled_result["selected_rules_internal"][: shuffled_result["selected_train"]["rule_count"]]
        control_scores.append(score(test, shuffled_baseline, shuffled_rules)["balanced_accuracy"])

    control = summarize(control_scores, selected["holdout"]["balanced_accuracy"])
    holdout_mdl_gain = baseline_holdout_mdl - selected["holdout_mdl_bits"]
    if selected["holdout"]["balanced_accuracy"] <= baseline_holdout["balanced_accuracy"]:
        verdict = "rejected_control"
    elif control["p_good_direction"] > 0.01:
        verdict = "rejected_control"
    elif holdout_mdl_gain > 0:
        verdict = "candidate_zero_exception_render_rule"
    else:
        verdict = "candidate_zero_exception_signal_only"

    result = {
        "schema": "zero_exception_decision_list_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "max_rules": MAX_RULES,
        "min_support": MIN_SUPPORT,
        "train_examples": len(train),
        "test_examples": len(test),
        "atom_count": atom_count,
        "baseline_holdout": baseline_holdout,
        "baseline_holdout_mdl_bits": baseline_holdout_mdl,
        "selected": {
            "rule_count": selected["rule_count"],
            "train": selected["train"],
            "train_mdl_bits": selected["train_mdl_bits"],
            "holdout": selected["holdout"],
            "holdout_mdl_bits": selected["holdout_mdl_bits"],
            "rules": selected_rules_public,
        },
        "path": path,
        "shuffle_control": control,
        "holdout_mdl_gain_vs_code_only_bits": holdout_mdl_gain,
        "verdict": verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} rules={selected['rule_count']} "
        f"bal={selected['holdout']['balanced_accuracy']:.3f} "
        f"mdl_gain={holdout_mdl_gain:.1f} p={control['p_good_direction']:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
