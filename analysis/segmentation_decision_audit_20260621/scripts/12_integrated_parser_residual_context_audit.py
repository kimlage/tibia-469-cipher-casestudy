from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
GATE111_SCRIPT = PREQ / "scripts" / "111_decoder_length_candidate_ambiguity_audit.py"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
TRACE_SCRIPT = HERE / "scripts" / "01_segmentation_decision_trace.py"
PEAK_STRENGTH = TEST_RESULTS / "11_integrated_parser_peak_strength_audit.json"

OUT_STEM = "12_integrated_parser_residual_context_audit"
SEED_BOOKS = list(range(10))
MIN_COPY_LEN = 5
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


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


def offset_rows(trace_module, emitted: str, target: str, start: int) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for offset in range(len(target) - start + 1):
        if start + offset >= len(target):
            max_copy_length = 0
        else:
            candidates = trace_module.candidate_sources_with_max(
                emitted + target[start : start + offset],
                target,
                start + offset,
            )
            max_copy_length = max(
                [row["max_length"] for row in candidates],
                default=0,
            )
        rows.append(
            {
                "offset": offset,
                "max_copy_length": max_copy_length,
                "total_advance": offset + max_copy_length,
            }
        )
    return rows


def predict_window5(rows: list[dict[str, int]]) -> dict[str, int] | None:
    for index, offset in enumerate(rows):
        if offset["max_copy_length"] < MIN_COPY_LEN:
            continue
        value = offset["max_copy_length"]
        if all(
            index + step >= len(rows)
            or rows[index + step]["max_copy_length"] <= value
            for step in range(1, 6)
        ):
            return {
                "offset": offset["offset"],
                "peak_len": offset["max_copy_length"],
                "total_advance": offset["total_advance"],
            }
    return None


def choose_copy(trace_module, emitted: str, target: str, pos: int) -> dict[str, int] | None:
    candidates = trace_module.candidate_sources_with_max(emitted, target, pos)
    if not candidates:
        return None
    max_length = max(row["max_length"] for row in candidates)
    source = min(row["source"] for row in candidates if row["max_length"] == max_length)
    return {"source": source, "length": max_length, "candidate_count": len(candidates)}


def normalized_projected_ops(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": row["type"],
            "target_start": int(row["target_start"]),
            "length": int(row["length"]),
            "source": row["source"],
        }
        for row in rows
    ]


def classify_diff(predicted: dict[str, Any] | None, stable: dict[str, Any] | None) -> str:
    if predicted is None:
        return "predicted_sequence_ended_early"
    if stable is None:
        return "predicted_extra_operation"
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


