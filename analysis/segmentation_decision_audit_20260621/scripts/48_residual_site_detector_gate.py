from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE22_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
GATE47 = TEST_RESULTS / "47_branch_rank_exception_cost_gate.json"

OUT_STEM = "48_residual_site_detector_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


Predicate = tuple[str, Callable[[dict[str, Any]], bool]]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def sanitize_label(value: str) -> str:
    parts = [part for part in value.split("+") if part != "stable_projection_oracle"]
    return "+".join(parts) if parts else "unlabeled"


def op_key(op: dict[str, Any]) -> tuple[Any, ...]:
    return (op["type"], int(op["target_start"]), int(op["length"]), op.get("source"))


def branch_length(branch: dict[str, Any]) -> int:
    return int(branch["op"]["length"])


def copy_type(branch: dict[str, Any]) -> int:
    return 0 if branch["op"]["type"] == "copy" else 1


def literal_type(branch: dict[str, Any]) -> int:
    return 0 if branch["op"]["type"] == "literal" else 1


def label_bucket(branch: dict[str, Any], wanted: str) -> int:
    return 0 if wanted in sanitize_label(branch["label"]) else 1


def metrics(branch: dict[str, Any]) -> dict[str, Any]:
    return branch["metrics"]


def rankers() -> dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]]:
    tie = lambda b: (op_key(b["op"]), sanitize_label(b["label"]))
    return {
        "active_first": lambda b: (0 if b["is_active"] else 1, tie(b)),
        "copy_first_longest": lambda b: (copy_type(b), -branch_length(b), tie(b)),
        "copy_first_shortest": lambda b: (copy_type(b), branch_length(b), tie(b)),
        "literal_first_longest": lambda b: (literal_type(b), -branch_length(b), tie(b)),
        "literal_first_shortest": lambda b: (literal_type(b), branch_length(b), tie(b)),
        "longest_op": lambda b: (-branch_length(b), copy_type(b), tie(b)),
        "shortest_op": lambda b: (branch_length(b), copy_type(b), tie(b)),
        "immediate_copy_first": lambda b: (label_bucket(b, "immediate_copy"), -branch_length(b), tie(b)),
        "literal_stop_first": lambda b: (label_bucket(b, "literal_stop"), branch_length(b), tie(b)),
        "min_suffix_ops": lambda b: (
            metrics(b)["suffix_op_count"],
            metrics(b)["suffix_literal_digits"],
            -metrics(b)["suffix_copy_digits"],
            tie(b),
        ),
        "min_suffix_literals": lambda b: (
            metrics(b)["suffix_literal_digits"],
            metrics(b)["suffix_op_count"],
            -metrics(b)["suffix_copy_digits"],
            tie(b),
        ),
        "max_suffix_copy_digits": lambda b: (
            -metrics(b)["suffix_copy_digits"],
            metrics(b)["suffix_op_count"],
            metrics(b)["suffix_literal_digits"],
            tie(b),
        ),
        "max_suffix_copy_count": lambda b: (
            -metrics(b)["suffix_copy_count"],
            metrics(b)["suffix_op_count"],
            metrics(b)["suffix_literal_digits"],
            tie(b),
        ),
        "balanced_ops_literals": lambda b: (
            metrics(b)["suffix_op_count"] * 5 + metrics(b)["suffix_literal_digits"],
            -metrics(b)["suffix_copy_digits"],
            tie(b),
        ),
    }


def top_branch(decision: dict[str, Any], ranker: Callable[[dict[str, Any]], tuple[Any, ...]]):
    return min(decision["branches"], key=ranker)


