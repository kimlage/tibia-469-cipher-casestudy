from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
GATE111_SCRIPT = PREQ / "scripts" / "111_decoder_length_candidate_ambiguity_audit.py"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
TRACE_SCRIPT = HERE / "scripts" / "01_segmentation_decision_trace.py"
OVERRIDE = TEST_RESULTS / "10_integrated_parser_override_audit.json"

OUT_STEM = "11_integrated_parser_peak_strength_audit"
SEED_BOOKS = list(range(10))
MIN_COPY_LEN = 5
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
PEAK_THRESHOLDS = list(range(5, 31))


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


def predict_window5_with_peak_threshold(
    rows: list[dict[str, int]], min_peak_len: int
) -> int | None:
    for index, offset in enumerate(rows):
        if offset["max_copy_length"] < max(MIN_COPY_LEN, min_peak_len):
            continue
        value = offset["max_copy_length"]
        if all(
            index + step >= len(rows)
            or rows[index + step]["max_copy_length"] <= value
            for step in range(1, 6)
        ):
            return offset["offset"]
    return None


def choose_copy(trace_module, emitted: str, target: str, pos: int) -> dict[str, int] | None:
    candidates = trace_module.candidate_sources_with_max(emitted, target, pos)
    if not candidates:
        return None
    max_length = max(row["max_length"] for row in candidates)
    source = min(row["source"] for row in candidates if row["max_length"] == max_length)
    return {"source": source, "length": max_length}


def parse_book(
    trace_module,
    target: str,
    emitted: str,
    min_peak_len: int,
) -> tuple[list[dict[str, Any]], str]:
    pos = 0
    ops: list[dict[str, Any]] = []
    while pos < len(target):
        rows = offset_rows(trace_module, emitted, target, pos)
        predicted_offset = predict_window5_with_peak_threshold(rows, min_peak_len)
        if predicted_offset is None:
            ops.append(
                {
                    "type": "literal",
                    "target_start": pos,
                    "length": len(target) - pos,
                    "source": None,
                }
            )
            emitted += target[pos:]
            pos = len(target)
            continue
        if predicted_offset > 0:
            ops.append(
                {
                    "type": "literal",
                    "target_start": pos,
                    "length": predicted_offset,
                    "source": None,
                }
            )
            emitted += target[pos : pos + predicted_offset]
            pos += predicted_offset
        copy = choose_copy(trace_module, emitted, target, pos)
        if copy is None:
            raise RuntimeError(
                {
                    "type": "predicted_offset_without_copy",
                    "target_start": pos,
                    "predicted_offset": predicted_offset,
                    "min_peak_len": min_peak_len,
                }
            )
        ops.append(
            {
                "type": "copy",
                "target_start": pos,
                "length": copy["length"],
                "source": copy["source"],
            }
        )
        emitted += target[pos : pos + copy["length"]]
        pos += copy["length"]
    return ops, emitted


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


