from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PREQ_RESULTS = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621" / "reports" / "test_results"
GATE98 = PREQ_RESULTS / "98_full_source_exact_skeleton_invariance.json"
GATE99 = PREQ_RESULTS / "99_exact_skeleton_dependency_ledger.json"

OUT_STEM = "01_hard_boundary_ledger"


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
    gate98 = load_json(GATE98)
    gate99 = load_json(GATE99)
    assert_boundary("full_source_exact_skeleton_invariance", gate98)
    assert_boundary("exact_skeleton_dependency_ledger", gate99)
    if gate98["classification"] != "source_free_skeleton_exactly_invariant":
        raise RuntimeError("gate98 must prove exact skeleton invariance")
    if gate99["classification"] != "exact_skeleton_dependency_ledger_atlas_only":
        raise RuntimeError("gate99 must leave skeleton as atlas-only")

    skeleton = gate99["exact_skeleton_dependency_counts"]
    residual = gate99["residual_dependencies"]
    summary = {
        "skeleton_atlas_records": int(skeleton["atlas_operation_skeleton_records"]),
        "copy_source_fields": int(skeleton["external_copy_source_fields"]),
        "literal_payload_chunks": int(skeleton["external_literal_payload_chunks"]),
        "literal_payload_digits": int(skeleton["external_literal_payload_digits"]),
        "external_dependency_fields_after_skeleton": int(
            skeleton["external_dependency_fields_after_skeleton"]
        ),
        "total_materialized_records_after_skeleton": int(
            skeleton["total_materialized_records_after_skeleton"]
        ),
        "copied_digits": int(residual["copied_digits"]),
        "seed_books_external": list(residual["seed_books_external"]),
        "row0_unchanged": True,
        "compression_bound_changed": False,
        "promotes_generator": False,
    }
    return {
        "schema": "hard_boundary_ledger.v1",
        "classification": "hard_boundary_ledger_audit_only",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "exact_skeleton_invariance": rel(GATE98),
            "exact_skeleton_dependency_ledger": rel(GATE99),
        },
        "scope": {
            "analysis_only": True,
            "freezes_remaining_dependencies": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": summary,
        "remaining_dependencies": {
            "skeleton_atlas": {
                "records": summary["skeleton_atlas_records"],
                "status": "materialized_atlas_not_generator",
                "next_test": "source_free_skeleton_grammar",
            },
            "copy_source_fields": {
                "records": summary["copy_source_fields"],
                "status": "external_after_skeleton",
                "priority": "secondary_after_skeleton_generation",
            },
            "literal_payload": {
                "chunks": summary["literal_payload_chunks"],
                "digits": summary["literal_payload_digits"],
                "status": "external_payload_after_skeleton",
                "priority": "parallel_payload_generation_audit",
            },
            "seed_payload": {
                "books": summary["seed_books_external"],
                "status": "external_operational_seed_context",
            },
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "hard_boundary_frozen_atlas_not_generator",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Hard Boundary Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Freeze the exact remaining dependencies after the source-free skeleton",
        "invariance result. This is the boundary for future generator work.",
        "",
        "## Ledger",
        "",
        f"- Skeleton atlas records: `{s['skeleton_atlas_records']}`.",
        f"- Copy-source fields: `{s['copy_source_fields']}`.",
        f"- Literal payload chunks/digits: `{s['literal_payload_chunks']}` / `{s['literal_payload_digits']}`.",
        f"- External dependency fields after skeleton: `{s['external_dependency_fields_after_skeleton']}`.",
        f"- Total materialized records after skeleton: `{s['total_materialized_records_after_skeleton']}`.",
        f"- Copied digits covered by skeleton copies: `{s['copied_digits']}`.",
        f"- Seed books external: `{s['seed_books_external']}`.",
        "",
        "## Decision",
        "",
        "- The next main test is skeleton generation, not source-choice selection.",
        "- Copy source and literal payload remain external after the skeleton.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
