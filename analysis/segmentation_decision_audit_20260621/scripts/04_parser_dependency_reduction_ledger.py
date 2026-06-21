from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
GATE99 = PREQ / "reports" / "test_results" / "99_exact_skeleton_dependency_ledger.json"
GATE111_SCRIPT = PREQ / "scripts" / "111_decoder_length_candidate_ambiguity_audit.py"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
TRACE = TEST_RESULTS / "01_segmentation_decision_trace.json"
STRUCTURAL = TEST_RESULTS / "02_structural_segmentation_hypothesis_audit.json"
TRACE_SCRIPT = HERE / "scripts" / "01_segmentation_decision_trace.py"

OUT_STEM = "04_parser_dependency_reduction_ledger"
MIN_COPY_LEN = 5
SEED_BOOKS = list(range(10))


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


def greedy_book_ops(target: str, emitted: str, trace_module) -> tuple[list[dict[str, Any]], str]:
    pos = 0
    ops: list[dict[str, Any]] = []
    while pos < len(target):
        candidates = trace_module.candidate_sources_with_max(emitted, target, pos)
        if candidates:
            max_length = max(row["max_length"] for row in candidates)
            source = min(
                row["source"] for row in candidates if row["max_length"] == max_length
            )
            ops.append(
                {
                    "type": "copy",
                    "target_start": pos,
                    "length": max_length,
                    "source": source,
                }
            )
            emitted += target[pos : pos + max_length]
            pos += max_length
            continue

        start = pos
        pos += 1
        while pos < len(target):
            provisional = emitted + target[start:pos]
            if trace_module.candidate_sources_with_max(provisional, target, pos):
                break
            pos += 1
        ops.append(
            {
                "type": "literal",
                "target_start": start,
                "length": pos - start,
                "source": None,
            }
        )
        emitted += target[start:pos]
    return ops, emitted