def first_diff(
    predicted: list[dict[str, Any]], projected: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if predicted == projected:
        return None
    for index, (left, right) in enumerate(zip(predicted, projected)):
        if left != right:
            return {
                "index": index,
                "predicted": left,
                "stable_projection": right,
            }
    index = min(len(predicted), len(projected))
    return {
        "index": index,
        "predicted": None if index >= len(predicted) else predicted[index],
        "stable_projection": None if index >= len(projected) else projected[index],
    }


def classify_diff(diff: dict[str, Any]) -> str:
    predicted = diff["predicted"]
    stable = diff["stable_projection"]
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


def score_threshold(
    trace_module,
    books: dict[int, str],
    stable_by_book: dict[int, list[dict[str, Any]]],
    min_peak_len: int,
) -> dict[str, Any]:
    emitted = "".join(books[book] for book in SEED_BOOKS)
    exact_books: list[int] = []
    mismatch_rows: list[dict[str, Any]] = []
    predicted_copy_count = 0
    predicted_literal_count = 0
    predicted_literal_digits = 0
    stable_copy_count = 0
    stable_literal_count = 0
    stable_literal_digits = 0
    for book in range(10, 70):
        predicted, emitted = parse_book(trace_module, books[book], emitted, min_peak_len)
        projected = normalized_projected_ops(stable_by_book.get(book, []))
        predicted_copy_count += sum(1 for row in predicted if row["type"] == "copy")
        predicted_literal_count += sum(1 for row in predicted if row["type"] == "literal")
        predicted_literal_digits += sum(
            int(row["length"]) for row in predicted if row["type"] == "literal"
        )
        stable_copy_count += sum(1 for row in projected if row["type"] == "copy")
        stable_literal_count += sum(1 for row in projected if row["type"] == "literal")
        stable_literal_digits += sum(
            int(row["length"]) for row in projected if row["type"] == "literal"
        )
        diff = first_diff(predicted, projected)
        if diff is None:
            exact_books.append(book)
        else:
            mismatch_rows.append(
                {
                    "book": book,
                    "predicted_op_count": len(predicted),
                    "stable_projection_op_count": len(projected),
                    "first_diff": diff,
                    "drift_class": classify_diff(diff),
                }
            )
    class_counts = Counter(row["drift_class"] for row in mismatch_rows)
    return {
        "label": f"window5:min_peak_len{min_peak_len}",
        "min_peak_len": min_peak_len,
        "tested_books": 60,
        "exact_book_count": len(exact_books),
        "mismatch_book_count": len(mismatch_rows),
        "exact_books": exact_books,
        "mismatch_books": [row["book"] for row in mismatch_rows],
        "predicted_operation_count": predicted_copy_count + predicted_literal_count,
        "stable_projection_operation_count": stable_copy_count + stable_literal_count,
        "predicted_copy_count": predicted_copy_count,
        "stable_copy_count": stable_copy_count,
        "predicted_literal_gap_count": predicted_literal_count,
        "stable_literal_gap_count": stable_literal_count,
        "predicted_literal_digit_count": predicted_literal_digits,
        "stable_literal_digit_count": stable_literal_digits,
        "drift_class_counts": dict(sorted(class_counts.items())),
        "mismatch_rows": mismatch_rows,
    }


def prequential_threshold_selection(scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = set(range(10, cutoff))
        test_books = set(range(cutoff, 70))
        scored = []
        for score in scores:
            exact = set(score["exact_books"])
            train_hits = len(exact & train_books)
            test_hits = len(exact & test_books)
            scored.append(
                {
                    "label": score["label"],
                    "train_hits": train_hits,
                    "test_hits": test_hits,
                    "train_total": len(train_books),
                    "test_total": len(test_books),
                    "exact_book_count": score["exact_book_count"],
                }
            )
        selected = max(
            scored,
            key=lambda row: (
                row["train_hits"],
                row["test_hits"],
                row["exact_book_count"],
                row["label"],
            ),
        )
        oracle = max(scored, key=lambda row: (row["test_hits"], row["train_hits"]))
        rows.append(
            {
                "cutoff_book": cutoff,
                "selected_policy": selected["label"],
                "train_hits": selected["train_hits"],
                "train_total": selected["train_total"],
                "test_hits": selected["test_hits"],
                "test_total": selected["test_total"],
                "oracle_policy": oracle["label"],
                "oracle_test_hits": oracle["test_hits"],
                "selected_matches_oracle": selected["test_hits"] == oracle["test_hits"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    override = load_json(OVERRIDE)
    assert_boundary("integrated_parser_override_audit", override)
    if override["summary"]["best_policy"] != "window5:no_override":
        raise RuntimeError("gate10 best policy changed")

    trace_module = load_module("segmentation_trace_for_gate11", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate11", GATE111_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    stable_ops = trace_module.projected_ops_from_copy_rows(gate111.make_copy_rows(), books)
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in stable_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    scores = [
        score_threshold(trace_module, books, stable_by_book, threshold)
        for threshold in PEAK_THRESHOLDS
    ]
    baseline = next(row for row in scores if row["min_peak_len"] == 5)
    best = max(
        scores,
        key=lambda row: (
            row["exact_book_count"],
            -abs(row["predicted_literal_digit_count"] - row["stable_literal_digit_count"]),
            -abs(row["predicted_operation_count"] - row["stable_projection_operation_count"]),
            -row["min_peak_len"],
        ),
    )
    preq = prequential_threshold_selection(scores)
    prequential_stable = all(row["selected_matches_oracle"] for row in preq)
    exact_improvement = best["exact_book_count"] - baseline["exact_book_count"]
    promotes_peak_threshold = best["exact_book_count"] == 60 and prequential_stable
    if promotes_peak_threshold:
        classification = "integrated_peak_strength_policy_promoted_target_text_parser"
    elif exact_improvement > 0 and prequential_stable:
        classification = "integrated_peak_strength_policy_prequential_partial_not_promoted"
    elif exact_improvement > 0:
        classification = "integrated_peak_strength_policy_posthoc_improvement_not_promoted"
    else:
        classification = "integrated_peak_strength_policy_rejected"

    return {
        "schema": "integrated_parser_peak_strength_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "integrated_parser_override_audit": rel(OVERRIDE),
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
            "policy_count": len(scores),
            "baseline_policy": baseline["label"],
            "baseline_exact_books": baseline["exact_book_count"],
            "best_policy": best["label"],
            "best_exact_books": best["exact_book_count"],
            "best_mismatch_books": best["mismatch_books"],
            "best_drift_class_counts": best["drift_class_counts"],
            "exact_improvement_vs_baseline": exact_improvement,
            "prequential_cells": len(preq),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "prequential_stable": prequential_stable,
            "promotes_peak_threshold_policy": promotes_peak_threshold,
            "interpretation": (
                "Minimum peak strength tests whether residual literal understops "
                "come from accepting weak local peaks. The family is promoted only "
                "if it improves exact stable projection coverage under prefix "
                "selection without turning missed copies into new exceptions."
            ),
        },
        "policy_scoreboard": [
            {
                "label": row["label"],
                "min_peak_len": row["min_peak_len"],
                "exact_book_count": row["exact_book_count"],
                "mismatch_book_count": row["mismatch_book_count"],
                "predicted_operation_count": row["predicted_operation_count"],
                "predicted_literal_gap_count": row["predicted_literal_gap_count"],
                "predicted_literal_digit_count": row["predicted_literal_digit_count"],
                "drift_class_counts": row["drift_class_counts"],
            }
            for row in sorted(scores, key=lambda item: (-item["exact_book_count"], item["min_peak_len"]))
        ],
        "baseline_mismatch_rows": baseline["mismatch_rows"],
        "best_mismatch_rows": best["mismatch_rows"],
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "integrated_parser_status": "not_promoted",
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
        "# Integrated Parser Peak Strength Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 10 rejected immediate-copy overrides. This gate tests the",
        "opposite structural rescue: require a stronger accepted local peak",
        "before ending a literal run, to see whether residual literal",
        "understops are caused by weak early copy peaks.",
        "",
        "## Scoreboard",
        "",
        f"- Policies tested: `{s['policy_count']}`.",
        f"- Baseline `{s['baseline_policy']}` exact books: `{s['baseline_exact_books']}/60`.",
        f"- Best policy `{s['best_policy']}` exact books: `{s['best_exact_books']}/60`.",
        f"- Exact-book improvement vs baseline: `{s['exact_improvement_vs_baseline']}`.",
        "",
        "| Policy | Exact books | Literal gaps | Literal digits | Drift classes |",
        "|---|---:|---:|---:|---|",
    ]
    for row in result["policy_scoreboard"][:14]:
        lines.append(
            f"| `{row['label']}` | `{row['exact_book_count']}/60` | "
            f"`{row['predicted_literal_gap_count']}` | "
            f"`{row['predicted_literal_digit_count']}` | "
            f"`{row['drift_class_counts']}` |"
        )
    lines.extend(
        [
            "",
            "## Prequential Policy Selection",
            "",
            "| Cutoff | Selected | Train hits | Test hits | Oracle | Oracle test hits |",
            "|---:|---|---:|---:|---|---:|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_policy']}` | "
            f"`{row['train_hits']}/{row['train_total']}` | "
            f"`{row['test_hits']}/{row['test_total']}` | "
            f"`{row['oracle_policy']}` | `{row['oracle_test_hits']}/{row['test_total']}` |"
        )
    lines.extend(
        [
            "",
            "## Best Residual Drift",
            "",
            f"- Best mismatch books: `{s['best_mismatch_books']}`.",
            f"- Best drift classes: `{s['best_drift_class_counts']}`.",
            "",
            "| Book | Class | First diff |",
            "|---:|---|---|",
        ]
    )
    for row in result["best_mismatch_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['drift_class']}` | "
            f"`{json.dumps(row['first_diff'], sort_keys=True)}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes peak-strength policy: `{s['promotes_peak_threshold_policy']}`.",
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
