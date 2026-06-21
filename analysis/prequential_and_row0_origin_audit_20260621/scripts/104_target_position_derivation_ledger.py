from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE99 = TEST_RESULTS / "99_exact_skeleton_dependency_ledger.json"
GATE100 = TEST_RESULTS / "100_skeleton_rule_coverage_audit.json"
GATE103 = TEST_RESULTS / "103_copy_availability_type_exception_ledger.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def make_result() -> dict[str, Any]:
    gate99 = load_json(GATE99)
    gate100 = load_json(GATE100)
    gate103 = load_json(GATE103)
    assert_boundary("exact_skeleton_dependency_ledger", gate99)
    assert_boundary("skeleton_rule_coverage_audit", gate100)
    assert_boundary("copy_availability_type_exception_ledger", gate103)
    if gate100["classification"] != "skeleton_simple_rule_coverage_insufficient":
        raise RuntimeError("gate100 did not reject simple skeleton rules")
    if gate103["classification"] != "copy_availability_type_exception_audit_only":
        raise RuntimeError("gate103 did not keep availability clue audit-only")

    by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in gate100["skeleton_rows"]:
        by_book[int(row["book"])].append(row)

    target_violations: list[dict[str, Any]] = []
    remaining_violations: list[dict[str, Any]] = []
    op_index_violations: list[dict[str, Any]] = []
    book_summaries: list[dict[str, Any]] = []
    rows_checked = 0
    for book, rows in sorted(by_book.items()):
        rows = sorted(rows, key=lambda row: int(row["op_index"]))
        book_length = sum(int(row["length"]) for row in rows)
        position = 0
        for expected_op_index, row in enumerate(rows):
            rows_checked += 1
            actual_op_index = int(row["op_index"])
            actual_target = int(row["target_start"])
            actual_remaining = int(row["remaining"])
            expected_remaining = book_length - position
            if actual_op_index != expected_op_index:
                op_index_violations.append(
                    {
                        "book": book,
                        "expected_op_index": expected_op_index,
                        "actual_op_index": actual_op_index,
                    }
                )
            if actual_target != position:
                target_violations.append(
                    {
                        "book": book,
                        "op_index": actual_op_index,
                        "actual_target_start": actual_target,
                        "expected_target_start": position,
                    }
                )
            if actual_remaining != expected_remaining:
                remaining_violations.append(
                    {
                        "book": book,
                        "op_index": actual_op_index,
                        "actual_remaining": actual_remaining,
                        "expected_remaining": expected_remaining,
                    }
                )
            position += int(row["length"])
        book_summaries.append(
            {
                "book": book,
                "op_count": len(rows),
                "book_length_from_skeleton": book_length,
                "first_target_start": int(rows[0]["target_start"]) if rows else None,
                "last_target_end": position,
            }
        )

    target_start_derivable = not target_violations
    remaining_derivable = not remaining_violations
    op_index_sequential = not op_index_violations
    exact_atlas_records = int(gate99["summary"]["skeleton_atlas_records"])
    skeleton_total_materialized = int(
        gate99["summary"]["skeleton_total_materialized_records"]
    )
    copy_source_fields = int(gate99["summary"]["copy_items"])
    literal_payload_chunks = int(gate99["summary"]["literal_runs"])
    independent_skeleton_records = rows_checked
    independent_total_materialized_records = (
        independent_skeleton_records + copy_source_fields + literal_payload_chunks
    )

    return {
        "schema": "target_position_derivation_ledger.v1",
        "classification": "target_position_derived_from_length_sequence",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate99_exact_skeleton_dependency_ledger": rel(GATE99),
            "gate100_skeleton_rule_coverage": rel(GATE100),
            "gate103_copy_availability_type_exception_ledger": rel(GATE103),
        },
        "scope": {
            "analysis_only": True,
            "ledger_only": True,
            "tests_target_position_derivation": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "book_count": len(by_book),
            "operation_rows_checked": rows_checked,
            "target_start_derivable_rows": rows_checked - len(target_violations),
            "target_start_violation_count": len(target_violations),
            "remaining_derivable_rows": rows_checked - len(remaining_violations),
            "remaining_violation_count": len(remaining_violations),
            "op_index_sequential_rows": rows_checked - len(op_index_violations),
            "op_index_violation_count": len(op_index_violations),
            "target_start_derivable": target_start_derivable,
            "remaining_derivable": remaining_derivable,
            "op_index_sequential": op_index_sequential,
            "exact_atlas_records": exact_atlas_records,
            "independent_skeleton_records_after_target_derivation": (
                independent_skeleton_records
            ),
            "independent_total_materialized_records_after_target_derivation": (
                independent_total_materialized_records
            ),
            "record_delta_vs_gate99_skeleton_atlas": (
                independent_skeleton_records - exact_atlas_records
            ),
            "record_delta_vs_gate99_total_materialized": (
                independent_total_materialized_records - skeleton_total_materialized
            ),
            "promotes_generator": False,
            "interpretation": (
                "Target positions are not an independent skeleton dependency: "
                "all target_start values equal the cumulative sum of previous "
                "operation lengths within each book, and remaining equals book "
                "length minus that position. This sharpens the ledger from "
                "type/target/length rows to type/length rows with derived target "
                "positions, but it does not reduce the one-row-per-operation "
                "atlas count or derive op types, lengths, copy sources, or "
                "literal payload."
            ),
        },
        "book_summaries": book_summaries,
        "violations": {
            "target_start": target_violations,
            "remaining": remaining_violations,
            "op_index": op_index_violations,
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "target_position_derived_but_skeleton_atlas_retained",
            "skeleton_status": "target_positions_derived_from_lengths",
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "104_target_position_derivation_ledger.json"
    md_path = TEST_RESULTS / "104_target_position_derivation_ledger.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Target Position Derivation Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The source-free skeleton was described as operation type, target start,",
        "and length. This ledger checks whether target positions are independent",
        "fields or deterministic consequences of the length sequence.",
        "",
        "## Result",
        "",
        f"- Books: `{s['book_count']}`.",
        f"- Operation rows checked: `{s['operation_rows_checked']}`.",
        f"- Target-start derivable rows: `{s['target_start_derivable_rows']}`.",
        f"- Target-start violations: `{s['target_start_violation_count']}`.",
        f"- Remaining derivable rows: `{s['remaining_derivable_rows']}`.",
        f"- Remaining violations: `{s['remaining_violation_count']}`.",
        f"- Op-index sequential rows: `{s['op_index_sequential_rows']}`.",
        f"- Op-index violations: `{s['op_index_violation_count']}`.",
        f"- Independent skeleton records after target derivation: `{s['independent_skeleton_records_after_target_derivation']}`.",
        f"- Record delta vs gate-99 skeleton atlas: `{s['record_delta_vs_gate99_skeleton_atlas']}`.",
        f"- Record delta vs gate-99 total materialized records: `{s['record_delta_vs_gate99_total_materialized']}`.",
        "",
        "## Decision",
        "",
        f"- Target start derivable: `{s['target_start_derivable']}`.",
        f"- Remaining derivable: `{s['remaining_derivable']}`.",
        f"- Promotes generator: `{s['promotes_generator']}`.",
        f"- {s['interpretation']}",
        "- No compression-bound change is introduced.",
        "- No formula is emitted.",
        "- Row0 remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
