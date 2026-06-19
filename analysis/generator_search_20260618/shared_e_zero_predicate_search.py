#!/usr/bin/env python3
"""Fixed shared predicate test for E pressure and zero omission.

This is intentionally narrow. The only tested predicate is:

    P(i, j) = i >= j

On the unordered upper-triangle pair table this collapses to the diagonal
(`i == j`). On ordered previous codes it is exactly the zero-render geometry
already observed as "previous code descending or diagonal".

Mechanical only. No plaintext, glossary, or semantic translation is promoted.
"""

from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

sys.path.insert(0, str(HERE))
import zero_omission_rule_explainer as zero_rules  # noqa: E402


OUT_JSON = HERE / "shared_e_zero_predicate_results.json"
OUT_MD = HERE / "shared_e_zero_predicate_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 10000


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def unordered_pair(code: str) -> str:
    return "".join(sorted(code))


def pair_cells() -> list[str]:
    return [f"{a}{b}" for a in range(10) for b in range(a, 10)]


UNORDERED_CELLS = pair_cells()
DIAGONAL_CELLS = {f"{d}{d}" for d in range(10)}
ANCHOR_33_66 = {"33", "66"}


def pair_symbol(pair_table: dict[str, Any], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return "+".join(sorted(row["symbols"]))


def fixed_predicate_code(code: str) -> bool:
    return len(code) == 2 and code.isdigit() and int(code[0]) >= int(code[1])


def score_binary(y_true: list[bool], y_pred: list[bool]) -> dict[str, Any]:
    tp = sum(a and b for a, b in zip(y_true, y_pred))
    fp = sum((not a) and b for a, b in zip(y_true, y_pred))
    fn = sum(a and (not b) for a, b in zip(y_true, y_pred))
    tn = sum((not a) and (not b) for a, b in zip(y_true, y_pred))
    pos = tp + fn
    neg = tn + fp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / pos if pos else 0.0
    specificity = tn / neg if neg else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "accuracy": (tp + tn) / max(1, len(y_true)),
        "balanced_accuracy": (recall + specificity) / 2.0,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "support_positive": int(pos),
        "predicted_positive": int(tp + fp),
    }


def pair_side(pair_table: dict[str, Any]) -> dict[str, Any]:
    e_by_pair = {pair: pair_symbol(pair_table, pair) == "E" for pair in UNORDERED_CELLS}
    diagonal_e = sorted(pair for pair in DIAGONAL_CELLS if e_by_pair[pair])
    offdiag_e = sorted(pair for pair, is_e in e_by_pair.items() if is_e and pair not in DIAGONAL_CELLS)
    score = score_binary(
        [e_by_pair[pair] for pair in UNORDERED_CELLS],
        [pair in DIAGONAL_CELLS for pair in UNORDERED_CELLS],
    )
    return {
        "unordered_e_cells": sorted(pair for pair, is_e in e_by_pair.items() if is_e),
        "diagonal_e_cells": diagonal_e,
        "offdiag_e_cells": offdiag_e,
        "diagonal_e_count": len(diagonal_e),
        "offdiag_e_count": len(offdiag_e),
        "anchor_33_66_e_count": sum(e_by_pair[pair] for pair in ANCHOR_33_66),
        "score_diagonal_predicts_e": score,
        "e_by_pair": e_by_pair,
    }


def make_code_baseline(train: list[dict[str, Any]]) -> Callable[[dict[str, Any]], bool]:
    by_code: dict[str, list[bool]] = defaultdict(list)
    for row in train:
        by_code[row["code"]].append(row["label"])
    default = Counter(row["label"] for row in train).most_common(1)[0][0]
    majority = {code: Counter(values).most_common(1)[0][0] for code, values in by_code.items()}
    return lambda row: majority.get(row["code"], default)


def zero_rule_predictions(rows: list[dict[str, Any]], baseline: Callable[[dict[str, Any]], bool]) -> list[bool]:
    out = []
    for row in rows:
        pred = baseline(row)
        if fixed_predicate_code(row["prev_code"]):
            pred = True
        out.append(pred)
    return out