def observable_features(decision: dict[str, Any]) -> dict[str, Any]:
    branches = decision["branches"]
    top_by_ranker = {
        name: top_branch(decision, ranker)
        for name, ranker in rankers().items()
        if branches
    }
    top_ops = {op_key(branch["op"]) for branch in top_by_ranker.values()}
    top_labels = {sanitize_label(branch["label"]) for branch in top_by_ranker.values()}
    active_top_count = sum(1 for branch in top_by_ranker.values() if branch["is_active"])
    nonactive_top_count = len(top_by_ranker) - active_top_count
    balanced = top_by_ranker.get("balanced_ops_literals")
    copy_lengths = [
        branch_length(branch) for branch in branches if branch["op"]["type"] == "copy"
    ]
    literal_lengths = [
        branch_length(branch) for branch in branches if branch["op"]["type"] == "literal"
    ]
    labels = [sanitize_label(branch["label"]) for branch in branches]
    return {
        "book": int(decision["book"]),
        "kind": decision["kind"],
        "is_residual": decision["kind"] == "residual_first_drift",
        "drift_class": decision["drift_class"],
        "branch_count": len(branches),
        "copy_branch_count": len(copy_lengths),
        "literal_branch_count": len(literal_lengths),
        "immediate_copy_branch_count": sum("immediate_copy" in label for label in labels),
        "literal_stop_branch_count": sum("literal_stop" in label for label in labels),
        "active_type": decision["active_op"]["type"],
        "active_length": int(decision["active_op"]["length"]),
        "active_is_copy": decision["active_op"]["type"] == "copy",
        "baseline_type": decision["baseline_op"]["type"],
        "baseline_length": int(decision["baseline_op"]["length"]),
        "active_repair_applied": decision["active_repair"] is not None,
        "ranker_disagreement_ops": len(top_ops),
        "ranker_disagreement_labels": len(top_labels),
        "active_top_count": active_top_count,
        "nonactive_top_count": nonactive_top_count,
        "balanced_top_is_active": None if balanced is None else balanced["is_active"],
        "balanced_top_type": None if balanced is None else balanced["op"]["type"],
        "balanced_top_length": None if balanced is None else int(balanced["op"]["length"]),
        "max_copy_length": max(copy_lengths) if copy_lengths else 0,
        "min_copy_length": min(copy_lengths) if copy_lengths else 0,
        "max_literal_length": max(literal_lengths) if literal_lengths else 0,
        "min_literal_length": min(literal_lengths) if literal_lengths else 0,
    }


def build_rows() -> list[dict[str, Any]]:
    gate22 = load_module("gate22_for_gate48", GATE22_SCRIPT)
    return [observable_features(row) for row in gate22.collect_decisions()["decisions"] if row["branches"]]


def make_predicates(rows: list[dict[str, Any]]) -> list[Predicate]:
    numeric_keys = [
        "branch_count",
        "copy_branch_count",
        "literal_branch_count",
        "immediate_copy_branch_count",
        "literal_stop_branch_count",
        "active_length",
        "baseline_length",
        "ranker_disagreement_ops",
        "ranker_disagreement_labels",
        "active_top_count",
        "nonactive_top_count",
        "balanced_top_length",
        "max_copy_length",
        "min_copy_length",
        "max_literal_length",
        "min_literal_length",
    ]
    categorical_keys = [
        "active_type",
        "baseline_type",
        "active_is_copy",
        "active_repair_applied",
        "balanced_top_is_active",
        "balanced_top_type",
    ]
    predicates: list[Predicate] = []
    for key in numeric_keys:
        values = sorted({row[key] for row in rows if row[key] is not None})
        for value in values:
            predicates.append((f"{key}_le_{value}", lambda row, key=key, value=value: row[key] is not None and row[key] <= value))
            predicates.append((f"{key}_ge_{value}", lambda row, key=key, value=value: row[key] is not None and row[key] >= value))
    for key in categorical_keys:
        for value in sorted({row[key] for row in rows}, key=repr):
            predicates.append((f"{key}_eq_{value}", lambda row, key=key, value=value: row[key] == value))
    return predicates