def parse_book_context_rows(
    trace_module,
    book: int,
    target: str,
    emitted: str,
    projected: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str, bool]:
    pos = 0
    op_index = 0
    rows: list[dict[str, Any]] = []
    previous_type = "BOS"
    previous_length = 0
    had_error = False
    while pos < len(target):
        rows_at_pos = offset_rows(trace_module, emitted, target, pos)
        peak = predict_window5(rows_at_pos)
        immediate_copy = choose_copy(trace_module, emitted, target, pos)
        stable_op = projected[op_index] if op_index < len(projected) else None
        if peak is None:
            predicted = {
                "type": "literal",
                "target_start": pos,
                "length": len(target) - pos,
                "source": None,
            }
        elif peak["offset"] > 0:
            predicted = {
                "type": "literal",
                "target_start": pos,
                "length": peak["offset"],
                "source": None,
            }
        else:
            copy = choose_copy(trace_module, emitted, target, pos)
            if copy is None:
                raise RuntimeError({"type": "peak_without_copy", "book": book, "pos": pos})
            predicted = {
                "type": "copy",
                "target_start": pos,
                "length": copy["length"],
                "source": copy["source"],
            }
        is_error = predicted != stable_op
        if not had_error:
            drift_class = None if not is_error else classify_diff(predicted, stable_op)
            rows.append(
                {
                    "book": book,
                    "op_index": op_index,
                    "target_start": pos,
                    "remaining": len(target) - pos,
                    "target_length": len(target),
                    "position_bucket": "start"
                    if pos == 0
                    else ("end" if len(target) - pos <= 20 else "middle"),
                    "previous_type": previous_type,
                    "previous_length": previous_length,
                    "predicted_type": predicted["type"],
                    "predicted_length": predicted["length"],
                    "predicted_source": predicted["source"],
                    "stable_type": None if stable_op is None else stable_op["type"],
                    "stable_length": None if stable_op is None else stable_op["length"],
                    "stable_source": None if stable_op is None else stable_op["source"],
                    "peak_offset": None if peak is None else peak["offset"],
                    "peak_len": 0 if peak is None else peak["peak_len"],
                    "peak_total_advance": 0 if peak is None else peak["total_advance"],
                    "immediate_copy_len": 0
                    if immediate_copy is None
                    else immediate_copy["length"],
                    "immediate_copy_candidate_count": 0
                    if immediate_copy is None
                    else immediate_copy["candidate_count"],
                    "is_error": is_error,
                    "drift_class": drift_class,
                }
            )
            if is_error:
                # Keep emitting the rest of this parsed book so later books see the
                # same parser state, but stop collecting aligned decision rows.
                had_error = True
        emitted += target[pos : pos + predicted["length"]]
        previous_type = predicted["type"]
        previous_length = predicted["length"]
        pos += predicted["length"]
        if not had_error:
            op_index += 1
    exact = (not had_error) and op_index == len(projected)
    if not had_error and not exact:
        rows.append(
            {
                "book": book,
                "op_index": op_index,
                "target_start": pos,
                "remaining": 0,
                "target_length": len(target),
                "position_bucket": "end",
                "previous_type": previous_type,
                "previous_length": previous_length,
                "predicted_type": None,
                "predicted_length": 0,
                "predicted_source": None,
                "stable_type": projected[op_index]["type"],
                "stable_length": projected[op_index]["length"],
                "stable_source": projected[op_index]["source"],
                "peak_offset": None,
                "peak_len": 0,
                "peak_total_advance": 0,
                "immediate_copy_len": 0,
                "immediate_copy_candidate_count": 0,
                "is_error": True,
                "drift_class": "predicted_sequence_ended_early",
            }
        )
        had_error = True
    return rows, emitted, exact


Predicate = tuple[str, Callable[[dict[str, Any]], bool]]


