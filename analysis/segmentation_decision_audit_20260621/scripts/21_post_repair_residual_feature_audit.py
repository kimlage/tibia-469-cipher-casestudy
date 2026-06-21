from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
GATE111_SCRIPT = PREQ / "scripts" / "111_decoder_length_candidate_ambiguity_audit.py"
TRACE_SCRIPT = HERE / "scripts" / "01_segmentation_decision_trace.py"
POLICY_DRIFT_SCRIPT = HERE / "scripts" / "09_integrated_parser_policy_and_drift_audit.py"
OBSERVABLE_REPAIR_SCRIPT = HERE / "scripts" / "17_observable_repair_policy_audit.py"
CONDITIONAL_REPAIR_SCRIPT = HERE / "scripts" / "18_conditional_repair_classifier_audit.py"
POST_REPAIR_ORACLE = TEST_RESULTS / "20_post_repair_residual_oracle_audit.json"

OUT_STEM = "21_post_repair_residual_feature_audit"
SEED_BOOKS = list(range(10))
ACTIVE_CLASSIFIER = "if_peak_len_le5_then_skip_to_next_peak_ge5"
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


def normalize_stable_ops(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": row["type"],
            "target_start": int(row["target_start"]),
            "length": int(row["length"]),
            "source": row["source"],
        }
        for row in rows
    ]


def op_equals(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left["type"] == right["type"]
        and int(left["target_start"]) == int(right["target_start"])
        and int(left["length"]) == int(right["length"])
        and left.get("source") == right.get("source")
    )


def classify_diff(predicted: dict[str, Any], stable: dict[str, Any]) -> str:
    if predicted["type"] == "literal" and stable["type"] == "literal":
        if predicted["length"] < stable["length"]:
            return "literal_understop"
        if predicted["length"] > stable["length"]:
            return "literal_overstop"
        return "literal_other_mismatch"
    if predicted["type"] == "literal" and stable["type"] == "copy":
        if predicted["target_start"] == 0:
            return "book_start_copy_missed_as_literal"
        return "internal_copy_missed_as_literal"
    if predicted["type"] == "copy" and stable["type"] == "literal":
        return "copy_started_inside_stable_literal"
    if predicted["type"] == "copy" and stable["type"] == "copy":
        if predicted["source"] == stable["source"] and predicted["length"] != stable["length"]:
            return "copy_length_drift_same_source"
        if predicted["length"] == stable["length"] and predicted["source"] != stable["source"]:
            return "copy_source_drift_same_length"
        return "copy_pair_drift"
    return "other_drift"


