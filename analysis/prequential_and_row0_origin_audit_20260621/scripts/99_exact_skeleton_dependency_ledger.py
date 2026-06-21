from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE71 = TEST_RESULTS / "71_final_formula_dependency_refresh_gate.json"
GATE87 = TEST_RESULTS / "87_stable_path_projection_boundary_audit.json"
GATE98 = TEST_RESULTS / "98_full_source_exact_skeleton_invariance.json"


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
    gate71 = load_json(GATE71)
    gate87 = load_json(GATE87)
    gate98 = load_json(GATE98)
    assert_boundary("final_formula_dependency_refresh_gate", gate71)
    assert_boundary("stable_path_projection_boundary_audit", gate87)
    assert_boundary("full_source_exact_skeleton_invariance", gate98)
    if gate98["classification"] != "source_free_skeleton_exactly_invariant":
        raise RuntimeError("gate98 did not prove exact source-free skeleton invariance")

    active = gate71["declared_dependency_counts"]
    prior_projection = gate87["dependency_counts"]
    skeleton = gate98["summary"]["skeleton_totals"]

    active_external_fields = (
        int(active["declared_literal_payload_fields"])
        + int(active["declared_copy_source_fields"])
        + int(active["declared_copy_length_fields"])
    )
    skeleton_atlas_records = int(skeleton["op_count"])
    skeleton_external_fields = int(skeleton["literal_runs"]) + int(skeleton["copy_items"])
    skeleton_total_materialized_records = skeleton_atlas_records + skeleton_external_fields

    family_delta = {
        "copy_items_delta_vs_active": int(skeleton["copy_items"])
        - int(active["declared_copy_source_fields"]),
        "literal_payload_chunk_delta_vs_active": int(skeleton["literal_runs"])
        - int(active["declared_literal_payload_fields"]),
        "external_field_delta_vs_active": skeleton_external_fields - active_external_fields,
        "total_materialized_record_delta_vs_active": (
            skeleton_total_materialized_records - active_external_fields
        ),
        "prior_projection_copy_source_field_delta": int(skeleton["copy_items"])
        - int(prior_projection["materialized_copy_source_fields"]),
        "prior_projection_literal_run_delta": int(skeleton["literal_runs"])
        - int(gate87["summary"]["canonical_literal_runs"]),
        "prior_projection_literal_digit_delta": int(skeleton["literal_digits"])
        - int(prior_projection["materialized_literal_payload_digit_fields"]),
    }

    residual_dependencies = {
        "skeleton_records": skeleton_atlas_records,
        "literal_payload_chunks": int(skeleton["literal_runs"]),
        "literal_payload_digits": int(skeleton["literal_digits"]),
        "copy_source_fields": int(skeleton["copy_items"]),
        "copied_digits": int(skeleton["copied_digits"]),
        "seed_books_external": list(gate87["target_text_blocker"]["seed_books_external"]),
        "target_text_required_for_literal_payload": True,
        "target_text_required_for_copy_source_choice": True,
        "decoder_can_emit_books_from_skeleton_without_payload_or_sources": False,
    }

    ledger_dependency_reduction = (
        gate98["summary"]["source_fields_removed_from_skeleton_atlas"]
        and not gate98["summary"]["source_fields_removed_from_decoder"]
    )
    promotes_generator = False
    classification = "exact_skeleton_dependency_ledger_atlas_only"

    return {
        "schema": "exact_skeleton_dependency_ledger.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate71_final_dependency_refresh": rel(GATE71),
            "gate87_stable_projection_boundary": rel(GATE87),
            "gate98_exact_skeleton_invariance": rel(GATE98),
        },
        "scope": {
            "analysis_only": True,
            "ledger_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "active_external_dependency_fields": active_external_fields,
            "skeleton_atlas_records": skeleton_atlas_records,
            "skeleton_external_dependency_fields": skeleton_external_fields,
            "skeleton_total_materialized_records": skeleton_total_materialized_records,
            "copy_items": int(skeleton["copy_items"]),
            "literal_runs": int(skeleton["literal_runs"]),
            "literal_digits": int(skeleton["literal_digits"]),
            "copied_digits": int(skeleton["copied_digits"]),
            "ledger_dependency_reduction": ledger_dependency_reduction,
            "promotes_generator": promotes_generator,
            "interpretation": (
                "The exact source-free skeleton moves operation type and length "
                "into a stable atlas, reducing the residual external field "
                "families to literal payload chunks and copy-source choices. "
                "Because the atlas itself is still materialized and source/"
                "payload fields remain external, this is a dependency ledger "
                "improvement rather than a generator promotion."
            ),
        },
        "active_formula_dependency_counts": active,
        "prior_projection_dependency_counts": prior_projection,
        "exact_skeleton_dependency_counts": {
            "atlas_operation_skeleton_records": skeleton_atlas_records,
            "external_literal_payload_chunks": int(skeleton["literal_runs"]),
            "external_literal_payload_digits": int(skeleton["literal_digits"]),
            "external_copy_source_fields": int(skeleton["copy_items"]),
            "external_dependency_fields_after_skeleton": skeleton_external_fields,
            "total_materialized_records_after_skeleton": skeleton_total_materialized_records,
        },
        "family_deltas": family_delta,
        "residual_dependencies": residual_dependencies,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "dependency_ledger_improved_generator_not_promoted",
            "skeleton_status": "stable_source_free_atlas",
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "99_exact_skeleton_dependency_ledger.json"
    md_path = TEST_RESULTS / "99_exact_skeleton_dependency_ledger.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    residual = result["residual_dependencies"]
    delta = result["family_deltas"]
    lines = [
        "# Exact Skeleton Dependency Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 98 proved that the exact source-free operation skeleton is invariant.",
        "This ledger asks what dependency families that actually removes, and what",
        "still remains materialized before a decoder-side generator exists.",
        "",
        "## Ledger",
        "",
        f"- Active external dependency fields: `{s['active_external_dependency_fields']}`.",
        f"- Skeleton atlas records: `{s['skeleton_atlas_records']}`.",
        f"- External fields after skeleton: `{s['skeleton_external_dependency_fields']}`.",
        f"- Total materialized records after skeleton: `{s['skeleton_total_materialized_records']}`.",
        f"- Copy-source fields after skeleton: `{residual['copy_source_fields']}`.",
        f"- Literal payload chunks/digits after skeleton: `{residual['literal_payload_chunks']}` / `{residual['literal_payload_digits']}`.",
        f"- Copied digits covered by skeleton copies: `{residual['copied_digits']}`.",
        f"- External-field delta vs active: `{delta['external_field_delta_vs_active']}`.",
        f"- Total-materialized-record delta vs active: `{delta['total_materialized_record_delta_vs_active']}`.",
        "",
        "## Decision",
        "",
        f"- Ledger dependency reduction: `{s['ledger_dependency_reduction']}`.",
        f"- Promotes generator: `{s['promotes_generator']}`.",
        f"- Decoder can emit books from skeleton without payload/source fields: `{residual['decoder_can_emit_books_from_skeleton_without_payload_or_sources']}`.",
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