def full_greedy_parser_control() -> dict[str, Any]:
    trace_module = load_module("segmentation_trace_for_gate04", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate04", GATE111_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    stable_ops = trace_module.projected_ops_from_copy_rows(gate111.make_copy_rows(), books)
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in stable_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    emitted = "".join(books[book] for book in SEED_BOOKS)
    exact_books: list[int] = []
    mismatch_rows: list[dict[str, Any]] = []
    for book in range(10, 70):
        greedy_ops, emitted = greedy_book_ops(books[book], emitted, trace_module)
        projected = [
            {
                "type": op["type"],
                "target_start": int(op["target_start"]),
                "length": int(op["length"]),
                "source": op["source"],
            }
            for op in stable_by_book.get(book, [])
        ]
        if greedy_ops == projected:
            exact_books.append(book)
            continue
        first_diff = None
        for index, (greedy, stable) in enumerate(zip(greedy_ops, projected)):
            if greedy != stable:
                first_diff = {
                    "index": index,
                    "greedy": greedy,
                    "stable": stable,
                }
                break
        if first_diff is None:
            first_diff = {
                "index": min(len(greedy_ops), len(projected)),
                "greedy": None if len(greedy_ops) <= len(projected) else greedy_ops[min(len(greedy_ops), len(projected))],
                "stable": None if len(projected) <= len(greedy_ops) else projected[min(len(greedy_ops), len(projected))],
            }
        mismatch_rows.append(
            {
                "book": book,
                "greedy_op_count": len(greedy_ops),
                "stable_projection_op_count": len(projected),
                "first_diff": first_diff,
            }
        )
    return {
        "tested_books": 60,
        "exact_book_count": len(exact_books),
        "mismatch_book_count": len(mismatch_rows),
        "exact_books": exact_books,
        "mismatch_books": [row["book"] for row in mismatch_rows],
        "sample_mismatches": mismatch_rows[:12],
    }


def make_result() -> dict[str, Any]:
    gate99 = load_json(GATE99)
    trace = load_json(TRACE)
    structural = load_json(STRUCTURAL)
    for name, data in [
        ("exact_skeleton_dependency_ledger", gate99),
        ("segmentation_decision_trace", trace),
        ("structural_segmentation_hypothesis", structural),
    ]:
        assert_boundary(name, data)

    ts = trace["summary"]
    ss = structural["summary"]
    if ss["target_text_global_longest_pair_hits"] != 207:
        raise RuntimeError("structural segmentation result changed")

    full_greedy = full_greedy_parser_control()

    baseline_total = int(gate99["summary"]["skeleton_total_materialized_records"])
    baseline_skeleton_records = int(gate99["summary"]["skeleton_atlas_records"])
    baseline_copy_source_fields = int(gate99["summary"]["copy_items"])
    baseline_literal_chunks = int(gate99["summary"]["literal_runs"])

    stable_projection_records = int(ts["stable_projection_operation_count"])
    stable_literal_chunks = int(ts["stable_projection_literal_gap_count"])
    parser_rule_records = 1
    copy_exception_records = int(
        ss["target_text_global_longest_pair_total"]
        - ss["target_text_global_longest_pair_hits"]
    )
    target_text_parser_total = (
        stable_projection_records
        + stable_literal_chunks
        + parser_rule_records
        + copy_exception_records
    )
    removed_copy_pair_fields = ss["target_text_global_longest_pair_hits"] * 2
    retained_copy_pair_fields = copy_exception_records * 2

    return {
        "schema": "parser_dependency_reduction_ledger.v1",
        "classification": "conditional_parser_dependency_reduction_not_source_free_generator",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "exact_skeleton_dependency_ledger": rel(GATE99),
            "segmentation_decision_trace": rel(TRACE),
            "structural_segmentation_hypothesis_audit": rel(STRUCTURAL),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_generator_emitted": False,
        },
        "ledger": {
            "baseline_exact_skeleton": {
                "skeleton_atlas_records": baseline_skeleton_records,
                "copy_source_fields": baseline_copy_source_fields,
                "literal_payload_chunks": baseline_literal_chunks,
                "total_materialized_records": baseline_total,
            },
            "target_text_parser_projection": {
                "stable_projection_operation_records": stable_projection_records,
                "literal_payload_chunks": stable_literal_chunks,
                "parser_rule_records": parser_rule_records,
                "copy_exception_records": copy_exception_records,
                "total_materialized_records": target_text_parser_total,
            },
            "delta_vs_exact_skeleton": {
                "materialized_record_delta": target_text_parser_total - baseline_total,
                "copy_pair_fields_removed_conditionally": removed_copy_pair_fields,
                "copy_pair_fields_retained_as_exceptions": retained_copy_pair_fields,
                "literal_chunk_delta": stable_literal_chunks - baseline_literal_chunks,
                "operation_record_delta": stable_projection_records
                - baseline_skeleton_records,
            },
        },
        "full_greedy_parser_control": full_greedy,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "conditional_parser_dependency_reduction",
            "target_text_parser_status": "copy_source_length_reduced_207_of_208_when_copy_starts_are_given",
            "source_free_parser_status": "not_promoted_full_greedy_exact_books_39_of_60",
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
    ledger = result["ledger"]
    base = ledger["baseline_exact_skeleton"]
    parser = ledger["target_text_parser_projection"]
    delta = ledger["delta_vs_exact_skeleton"]
    greedy = result["full_greedy_parser_control"]
    lines = [
        "# Parser Dependency Reduction Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This gate asks whether the segmentation parser clue can reduce declared",
        "`(source,length)` dependency records, and where that reduction stops.",
        "It does not change the compression bound and does not emit a source-free",
        "generator.",
        "",
        "## Ledger",
        "",
        "| Representation | Operation/skeleton records | Literal chunks | Copy/source exception records | Parser rule records | Total materialized records |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Exact skeleton ledger | `{base['skeleton_atlas_records']}` | `{base['literal_payload_chunks']}` | `{base['copy_source_fields']}` | `0` | `{base['total_materialized_records']}` |",
        f"| Target-text parser projection | `{parser['stable_projection_operation_records']}` | `{parser['literal_payload_chunks']}` | `{parser['copy_exception_records']}` | `{parser['parser_rule_records']}` | `{parser['total_materialized_records']}` |",
        "",
        "## Delta",
        "",
        f"- Materialized record delta vs exact skeleton: `{delta['materialized_record_delta']}`.",
        f"- Conditional copy `(source,length)` fields removed: `{delta['copy_pair_fields_removed_conditionally']}`.",
        f"- Copy `(source,length)` fields retained as exceptions: `{delta['copy_pair_fields_retained_as_exceptions']}`.",
        f"- Literal chunk delta: `{delta['literal_chunk_delta']}`.",
        f"- Operation record delta: `{delta['operation_record_delta']}`.",
        "",
        "## Full Greedy Parser Control",
        "",
        "Control parser: at each target position, if a prior match exists, choose",
        "the longest previous target match with earliest-source tie; otherwise emit",
        "literal digits until the next match becomes available.",
        "",
        f"- Exact books: `{greedy['exact_book_count']}/{greedy['tested_books']}`.",
        f"- Mismatch books: `{greedy['mismatch_book_count']}/{greedy['tested_books']}`.",
        f"- Mismatch book ids: `{greedy['mismatch_books']}`.",
        "",
        "## Decision",
        "",
        "- The parser rule conditionally removes most copy source/length declarations when target text and copy starts are granted.",
        "- It does not remove the segmentation/op-start atlas: the full greedy parser fails on `21/60` non-seed books.",
        "- The result is a genuine generation-explanation improvement, but only for target-text-aware parsing.",
        "- Source-free book generation is not promoted.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