def active_decision(
    repair_module,
    conditional_module,
    trace_module,
    policy_module,
    predicates: dict[str, Callable[[dict[str, Any]], bool]],
    classifier: dict[str, Any],
    emitted: str,
    target: str,
    pos: int,
    previous_type: str,
    previous_length: int,
    op_index: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    baseline, context = repair_module.baseline_op(
        policy_module, trace_module, emitted, target, pos
    )
    baseline_row = conditional_module.context_row(
        target, pos, baseline, context, previous_type, previous_length, op_index
    )
    chosen = baseline
    reason = None
    active_applies = predicates[classifier["predicate"]](baseline_row)
    if active_applies:
        chosen, reason = repair_module.apply_repair_policy(
            policy_module,
            trace_module,
            emitted,
            target,
            pos,
            baseline,
            context,
            classifier["action"],
        )
    active_row = conditional_module.context_row(
        target, pos, chosen, context, previous_type, previous_length, op_index
    )
    features = dict(active_row)
    features.update(
        {
            "baseline_type": baseline["type"],
            "baseline_length": int(baseline["length"]),
            "baseline_source": baseline.get("source"),
            "active_type": chosen["type"],
            "active_length": int(chosen["length"]),
            "active_source": chosen.get("source"),
            "active_classifier_applied": bool(reason),
            "active_classifier_condition_true": bool(active_applies),
            "active_classifier_repair": reason,
            "predicted_stops_before_next_peak": (
                active_row["next_peak_offset"] is not None
                and active_row["next_peak_offset"] > active_row["predicted_length"]
            ),
            "immediate_copy_minus_predicted_length": (
                active_row["immediate_copy_len"] - active_row["predicted_length"]
            ),
            "next_peak_minus_predicted_length": (
                None
                if active_row["next_peak_offset"] is None
                else active_row["next_peak_offset"] - active_row["predicted_length"]
            ),
        }
    )
    return chosen, features


def make_base_predicates() -> list[Predicate]:
    predicates: list[Predicate] = [
        ("book_start", lambda row: row["target_start"] == 0),
        ("internal", lambda row: row["target_start"] > 0),
        ("position_middle", lambda row: row["position_bucket"] == "middle"),
        ("position_end", lambda row: row["position_bucket"] == "end"),
        ("previous_literal", lambda row: row["previous_type"] == "literal"),
        ("previous_copy", lambda row: row["previous_type"] == "copy"),
        ("active_literal", lambda row: row["active_type"] == "literal"),
        ("active_copy", lambda row: row["active_type"] == "copy"),
        ("baseline_literal", lambda row: row["baseline_type"] == "literal"),
        ("baseline_copy", lambda row: row["baseline_type"] == "copy"),
        (
            "active_literal_with_immediate_copy",
            lambda row: row["active_type"] == "literal"
            and row["immediate_copy_len"] >= 5,
        ),
        (
            "active_literal_stops_before_next_peak",
            lambda row: row["active_type"] == "literal"
            and row["predicted_stops_before_next_peak"],
        ),
        (
            "active_classifier_applied",
            lambda row: row["active_classifier_applied"],
        ),
        (
            "active_copy_after_literal",
            lambda row: row["active_type"] == "copy"
            and row["previous_type"] == "literal",
        ),
        (
            "active_literal_after_copy",
            lambda row: row["active_type"] == "literal"
            and row["previous_type"] == "copy",
        ),
    ]
    for value in [1, 2, 3, 5, 7, 8, 10, 13, 21, 34]:
        predicates.extend(
            [
                (
                    f"active_len_le{value}",
                    lambda row, value=value: row["active_length"] <= value,
                ),
                (
                    f"active_literal_len_le{value}",
                    lambda row, value=value: row["active_type"] == "literal"
                    and row["active_length"] <= value,
                ),
                (
                    f"active_copy_len_ge{value}",
                    lambda row, value=value: row["active_type"] == "copy"
                    and row["active_length"] >= value,
                ),
                (
                    f"immediate_copy_ge{value}",
                    lambda row, value=value: row["immediate_copy_len"] >= value,
                ),
                (
                    f"active_literal_immediate_copy_ge{value}",
                    lambda row, value=value: row["active_type"] == "literal"
                    and row["immediate_copy_len"] >= value,
                ),
                (
                    f"peak_len_le{value}",
                    lambda row, value=value: row["peak_len"] > 0
                    and row["peak_len"] <= value,
                ),
                (
                    f"next_peak_ge{value}",
                    lambda row, value=value: row["next_peak_len"] >= value,
                ),
            ]
        )
    for value in [10, 20, 40, 80]:
        predicates.append(
            (
                f"remaining_le{value}",
                lambda row, value=value: row["remaining"] <= value,
            )
        )
    return predicates


def make_predicates() -> list[Predicate]:
    base = make_base_predicates()
    predicates = list(base)
    base_by_name = {name: fn for name, fn in base}
    pair_names = [
        "book_start",
        "internal",
        "position_middle",
        "position_end",
        "previous_literal",
        "previous_copy",
        "active_literal",
        "active_copy",
        "active_literal_with_immediate_copy",
        "active_literal_stops_before_next_peak",
        "active_classifier_applied",
        "active_copy_after_literal",
        "active_literal_after_copy",
        "active_len_le5",
        "active_len_le8",
        "active_literal_len_le5",
        "active_literal_immediate_copy_ge5",
        "active_literal_immediate_copy_ge8",
        "immediate_copy_ge5",
        "immediate_copy_ge8",
        "immediate_copy_ge10",
        "peak_len_le5",
        "next_peak_ge5",
        "remaining_le20",
    ]
    for left_index, left_name in enumerate(pair_names):
        for right_name in pair_names[left_index + 1 :]:
            left = base_by_name[left_name]
            right = base_by_name[right_name]
            predicates.append(
                (
                    f"{left_name}__and__{right_name}",
                    lambda row, left=left, right=right: left(row) and right(row),
                )
            )
    return predicates


def collect_rows() -> dict[str, Any]:
    post_repair = load_json(POST_REPAIR_ORACLE)
    assert_boundary("post_repair_residual_oracle_audit", post_repair)
    if post_repair["summary"]["active_exact_books"] != 50:
        raise RuntimeError("gate21 expects the gate20 active parser at 50/60")

    trace_module = load_module("segmentation_trace_for_gate21", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate21", GATE111_SCRIPT)
    policy_module = load_module("policy_drift_for_gate21", POLICY_DRIFT_SCRIPT)
    repair_module = load_module("observable_repair_for_gate21", OBSERVABLE_REPAIR_SCRIPT)
    conditional_module = load_module("conditional_repair_for_gate21", CONDITIONAL_REPAIR_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    projected_ops = trace_module.projected_ops_from_copy_rows(
        gate111.make_copy_rows(), books
    )
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in projected_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    classifiers = {row["label"]: row for row in conditional_module.make_classifiers()}
    classifier = classifiers[ACTIVE_CLASSIFIER]
    active_predicates = {"always_false": lambda row: False}
    active_predicates.update({name: fn for name, fn in conditional_module.make_predicates()})

    clean_rows: list[dict[str, Any]] = []
    residual_rows: list[dict[str, Any]] = []
    exact_books: list[int] = []
    mismatch_books: list[int] = []
    emitted_prefix = "".join(books[book] for book in SEED_BOOKS)
    for book in range(10, 70):
        target = books[book]
        stable_ops = normalize_stable_ops(stable_by_book[book])
        emitted = emitted_prefix
        pos = 0
        previous_type = "BOS"
        previous_length = 0
        book_exact = True
        for stable_index, stable in enumerate(stable_ops):
            if stable["target_start"] != pos:
                raise RuntimeError(
                    {
                        "type": "stable_projection_desynced",
                        "book": book,
                        "pos": pos,
                        "stable": stable,
                    }
                )
            chosen, features = active_decision(
                repair_module,
                conditional_module,
                trace_module,
                policy_module,
                active_predicates,
                classifier,
                emitted,
                target,
                pos,
                previous_type,
                previous_length,
                stable_index,
            )
            row = {
                "book": book,
                "stable_index": stable_index,
                "target_start": pos,
                "features": features,
                "predicted": chosen,
                "stable_projection": stable,
                "stable_type": stable["type"],
                "stable_length": int(stable["length"]),
                "stable_source": stable.get("source"),
            }
            if op_equals(chosen, stable):
                clean_rows.append(row)
                emitted += target[pos : pos + int(chosen["length"])]
                previous_type = chosen["type"]
                previous_length = int(chosen["length"])
                pos += int(chosen["length"])
                continue
            row["drift_class"] = classify_diff(chosen, stable)
            residual_rows.append(row)
            mismatch_books.append(book)
            book_exact = False
            break
        if book_exact and pos == len(target):
            exact_books.append(book)
        emitted_prefix += target

    return {
        "clean_rows": clean_rows,
        "residual_rows": residual_rows,
        "exact_books": exact_books,
        "mismatch_books": mismatch_books,
    }


def score_predicate(
    label: str,
    fn: Callable[[dict[str, Any]], bool],
    positives: list[dict[str, Any]],
    negatives: list[dict[str, Any]],
) -> dict[str, Any]:
    tp_rows = [row for row in positives if fn(row["features"])]
    fn_rows = [row for row in positives if not fn(row["features"])]
    fp_rows = [row for row in negatives if fn(row["features"])]
    tn = len(negatives) - len(fp_rows)
    tp = len(tp_rows)
    fp = len(fp_rows)
    fn_count = len(fn_rows)
    precision = None if tp + fp == 0 else tp / (tp + fp)
    recall = None if not positives else tp / len(positives)
    f1 = (
        0.0
        if precision in {None, 0} or recall in {None, 0}
        else 2 * precision * recall / (precision + recall)
    )
    return {
        "label": label,
        "tp": tp,
        "fp": fp,
        "fn": fn_count,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "positive_books": [row["book"] for row in tp_rows],
        "false_positive_books_sample": sorted({row["book"] for row in fp_rows})[:20],
        "false_negative_books": [row["book"] for row in fn_rows],
    }


def select_score(scores: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        scores,
        key=lambda row: (
            row["f1"],
            row["precision"] or 0.0,
            row["recall"] or 0.0,
            -row["fp"],
            -row["label"].count("__and__"),
            row["label"],
        ),
    )


def prequential_rows(
    predicates: list[Predicate],
    positives: list[dict[str, Any]],
    negatives: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_pos = [row for row in positives if row["book"] < cutoff]
        train_neg = [row for row in negatives if row["book"] < cutoff]
        test_pos = [row for row in positives if row["book"] >= cutoff]
        test_neg = [row for row in negatives if row["book"] >= cutoff]
        train_scores = [
            score_predicate(label, fn, train_pos, train_neg)
            for label, fn in predicates
        ]
        selected = select_score(train_scores)
        selected_fn = dict(predicates)[selected["label"]]
        test_score = score_predicate(selected["label"], selected_fn, test_pos, test_neg)
        test_scores = [
            score_predicate(label, fn, test_pos, test_neg)
            for label, fn in predicates
        ]
        oracle = select_score(test_scores)
        rows.append(
            {
                "cutoff_book": cutoff,
                "selected_predicate": selected["label"],
                "train_tp": selected["tp"],
                "train_fp": selected["fp"],
                "train_fn": selected["fn"],
                "train_precision": selected["precision"],
                "train_recall": selected["recall"],
                "test_tp": test_score["tp"],
                "test_fp": test_score["fp"],
                "test_fn": test_score["fn"],
                "test_precision": test_score["precision"],
                "test_recall": test_score["recall"],
                "oracle_predicate": oracle["label"],
                "oracle_test_tp": oracle["tp"],
                "oracle_test_fp": oracle["fp"],
                "oracle_test_fn": oracle["fn"],
                "selected_matches_oracle_f1": test_score["f1"] == oracle["f1"],
            }
        )
    return rows


def public_residual_row(row: dict[str, Any]) -> dict[str, Any]:
    features = row["features"]
    keep = [
        "target_start",
        "position_bucket",
        "previous_type",
        "previous_length",
        "active_type",
        "active_length",
        "immediate_copy_len",
        "immediate_copy_candidate_count",
        "peak_offset",
        "peak_len",
        "next_peak_offset",
        "next_peak_len",
        "active_classifier_applied",
        "predicted_stops_before_next_peak",
    ]
    return {
        "book": row["book"],
        "stable_index": row["stable_index"],
        "drift_class": row["drift_class"],
        "predicted": row["predicted"],
        "stable_projection": row["stable_projection"],
        "features": {key: features[key] for key in keep},
    }


def make_result() -> dict[str, Any]:
    rows = collect_rows()
    predicates = make_predicates()
    residual_rows = rows["residual_rows"]
    clean_rows = rows["clean_rows"]
    scores = [
        score_predicate(label, fn, residual_rows, clean_rows)
        for label, fn in predicates
    ]
    top_scores = sorted(
        scores,
        key=lambda row: (
            -row["f1"],
            -(row["precision"] or 0.0),
            -(row["recall"] or 0.0),
            row["fp"],
            row["label"].count("__and__"),
            row["label"],
        ),
    )
    zero_fp_scores = [
        row for row in scores if row["fp"] == 0 and row["tp"] > 0
    ]
    zero_fp_scores.sort(
        key=lambda row: (
            -row["tp"],
            -row["f1"],
            row["label"].count("__and__"),
            row["label"],
        )
    )
    class_scores: dict[str, dict[str, Any]] = {}
    drift_counts = Counter(row["drift_class"] for row in residual_rows)
    for drift_class in sorted(drift_counts):
        positives = [row for row in residual_rows if row["drift_class"] == drift_class]
        negatives = clean_rows + [
            row for row in residual_rows if row["drift_class"] != drift_class
        ]
        drift_scores = [
            score_predicate(label, fn, positives, negatives)
            for label, fn in predicates
        ]
        class_scores[drift_class] = select_score(drift_scores)
    preq = prequential_rows(predicates, residual_rows, clean_rows)
    full_detector = next(
        (
            row
            for row in scores
            if row["tp"] == len(residual_rows) and row["fp"] == 0
        ),
        None,
    )
    preq_clean = all(row["test_fp"] == 0 for row in preq)
    preq_covers_all_test = all(row["test_fn"] == 0 for row in preq)
    promotes = full_detector is not None and preq_clean and preq_covers_all_test
    classification = (
        "post_repair_residual_feature_rule_promoted"
        if promotes
        else "post_repair_residual_feature_screen_rejected"
    )
    return {
        "schema": "post_repair_residual_feature_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "post_repair_residual_oracle_audit": rel(POST_REPAIR_ORACLE),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_label_only": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "active_classifier": ACTIVE_CLASSIFIER,
            "active_exact_books": len(rows["exact_books"]),
            "active_mismatch_books": rows["mismatch_books"],
            "residual_book_count": len(residual_rows),
            "clean_decision_control_count": len(clean_rows),
            "predicate_count": len(predicates),
            "residual_drift_classes": dict(sorted(drift_counts.items())),
            "best_overall_predicate": top_scores[0]["label"],
            "best_overall_tp_fp_fn": {
                "tp": top_scores[0]["tp"],
                "fp": top_scores[0]["fp"],
                "fn": top_scores[0]["fn"],
            },
            "best_zero_fp_predicate": None
            if not zero_fp_scores
            else zero_fp_scores[0]["label"],
            "best_zero_fp_tp": 0 if not zero_fp_scores else zero_fp_scores[0]["tp"],
            "full_zero_fp_detector": None
            if full_detector is None
            else full_detector["label"],
            "prequential_cells": len(preq),
            "prequential_zero_test_fp_cells": sum(1 for row in preq if row["test_fp"] == 0),
            "prequential_cover_all_test_residual_cells": sum(
                1 for row in preq if row["test_fn"] == 0
            ),
            "prequential_selected_matches_oracle_f1_cells": sum(
                1 for row in preq if row["selected_matches_oracle_f1"]
            ),
            "promotes_residual_feature_rule": promotes,
            "interpretation": (
                "Gate 21 treats the ten gate-20 first residual drifts as "
                "positives and all active-parser aligned decisions before any "
                "drift as negative controls. A feature rule is promotable only "
                "if it separates residuals without false positives and remains "
                "stable under prefix/holdout selection."
            ),
        },
        "top_predicate_scores": top_scores[:20],
        "zero_false_positive_scores": zero_fp_scores[:20],
        "best_by_drift_class": class_scores,
        "prequential_rows": preq,
        "residual_feature_rows": [public_residual_row(row) for row in residual_rows],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "residual_feature_screen_rejected"
            if not promotes
            else "residual_feature_rule_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Post-Repair Residual Feature Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 21 asks whether the gate-20 residual oracle map can be replaced",
        "by a non-oracle observable feature rule. The ten first residual drifts",
        "are positives; active-parser aligned decisions before any drift are",
        "negative controls.",
        "",
        "## Feature Screen",
        "",
        f"- Active classifier: `{s['active_classifier']}`.",
        f"- Active exact books: `{s['active_exact_books']}/60`.",
        f"- Residual books: `{s['active_mismatch_books']}`.",
        f"- Clean decision controls: `{s['clean_decision_control_count']}`.",
        f"- Predicates tested: `{s['predicate_count']}`.",
        f"- Residual drift classes: `{s['residual_drift_classes']}`.",
        "",
        "| Predicate | TP | FP | FN | Precision | Recall |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["top_predicate_scores"][:12]:
        precision = "None" if row["precision"] is None else f"{row['precision']:.3f}"
        recall = "None" if row["recall"] is None else f"{row['recall']:.3f}"
        lines.append(
            f"| `{row['label']}` | `{row['tp']}` | `{row['fp']}` | "
            f"`{row['fn']}` | `{precision}` | `{recall}` |"
        )
    lines.extend(
        [
            "",
            "## Zero-False-Positive Controls",
            "",
            f"- Best zero-FP predicate: `{s['best_zero_fp_predicate']}`.",
            f"- Best zero-FP TP: `{s['best_zero_fp_tp']}/{s['residual_book_count']}`.",
            f"- Full zero-FP detector: `{s['full_zero_fp_detector']}`.",
            "",
            "| Predicate | TP | Positive books |",
            "|---|---:|---|",
        ]
    )
    for row in result["zero_false_positive_scores"][:10]:
        lines.append(
            f"| `{row['label']}` | `{row['tp']}` | `{row['positive_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected predicate | Train TP/FP/FN | Test TP/FP/FN | Oracle predicate |",
            "|---:|---|---:|---:|---|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_predicate']}` | "
            f"`{row['train_tp']}/{row['train_fp']}/{row['train_fn']}` | "
            f"`{row['test_tp']}/{row['test_fp']}/{row['test_fn']}` | "
            f"`{row['oracle_predicate']}` |"
        )
    lines.extend(
        [
            "",
            "## Residual Feature Rows",
            "",
            "| Book | Class | Target | Active op | Stable op | Immediate copy | Peak/next peak |",
            "|---:|---|---:|---|---|---:|---|",
        ]
    )
    for row in result["residual_feature_rows"]:
        f = row["features"]
        active = row["predicted"]
        stable = row["stable_projection"]
        lines.append(
            f"| `{row['book']}` | `{row['drift_class']}` | `{f['target_start']}` | "
            f"`{active['type']}:{active['length']}` | "
            f"`{stable['type']}:{stable['length']}` | "
            f"`{f['immediate_copy_len']}` | "
            f"`{f['peak_len']}/{f['next_peak_len']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes residual feature rule: `{s['promotes_residual_feature_rule']}`.",
            f"- Prequential zero-test-FP cells: `{s['prequential_zero_test_fp_cells']}/{s['prequential_cells']}`.",
            f"- Prequential cover-all-test-residual cells: `{s['prequential_cover_all_test_residual_cells']}/{s['prequential_cells']}`.",
            f"- Prequential selected matches oracle-F1 cells: `{s['prequential_selected_matches_oracle_f1_cells']}/{s['prequential_cells']}`.",
            f"- {s['interpretation']}",
            "- No predicate separates all residual repairs from clean decisions.",
            "- The remaining blocker is still a richer path/state segmentation rule, not a simple residual feature flag.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