def make_predicates() -> list[Predicate]:
    predicates: list[Predicate] = []
    predicates.extend(
        [
            ("book_start", lambda row: row["target_start"] == 0),
            ("middle_position", lambda row: row["position_bucket"] == "middle"),
            ("end_position", lambda row: row["position_bucket"] == "end"),
            ("previous_literal", lambda row: row["previous_type"] == "literal"),
            ("previous_copy", lambda row: row["previous_type"] == "copy"),
            ("predicted_literal", lambda row: row["predicted_type"] == "literal"),
            ("predicted_copy", lambda row: row["predicted_type"] == "copy"),
            (
                "predicted_literal_after_copy",
                lambda row: row["predicted_type"] == "literal"
                and row["previous_type"] == "copy",
            ),
            (
                "predicted_copy_after_literal",
                lambda row: row["predicted_type"] == "copy"
                and row["previous_type"] == "literal",
            ),
            (
                "copy_available_at_literal",
                lambda row: row["predicted_type"] == "literal"
                and row["immediate_copy_len"] >= MIN_COPY_LEN,
            ),
        ]
    )
    for length in [1, 2, 3, 5, 8, 13, 21, 34]:
        predicates.append(
            (
                f"predicted_literal_len_le{length}",
                lambda row, length=length: row["predicted_type"] == "literal"
                and row["predicted_length"] <= length,
            )
        )
        predicates.append(
            (
                f"predicted_copy_len_le{length}",
                lambda row, length=length: row["predicted_type"] == "copy"
                and row["predicted_length"] <= length,
            )
        )
    for length in [5, 6, 8, 10, 13, 21, 34]:
        predicates.append(
            (
                f"immediate_copy_ge{length}",
                lambda row, length=length: row["immediate_copy_len"] >= length,
            )
        )
        predicates.append(
            (
                f"literal_with_immediate_copy_ge{length}",
                lambda row, length=length: row["predicted_type"] == "literal"
                and row["immediate_copy_len"] >= length,
            )
        )
        predicates.append(
            (
                f"peak_len_le{length}",
                lambda row, length=length: row["peak_len"] > 0
                and row["peak_len"] <= length,
            )
        )
    for offset in [0, 1, 2, 3, 5, 8, 13, 21, 34]:
        predicates.append(
            (
                f"peak_offset_le{offset}",
                lambda row, offset=offset: row["peak_offset"] is not None
                and row["peak_offset"] <= offset,
            )
        )
    for remaining in [10, 20, 34, 55, 89]:
        predicates.append(
            (
                f"remaining_le{remaining}",
                lambda row, remaining=remaining: row["remaining"] <= remaining,
            )
        )
    predicates.extend(
        [
            (
                "book_start_literal_with_immediate_copy",
                lambda row: row["target_start"] == 0
                and row["predicted_type"] == "literal"
                and row["immediate_copy_len"] >= MIN_COPY_LEN,
            ),
            (
                "internal_literal_with_short_predicted_len",
                lambda row: row["target_start"] > 0
                and row["predicted_type"] == "literal"
                and row["predicted_length"] <= 5,
            ),
            (
                "literal_under_8_after_copy",
                lambda row: row["previous_type"] == "copy"
                and row["predicted_type"] == "literal"
                and row["predicted_length"] <= 8,
            ),
        ]
    )
    return predicates