def score_predicate(rows: list[dict[str, Any]], predicate: Predicate) -> dict[str, Any]:
    name, fn = predicate
    tp = fp = fn_count = tn = 0
    positive_books = []
    false_books = []
    for row in rows:
        fired = fn(row)
        if row["is_residual"] and fired:
            tp += 1
            positive_books.append(row["book"])
        elif row["is_residual"] and not fired:
            fn_count += 1
        elif not row["is_residual"] and fired:
            fp += 1
            false_books.append(row["book"])
        else:
            tn += 1
    precision = 0.0 if tp + fp == 0 else tp / (tp + fp)
    recall = 0.0 if tp + fn_count == 0 else tp / (tp + fn_count)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {
        "predicate": name,
        "tp": tp,
        "fp": fp,
        "fn": fn_count,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "positive_books": sorted(set(positive_books)),
        "false_books_sample": sorted(set(false_books))[:20],
    }


def score_conjunction(
    rows: list[dict[str, Any]], left: Predicate, right: Predicate
) -> dict[str, Any]:
    name_l, fn_l = left
    name_r, fn_r = right
    return score_predicate(
        rows,
        (f"{name_l}__and__{name_r}", lambda row: fn_l(row) and fn_r(row)),
    )


def top_scores(rows: list[dict[str, Any]], predicates: list[Predicate]) -> list[dict[str, Any]]:
    singles = [score_predicate(rows, predicate) for predicate in predicates]
    candidate_preds = [
        predicates[index]
        for index, score in sorted(
            enumerate(singles),
            key=lambda item: (-item[1]["f1"], item[1]["fp"], -item[1]["tp"]),
        )[:80]
    ]
    pairs = []
    for i, left in enumerate(candidate_preds):
        for right in candidate_preds[i + 1 :]:
            pairs.append(score_conjunction(rows, left, right))
    return sorted(
        singles + pairs,
        key=lambda row: (-row["f1"], row["fp"], -row["tp"], row["predicate"]),
    )