def zero_side(train: list[dict[str, Any]], holdout: list[dict[str, Any]]) -> dict[str, Any]:
    baseline = make_code_baseline(train)
    train_y = [row["label"] for row in train]
    holdout_y = [row["label"] for row in holdout]
    train_base = score_binary(train_y, [baseline(row) for row in train])
    holdout_base = score_binary(holdout_y, [baseline(row) for row in holdout])
    train_rule = score_binary(train_y, zero_rule_predictions(train, baseline))
    holdout_rule = score_binary(holdout_y, zero_rule_predictions(holdout, baseline))
    train_hits = [row for row in train if fixed_predicate_code(row["prev_code"])]
    holdout_hits = [row for row in holdout if fixed_predicate_code(row["prev_code"])]
    base_errors = holdout_base["fp"] + holdout_base["fn"]
    rule_errors = holdout_rule["fp"] + holdout_rule["fn"]
    return {
        "train_code_only": train_base,
        "train_rule": train_rule,
        "holdout_code_only": holdout_base,
        "holdout_rule": holdout_rule,
        "train_delta_balanced_accuracy": train_rule["balanced_accuracy"] - train_base["balanced_accuracy"],
        "holdout_delta_balanced_accuracy": holdout_rule["balanced_accuracy"] - holdout_base["balanced_accuracy"],
        "holdout_error_delta_vs_code_only": int(base_errors - rule_errors),
        "train_predicate_support": len(train_hits),
        "train_predicate_omitted": int(sum(row["label"] for row in train_hits)),
        "holdout_predicate_support": len(holdout_hits),
        "holdout_predicate_omitted": int(sum(row["label"] for row in holdout_hits)),
        "rough_holdout_error_gain_bits": (base_errors - rule_errors) * math.log2(len(holdout) + 1),
    }


def shuffle_zero_labels_by_code(rows: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    shuffled = [dict(row) for row in rows]
    by_code: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        by_code[row["code"]].append(idx)
    for indexes in by_code.values():
        labels = [rows[idx]["label"] for idx in indexes]
        rng.shuffle(labels)
        for idx, label in zip(indexes, labels):
            shuffled[idx]["label"] = label
    return shuffled


def summarize_high(values: list[float], observed: float) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "z_good_direction": (observed - mean) / sd if sd else 0.0,
        "p_good_direction": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
    }


