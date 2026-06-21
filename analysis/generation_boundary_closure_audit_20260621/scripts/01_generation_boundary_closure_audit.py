from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

SKELETON_GATE = (
    ROOT
    / "analysis"
    / "source_free_skeleton_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "02_source_free_skeleton_grammar_gate.json"
)
SKELETON_LEDGER = (
    ROOT
    / "analysis"
    / "source_free_skeleton_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_hard_boundary_ledger.json"
)
BOOK_ORDER_GATE = (
    ROOT
    / "analysis"
    / "book_order_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_book_order_dependency_gate.json"
)
BOOK_LENGTH_GATE = (
    ROOT
    / "analysis"
    / "book_length_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "02_book_length_generation_gate.json"
)
BOOK_LENGTH_LEDGER = (
    ROOT
    / "analysis"
    / "book_length_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_book_length_ledger.json"
)
LITERAL_GATE = (
    ROOT
    / "analysis"
    / "literal_payload_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "02_literal_payload_context_gate.json"
)
LITERAL_LEDGER = (
    ROOT
    / "analysis"
    / "literal_payload_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_literal_payload_ledger.json"
)
COPY_SOURCE_GATE = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "03_copy_source_context_gate.json"
)
COPY_SOURCE_POLICY = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "02_copy_source_policy_gate.json"
)
ROW0_COMPAT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "108_recent_gates_row0_compatibility_refresh.json"
)