def prequential(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        train_predicates = make_predicates(train)
        single_scores = [
            score_predicate(train, predicate) for predicate in train_predicates
        ]
        selected_index, selected = max(
            enumerate(single_scores),
            key=lambda item: (
                item[1]["f1"],
                -item[1]["fp"],
                item[1]["tp"],
                item[1]["predicate"],
            ),
        )
        test_score = score_predicate(test, train_predicates[selected_index])
        out.append(
            {
                "cutoff_book": cutoff,
                "selected_predicate": selected["predicate"],
                "train_tp_fp_fn": [selected["tp"], selected["fp"], selected["fn"]],
                "test_tp_fp_fn": [
                    test_score["tp"],
                    test_score["fp"],
                    test_score["fn"],
                ],
                "test_precision": test_score["precision"],
                "test_recall": test_score["recall"],
                "test_f1": test_score["f1"],
            }
        )
    return out


def make_result() -> dict[str, Any]:
    gate47 = load_json(GATE47)
    assert_boundary("branch_rank_exception_cost_gate", gate47)
    if gate47["classification"] != "branch_rank_exception_cost_rejected":
        raise RuntimeError("gate48 expects gate47 rank-cost rejection")

    rows = build_rows()
    predicates = make_predicates(rows)
    scores = top_scores(rows, predicates)
    best = scores[0]
    zero_fp = [row for row in scores if row["fp"] == 0]
    best_zero_fp = max(zero_fp, key=lambda row: (row["tp"], row["f1"], row["predicate"]))
    preq = prequential(rows)
    preq_with_residuals = [
        row for row in preq if row["test_tp_fp_fn"][0] + row["test_tp_fp_fn"][2] > 0
    ]
    promotes = (
        best["tp"] == sum(1 for row in rows if row["is_residual"])
        and best["fp"] == 0
        and all(row["test_tp_fp_fn"][2] == 0 and row["test_tp_fp_fn"][1] == 0 for row in preq)
    )
    classification = (
        "residual_site_detector_promoted"
        if promotes
        else "residual_site_detector_rejected"
    )
    return {
        "schema": "residual_site_detector_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "branch_rank_exception_cost_gate": rel(GATE47),
            "residual_branch_continuation_script": rel(GATE22_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_label_only": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "tests_residual_site_detector": True,
        },
        "summary": {
            "interpretation": (
                "This gate tests whether the residual sites needed by the "
                "gate-47 residual-gated ranker can be detected from observable "
                "branch ambiguity and ranker-disagreement features."
            ),
            "decision_count": len(rows),
            "residual_count": sum(1 for row in rows if row["is_residual"]),
            "clean_control_count": sum(1 for row in rows if not row["is_residual"]),
            "predicate_count": len(predicates),
            "scored_rule_count": len(scores),
            "best_predicate": best["predicate"],
            "best_tp": best["tp"],
            "best_fp": best["fp"],
            "best_fn": best["fn"],
            "best_precision": best["precision"],
            "best_recall": best["recall"],
            "best_zero_fp_predicate": best_zero_fp["predicate"],
            "best_zero_fp_tp": best_zero_fp["tp"],
            "prequential_cells_with_residuals": len(preq_with_residuals),
            "prequential_zero_fp_cells": sum(
                1 for row in preq_with_residuals if row["test_tp_fp_fn"][1] == 0
            ),
            "prequential_cover_all_residual_cells": sum(
                1 for row in preq_with_residuals if row["test_tp_fp_fn"][2] == 0
            ),
            "promotes_residual_site_detector": promotes,
        },
        "scoreboard": scores[:20],
        "best_zero_fp_score": best_zero_fp,
        "prequential_rows": preq,
        "feature_rows": rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "residual_site_detector_tested",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def md_table(rows: list[list[Any]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    scoreboard_rows = [
        [
            row["predicate"],
            row["tp"],
            row["fp"],
            row["fn"],
            f"{row['precision']:.3f}",
            f"{row['recall']:.3f}",
            f"{row['f1']:.3f}",
        ]
        for row in result["scoreboard"][:12]
    ]
    preq_rows = [
        [
            row["cutoff_book"],
            row["selected_predicate"],
            row["train_tp_fp_fn"],
            row["test_tp_fp_fn"],
            f"{row['test_f1']:.3f}",
        ]
        for row in result["prequential_rows"]
    ]
    body = f"""# Residual Site Detector Gate

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 48 tests the missing condition from gate 47: can the residual sites be
detected from observable branch ambiguity and ranker-disagreement features,
without granting a residual-site lookup?

## Summary

- Decisions scored: `{s['decision_count']}`.
- Residual sites: `{s['residual_count']}`.
- Clean controls: `{s['clean_control_count']}`.
- Predicates: `{s['predicate_count']}`.
- Scored single/pair rules: `{s['scored_rule_count']}`.
- Best predicate: `{s['best_predicate']}`.
- Best TP/FP/FN: `{s['best_tp']}/{s['best_fp']}/{s['best_fn']}`.
- Best precision/recall: `{s['best_precision']:.3f}` / `{s['best_recall']:.3f}`.
- Best zero-FP predicate: `{s['best_zero_fp_predicate']}`.
- Best zero-FP TP: `{s['best_zero_fp_tp']}`.
- Prequential cells with residuals: `{s['prequential_cells_with_residuals']}`.
- Prequential zero-FP cells: `{s['prequential_zero_fp_cells']}/{s['prequential_cells_with_residuals']}`.
- Prequential cover-all-residual cells: `{s['prequential_cover_all_residual_cells']}/{s['prequential_cells_with_residuals']}`.
- Promotes residual site detector: `{s['promotes_residual_site_detector']}`.

## Scoreboard

{md_table(scoreboard_rows, ['predicate', 'TP', 'FP', 'FN', 'precision', 'recall', 'F1'])}

## Prefix/Holdout

{md_table(preq_rows, ['cutoff', 'selected predicate', 'train TP/FP/FN', 'test TP/FP/FN', 'test F1'])}

## Decision

No residual-site detector is promoted. Observable branch ambiguity and ranker
disagreement do not identify the residual sites cleanly enough to make the
gate-47 residual-gated ranker source-free. The apparent residual-gated saving
therefore remains lookup-dependent.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
"""
    md_path.write_text(body, encoding="utf-8")
    print(json_path)
    print(md_path)


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