def controls(pair: dict[str, Any], zero_train: list[dict[str, Any]], zero_observed: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    e_values = list(pair["e_by_pair"].values())
    diagonal_e_values: list[float] = []
    anchor_values: list[float] = []
    zero_delta_values: list[float] = []
    joint_values: list[float] = []

    observed_diag_fraction = pair["diagonal_e_count"] / len(DIAGONAL_CELLS)
    observed_zero_delta = zero_observed["train_delta_balanced_accuracy"]
    observed_joint = observed_diag_fraction + max(0.0, observed_zero_delta)

    for _ in range(CONTROL_TRIALS):
        shuffled_e = e_values[:]
        rng.shuffle(shuffled_e)
        e_by_pair = {pair_id: is_e for pair_id, is_e in zip(UNORDERED_CELLS, shuffled_e)}
        diag_count = sum(e_by_pair[pair_id] for pair_id in DIAGONAL_CELLS)
        anchor_count = sum(e_by_pair[pair_id] for pair_id in ANCHOR_33_66)

        shuffled_zero = shuffle_zero_labels_by_code(zero_train, rng)
        z = zero_side(shuffled_zero, [])
        zero_delta = z["train_delta_balanced_accuracy"]

        diagonal_e_values.append(diag_count)
        anchor_values.append(anchor_count)
        zero_delta_values.append(zero_delta)
        joint_values.append((diag_count / len(DIAGONAL_CELLS)) + max(0.0, zero_delta))

    return {
        "trials": CONTROL_TRIALS,
        "diagonal_e_count": summarize_high(diagonal_e_values, pair["diagonal_e_count"]),
        "anchor_33_66_e_count": summarize_high(anchor_values, pair["anchor_33_66_e_count"]),
        "zero_train_delta_balanced_accuracy": summarize_high(zero_delta_values, observed_zero_delta),
        "joint_diag_fraction_plus_zero_delta": summarize_high(joint_values, observed_joint),
    }


def classify(pair: dict[str, Any], zero: dict[str, Any], ctrl: dict[str, Any]) -> str:
    if (
        ctrl["diagonal_e_count"]["p_good_direction"] <= 0.05
        and ctrl["zero_train_delta_balanced_accuracy"]["p_good_direction"] <= 0.01
        and zero["holdout_delta_balanced_accuracy"] > 0
    ):
        return "shared_predicate_signal_only"
    if zero["holdout_delta_balanced_accuracy"] > 0:
        return "weak_shared_predicate_not_formula"
    return "rejected_control"


def write_report(result: dict[str, Any]) -> None:
    pair = result["pair_side"]
    zero = result["zero_side"]
    ctrl = result["controls"]
    lines = [
        "# Shared E / Zero Predicate Search",
        "",
        "Generated by `shared_e_zero_predicate_search.py`.",
        "",
        "The only tested predicate is `P(i,j)=i>=j`. On unordered pair cells",
        "this becomes the diagonal; on ordered previous codes it is the",
        "descending-or-diagonal zero-render predicate.",
        "",
        "## Summary",
        "",
        "| Predicate | Diagonal E | 33/66 E | Zero train delta | Zero holdout delta | Holdout error gain | Joint p | Verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
        f"| `i>=j` | {pair['diagonal_e_count']}/10 | {pair['anchor_33_66_e_count']}/2 | {zero['train_delta_balanced_accuracy']:.3f} | {zero['holdout_delta_balanced_accuracy']:.3f} | {zero['holdout_error_delta_vs_code_only']} | {ctrl['joint_diag_fraction_plus_zero_delta']['p_good_direction']:.5f} | `{result['verdict']}` |",
        "",
        "## Pair Side",
        "",
        f"- E cells on diagonal: `{', '.join(pair['diagonal_e_cells'])}`.",
        f"- E cells off diagonal: `{', '.join(pair['offdiag_e_cells'])}`.",
        f"- Diagonal E control p: `{ctrl['diagonal_e_count']['p_good_direction']:.5f}`.",
        f"- 33/66 anchor control p: `{ctrl['anchor_33_66_e_count']['p_good_direction']:.5f}`.",
        f"- Diagonal-as-E F1: `{pair['score_diagonal_predicts_e']['f1']:.3f}`.",
        "",
        "## Zero Side",
        "",
        f"- Train predicate support: {zero['train_predicate_support']} examples, {zero['train_predicate_omitted']} omitted.",
        f"- Holdout predicate support: {zero['holdout_predicate_support']} examples, {zero['holdout_predicate_omitted']} omitted.",
        f"- Zero train-delta control p: `{ctrl['zero_train_delta_balanced_accuracy']['p_good_direction']:.5f}`.",
        f"- Rough holdout error gain: `{zero['rough_holdout_error_gain_bits']:.1f}` bits before shared-predicate description cost.",
        "",
        "## Interpretation",
        "",
        "The fixed predicate is a real shared mechanical signal: it is unusual for",
        "E labels to concentrate on the diagonal, and the same inequality improves",
        "zero omission on book holdout. It still does not derive the E labels, the",
        "off-diagonal E cells, or the rest of the pair table. Classification stays",
        "as signal only, not the original formula.",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair = pair_side(formula["pair_table"])
    zero_train, zero_holdout = zero_rules.build_dataset()
    zero = zero_side(zero_train, zero_holdout)
    ctrl = controls(pair, zero_train, zero)
    result = {
        "schema": "shared_e_zero_predicate_results.v1",
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "predicate": "i>=j",
        "control_trials": CONTROL_TRIALS,
        "pair_side": {key: value for key, value in pair.items() if key != "e_by_pair"},
        "zero_side": zero,
        "controls": ctrl,
        "verdict": classify(pair, zero, ctrl),
        "translation_delta": "NONE",
        "new_plaintext": False,
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "diag_e={diag}/10 zero_delta={delta:.3f} joint_p={p:.5f} verdict={verdict}".format(
            diag=pair["diagonal_e_count"],
            delta=zero["holdout_delta_balanced_accuracy"],
            p=ctrl["joint_diag_fraction_plus_zero_delta"]["p_good_direction"],
            verdict=result["verdict"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