OUT_STEM = "01_generation_boundary_closure_audit"


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
    skeleton_gate = load_json(SKELETON_GATE)
    skeleton_ledger = load_json(SKELETON_LEDGER)
    order_gate = load_json(BOOK_ORDER_GATE)
    length_gate = load_json(BOOK_LENGTH_GATE)
    length_ledger = load_json(BOOK_LENGTH_LEDGER)
    literal_gate = load_json(LITERAL_GATE)
    literal_ledger = load_json(LITERAL_LEDGER)
    source_gate = load_json(COPY_SOURCE_GATE)
    source_policy = load_json(COPY_SOURCE_POLICY)
    row0_compat = load_json(ROW0_COMPAT)
    for name, data in [
        ("skeleton_gate", skeleton_gate),
        ("skeleton_ledger", skeleton_ledger),
        ("book_order_gate", order_gate),
        ("book_length_gate", length_gate),
        ("book_length_ledger", length_ledger),
        ("literal_gate", literal_gate),
        ("literal_ledger", literal_ledger),
        ("copy_source_gate", source_gate),
        ("copy_source_policy", source_policy),
        ("row0_compat", row0_compat),
    ]:
        assert_boundary(name, data)

    hard = skeleton_ledger["summary"]
    length_summary = length_gate["summary"]
    literal_summary = literal_gate["summary"]
    source_summary = source_gate["summary"]
    order_summary = order_gate["summary"]

    dependency_rows = [
        {
            "dependency": "book_order",
            "status": "canonical_retained_not_generated",
            "count": 1,
            "best_generator_signal": "numeric survives full formula controls",
            "best_negative_control": "prefix order-specific cutoffs = 0; frontier perfect in 10 orders including 6 random",
            "promoted_generator": False,
        },
        {
            "dependency": "book_lengths",
            "status": "declared_residuals",
            "count": length_summary["book_count"],
            "best_generator_signal": f"active residual ledger {length_ledger['summary']['raw_gamma_length_bits']} -> {length_ledger['summary']['active_signed_rice_length_bits']} bits",
            "best_negative_control": f"best source-free policy {length_summary['best_full_exact_lengths']}/{length_summary['book_count']} exact; holdout cover-all {length_summary['prequential_cover_all_cells']}/{length_summary['prequential_cells']}",
            "promoted_generator": False,
        },
        {
            "dependency": "operation_skeleton",
            "status": "atlas_retained",
            "count": hard["skeleton_atlas_records"],
            "best_generator_signal": "exact skeleton invariant across exposed-source policy/cutoff cases",
            "best_negative_control": f"best grammar {skeleton_gate['summary']['best_exact_books']}/{skeleton_gate['summary']['book_count']} books and {skeleton_gate['summary']['best_op_hits']}/{skeleton_gate['summary']['op_count']} ops",
            "promoted_generator": False,
        },
        {
            "dependency": "copy_sources",
            "status": "declared_after_skeleton_and_payload",
            "count": source_summary["copy_events"],
            "best_generator_signal": f"target-aware controls hit {source_policy['summary']['best_oracle_chunk_hits']}/{source_policy['summary']['copy_events']}",
            "best_negative_control": f"best decoder-visible policy {source_policy['summary']['best_decoder_chunk_hits']}/{source_policy['summary']['copy_events']}; context holdout cover-all {source_summary['prequential_cover_all_chunk_cells']}/{source_summary['prequential_cells']}",
            "promoted_generator": False,
        },
        {
            "dependency": "literal_payload",
            "status": "declared_after_skeleton",
            "count": literal_ledger["summary"]["literal_chunk_count"],
            "best_generator_signal": f"{literal_ledger['summary']['literal_digit_count']} digits across {literal_ledger['summary']['literal_chunk_count']} chunks; {literal_ledger['summary']['whole_chunk_seen_before_digits']} digits are in chunks seen before",
            "best_negative_control": f"paid context +{literal_summary['best_net_vs_raw_uniform_bits']:.3f} bits vs raw; holdout any-exact chunks {literal_summary['prequential_any_exact_chunk_cells']}/{literal_summary['prequential_cells']}",
            "promoted_generator": False,
        },
    ]
    promoted = [row for row in dependency_rows if row["promoted_generator"]]
    blocker_rank = [
        "operation_skeleton",
        "book_lengths",
        "literal_payload",
        "copy_sources",
        "book_order",
    ]
    classification = (
        "generation_boundary_has_promoted_generator"
        if promoted
        else "generation_boundary_open_no_generator_promoted"
    )
    total_materialized_units = (
        1
        + int(length_summary["book_count"])
        + int(hard["skeleton_atlas_records"])
        + int(source_summary["copy_events"])
        + int(literal_ledger["summary"]["literal_chunk_count"])
    )
    return {
        "schema": "generation_boundary_closure_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "skeleton_ledger": rel(SKELETON_LEDGER),
            "skeleton_gate": rel(SKELETON_GATE),
            "book_order_gate": rel(BOOK_ORDER_GATE),
            "book_length_gate": rel(BOOK_LENGTH_GATE),
            "literal_gate": rel(LITERAL_GATE),
            "copy_source_gate": rel(COPY_SOURCE_GATE),
            "row0_compatibility_refresh": rel(ROW0_COMPAT),
        },
        "scope": {
            "analysis_only": True,
            "consolidates_existing_generation_gates": True,
            "does_not_introduce_new_formula": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "dependency_count": len(dependency_rows),
            "promoted_generator_count": len(promoted),
            "total_materialized_units_floor": total_materialized_units,
            "materialized_unit_definition": "book_order + 70 book lengths + 261 skeleton records + 208 source fields + 53 literal chunks",
            "book_order_status": order_gate["decision"]["book_order_status"],
            "book_length_status": length_gate["decision"]["book_length_status"],
            "skeleton_status": skeleton_gate["decision"]["generation_explanation_status"],
            "copy_source_status": source_gate["decision"]["copy_source_status"],
            "literal_payload_status": literal_gate["decision"]["literal_payload_status"],
            "row0_status": "unchanged_exogenous",
            "compression_bound_status": "unchanged_8154_676268",
            "next_blocker": blocker_rank[0],
            "blocker_rank": blocker_rank,
            "interpretation": (
                "The current work has a robust parser/atlas boundary, not a "
                "source-free generator. The exact operation skeleton remains the "
                "first blocker; book lengths, literal payload, and copy sources "
                "remain declared dependencies even after their local gates."
            ),
        },
        "dependency_rows": dependency_rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "next_work_status": "derive_operation_skeleton_or_find_stronger_target_stream_account",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    lines = [
        "# Generation Boundary Closure Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Consolidate the recent analysis-only generation gates into one current",
        "boundary ledger: what is generated, what remains declared, and what the",
        "next real blocker is.",
        "",
        "## Summary",
        "",
        f"- Dependencies consolidated: `{s['dependency_count']}`.",
        f"- Promoted generators: `{s['promoted_generator_count']}`.",
        f"- Materialized unit floor: `{s['total_materialized_units_floor']}`.",
        f"- Unit definition: {s['materialized_unit_definition']}.",
        f"- Next blocker: `{s['next_blocker']}`.",
        f"- Compression bound: `{s['compression_bound_status']}`.",
        f"- Row0: `{s['row0_status']}`.",
        "",
        "## Dependency Ledger",
        "",
        "| Dependency | Status | Count | Best signal | Negative control |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in result["dependency_rows"]:
        lines.append(
            f"| `{row['dependency']}` | `{row['status']}` | `{row['count']}` | "
            f"{row['best_generator_signal']} | {row['best_negative_control']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- {s['interpretation']}",
            "- Do not count further compression micro-sweeps as progress unless they remove one of the declared dependencies above or generalize under holdout.",
            "- The next constructive path is deriving the operation skeleton or finding a stronger target-stream account that removes the need to materialize it.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