def score_predicate(rows: list[dict[str, Any]], name: str, pred: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
    tp = fp = fn = tn = 0
    flagged_books: set[int] = set()
    error_books: set[int] = set()
    for row in rows:
        actual = bool(row["is_error"])
        flagged = bool(pred(row))
        if flagged:
            flagged_books.add(row["book"])
        if actual:
            error_books.add(row["book"])
        if actual and flagged:
            tp += 1
        elif not actual and flagged:
            fp += 1
        elif actual and not flagged:
            fn += 1
        else:
            tn += 1
    precision = None if tp + fp == 0 else tp / (tp + fp)
    recall = None if tp + fn == 0 else tp / (tp + fn)
    return {
        "predicate": name,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "flagged_books": sorted(flagged_books),
        "error_books": sorted(error_books),
        "flagged_error_books": sorted(flagged_books & error_books),
        "flagged_clean_books": sorted(flagged_books - error_books),
    }


def score_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [score_predicate(rows, name, pred) for name, pred in make_predicates()]


def prequential_selection(rows: list[dict[str, Any]], predicates: list[Predicate]) -> list[dict[str, Any]]:
    result = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        train_scores = [score_predicate(train, name, pred) for name, pred in predicates]
        eligible = [row for row in train_scores if row["tp"] > 0]
        if not eligible:
            result.append(
                {
                    "cutoff_book": cutoff,
                    "selected_predicate": None,
                    "train_tp": 0,
                    "train_fp": 0,
                    "train_fn": sum(1 for row in train if row["is_error"]),
                    "train_precision": None,
                    "train_recall": None,
                    "test_tp": 0,
                    "test_fp": 0,
                    "test_fn": sum(1 for row in test if row["is_error"]),
                    "test_precision": None,
                    "test_recall": None,
                    "oracle_predicate": None,
                    "oracle_test_tp": 0,
                    "oracle_test_fp": 0,
                    "oracle_test_precision": None,
                    "selected_matches_oracle": False,
                }
            )
            continue
        selected = max(
            eligible,
            key=lambda row: (
                row["precision"] or 0.0,
                row["recall"] or 0.0,
                -row["fp"],
                row["tp"],
                row["predicate"],
            ),
        )
        pred = next(pred for name, pred in predicates if name == selected["predicate"])
        test_score = score_predicate(test, selected["predicate"], pred)
        oracle_scores = [score_predicate(test, name, pred) for name, pred in predicates]
        oracle_eligible = [row for row in oracle_scores if row["tp"] > 0]
        oracle = (
            max(
                oracle_eligible,
                key=lambda row: (
                    row["precision"] or 0.0,
                    row["recall"] or 0.0,
                    -row["fp"],
                    row["tp"],
                    row["predicate"],
                ),
            )
            if oracle_eligible
            else {
                "predicate": None,
                "tp": 0,
                "fp": 0,
                "precision": None,
            }
        )
        result.append(
            {
                "cutoff_book": cutoff,
                "selected_predicate": selected["predicate"],
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
                "oracle_predicate": oracle["predicate"],
                "oracle_test_tp": oracle["tp"],
                "oracle_test_fp": oracle["fp"],
                "oracle_test_precision": oracle["precision"],
                "selected_matches_oracle": (
                    test_score["tp"] == oracle["tp"]
                    and test_score["fp"] == oracle["fp"]
                ),
            }
        )
    return result


def make_context_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    trace_module = load_module("segmentation_trace_for_gate12", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate12", GATE111_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    stable_ops = trace_module.projected_ops_from_copy_rows(gate111.make_copy_rows(), books)
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in stable_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    emitted = "".join(books[book] for book in SEED_BOOKS)
    rows: list[dict[str, Any]] = []
    exact_books = []
    mismatch_books = []
    for book in range(10, 70):
        book_rows, emitted, exact = parse_book_context_rows(
            trace_module,
            book,
            books[book],
            emitted,
            normalized_projected_ops(stable_by_book.get(book, [])),
        )
        rows.extend(book_rows)
        if exact:
            exact_books.append(book)
        else:
            mismatch_books.append(book)
    return rows, {"exact_books": exact_books, "mismatch_books": mismatch_books}


def make_result() -> dict[str, Any]:
    peak = load_json(PEAK_STRENGTH)
    assert_boundary("integrated_parser_peak_strength_audit", peak)
    if peak["summary"]["best_exact_books"] != 48:
        raise RuntimeError("gate11 exact coverage changed")

    rows, book_summary = make_context_rows()
    predicates = make_predicates()
    scores = score_rows(rows)
    best = max(
        [row for row in scores if row["tp"] > 0],
        key=lambda row: (
            row["precision"] or 0.0,
            row["recall"] or 0.0,
            -row["fp"],
            row["tp"],
            row["predicate"],
        ),
    )
    preq = prequential_selection(rows, predicates)
    promotes_context_rule = (
        best["precision"] == 1.0
        and best["recall"] == 1.0
        and all(row["selected_matches_oracle"] for row in preq)
    )
    if promotes_context_rule:
        classification = "residual_context_rule_promoted_target_text_parser"
    elif (best["precision"] or 0.0) == 1.0 and (best["recall"] or 0.0) >= 0.5:
        classification = "residual_context_rule_weak_high_precision_not_promoted"
    else:
        classification = "residual_context_rule_rejected"
    class_counts = Counter(row["drift_class"] for row in rows if row["is_error"])

    return {
        "schema": "integrated_parser_residual_context_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "integrated_parser_peak_strength_audit": rel(PEAK_STRENGTH),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "declared_literal_windows_granted": False,
            "declared_copy_starts_granted": False,
            "source_free_digit_generator_emitted": False,
        },
        "summary": {
            "decision_rows": len(rows),
            "error_rows": sum(1 for row in rows if row["is_error"]),
            "exact_books": len(book_summary["exact_books"]),
            "mismatch_books": len(book_summary["mismatch_books"]),
            "mismatch_book_ids": book_summary["mismatch_books"],
            "drift_class_counts": dict(sorted(class_counts.items())),
            "predicate_count": len(predicates),
            "best_predicate": best,
            "prequential_cells": len(preq),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "promotes_context_rule": promotes_context_rule,
            "interpretation": (
                "Residual context predicates test whether a simple observable "
                "parser-state flag can identify the remaining first-drift decisions. "
                "A promotable correction must isolate the residuals without broad "
                "false positives and survive prefix selection."
            ),
        },
        "predicate_scoreboard": sorted(
            scores,
            key=lambda row: (
                -(row["precision"] or 0.0),
                -(row["recall"] or 0.0),
                row["fp"],
                -row["tp"],
                row["predicate"],
            ),
        )[:25],
        "error_rows": [row for row in rows if row["is_error"]],
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "integrated_parser_status": "not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def fmt_float(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    best = s["best_predicate"]
    lines = [
        "# Integrated Parser Residual Context Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The prior controls rejected immediate-copy and weak-peak fixes. This",
        "gate turns each aligned parser decision into observable context",
        "features and asks whether simple predicates can identify the first",
        "remaining drift decision without broad false positives.",
        "",
        "## Summary",
        "",
        f"- Decision rows: `{s['decision_rows']}`.",
        f"- Error rows: `{s['error_rows']}`.",
        f"- Exact books: `{s['exact_books']}/60`.",
        f"- Mismatch books: `{s['mismatch_book_ids']}`.",
        f"- Drift classes: `{s['drift_class_counts']}`.",
        f"- Predicate count: `{s['predicate_count']}`.",
        "",
        "## Best Predicate",
        "",
        f"- Predicate: `{best['predicate']}`.",
        f"- TP/FP/FN/TN: `{best['tp']}/{best['fp']}/{best['fn']}/{best['tn']}`.",
        f"- Precision: `{fmt_float(best['precision'])}`.",
        f"- Recall: `{fmt_float(best['recall'])}`.",
        f"- Flagged clean books: `{best['flagged_clean_books']}`.",
        "",
        "## Predicate Scoreboard",
        "",
        "| Predicate | TP | FP | FN | Precision | Recall |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["predicate_scoreboard"][:15]:
        lines.append(
            f"| `{row['predicate']}` | `{row['tp']}` | `{row['fp']}` | "
            f"`{row['fn']}` | `{fmt_float(row['precision'])}` | "
            f"`{fmt_float(row['recall'])}` |"
        )
    lines.extend(
        [
            "",
            "## Prequential Predicate Selection",
            "",
            "| Cutoff | Selected | Train TP/FP | Test TP/FP | Oracle | Oracle TP/FP |",
            "|---:|---|---:|---:|---|---:|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_predicate']}` | "
            f"`{row['train_tp']}/{row['train_fp']}` | "
            f"`{row['test_tp']}/{row['test_fp']}` | "
            f"`{row['oracle_predicate']}` | "
            f"`{row['oracle_test_tp']}/{row['oracle_test_fp']}` |"
        )
    lines.extend(
        [
            "",
            "## Residual Error Rows",
            "",
            "| Book | Op | Class | Context |",
            "|---:|---:|---|---|",
        ]
    )
    for row in result["error_rows"]:
        context = {
            "target_start": row["target_start"],
            "previous_type": row["previous_type"],
            "predicted_type": row["predicted_type"],
            "predicted_length": row["predicted_length"],
            "peak_offset": row["peak_offset"],
            "peak_len": row["peak_len"],
            "immediate_copy_len": row["immediate_copy_len"],
        }
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['drift_class']}` | "
            f"`{json.dumps(context, sort_keys=True)}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes context rule: `{s['promotes_context_rule']}`.",
            f"- {s['interpretation']}",
            "- The result remains target-text-aware and analysis-only.",
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
