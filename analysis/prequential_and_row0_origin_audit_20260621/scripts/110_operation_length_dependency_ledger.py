from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE32 = TEST_RESULTS / "32_copy_length_derivation_boundary_gate.json"
GATE71 = TEST_RESULTS / "71_final_formula_dependency_refresh_gate.json"
GATE100 = TEST_RESULTS / "100_skeleton_rule_coverage_audit.json"
GATE104 = TEST_RESULTS / "104_target_position_derivation_ledger.json"
GATE107 = TEST_RESULTS / "107_operation_type_dependency_ledger.json"
OUT_STEM = "110_operation_length_dependency_ledger"


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
    gate32 = load_json(GATE32)
    gate71 = load_json(GATE71)
    gate100 = load_json(GATE100)
    gate104 = load_json(GATE104)
    gate107 = load_json(GATE107)

    for name, data in [
        ("copy_length_derivation_boundary", gate32),
        ("final_formula_dependency_refresh", gate71),
        ("skeleton_rule_coverage", gate100),
        ("target_position_derivation", gate104),
        ("operation_type_dependency", gate107),
    ]:
        assert_boundary(name, data)

    if gate100["summary"]["simple_rule_covers_skeleton"] is not False:
        raise RuntimeError("skeleton simple rules unexpectedly promoted")
    if gate104["summary"]["target_start_derivable"] is not True:
        raise RuntimeError("target_start is no longer derivable from lengths")
    if gate107["summary"]["length_atlas_records_retained"] != 261:
        raise RuntimeError("length atlas count changed")
    if gate71["summary"]["decoder_valid_joint_rule_improved"] is not False:
        raise RuntimeError("final dependency refresh changed joint decoder boundary")

    op_count = int(gate107["summary"]["operation_count"])
    copy_count = int(gate107["summary"]["copy_count"])
    literal_count = int(gate107["summary"]["literal_count"])
    length_atlas_records = int(gate107["summary"]["length_atlas_records_retained"])
    op_type_residual = int(gate107["summary"]["explicit_op_type_residual_after_rule"])
    best_length_rule = gate100["summary"]["best_length_rule"]
    best_copy_length_rule = gate100["summary"]["best_copy_length_rule"]
    best_literal_length_rule = gate100["summary"]["best_literal_length_rule"]
    decoder_default_count = int(gate32["summary"]["decoder_max_possible_default_count"])
    decoder_exception_count = int(gate32["summary"]["decoder_max_possible_exception_count"])
    copy_length_fields_retained = int(
        gate32["summary"]["copy_length_fields_retained_in_compact_recipe"]
    )

    length_records_removed_by_rules = 0
    target_position_fields_removed = int(gate104["summary"]["operation_rows_checked"])
    type_length_records_after_type_rule = int(
        gate107["summary"]["type_length_records_after_rule"]
    )
    length_blocker_record_share = length_atlas_records / type_length_records_after_type_rule

    promotes_length_generator = (
        best_length_rule["hits"] == best_length_rule["total"]
        and gate32["summary"]["copy_length_fields_retained_in_compact_recipe"] == 0
        and gate71["summary"]["decoder_valid_joint_rule_improved"] is True
    )
    classification = (
        "operation_length_generator_promotable"
        if promotes_length_generator
        else "operation_length_dependency_retained"
    )

    return {
        "schema": "operation_length_dependency_ledger.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate32_copy_length_derivation_boundary": rel(GATE32),
            "gate71_final_formula_dependency_refresh": rel(GATE71),
            "gate100_skeleton_rule_coverage": rel(GATE100),
            "gate104_target_position_derivation": rel(GATE104),
            "gate107_operation_type_dependency": rel(GATE107),
        },
        "scope": {
            "analysis_only": True,
            "ledger_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "does_not_search_new_compression_sweep": True,
        },
        "summary": {
            "operation_count": op_count,
            "copy_count": copy_count,
            "literal_count": literal_count,
            "current_compression_bound_bits": gate71["summary"]["final_total_bits"],
            "declared_operation_dependency_fields": gate71["summary"][
                "declared_operation_dependency_fields"
            ],
            "target_start_fields_derived_from_lengths": target_position_fields_removed,
            "target_start_dependency_removed": True,
            "op_type_residual_after_rule": op_type_residual,
            "length_atlas_records_retained": length_atlas_records,
            "length_records_removed_by_current_rules": length_records_removed_by_rules,
            "type_length_records_after_type_rule": type_length_records_after_type_rule,
            "length_blocker_record_share_after_type_rule": length_blocker_record_share,
            "best_source_free_length_rule": best_length_rule,
            "best_source_free_copy_length_rule": best_copy_length_rule,
            "best_source_free_literal_length_rule": best_literal_length_rule,
            "copy_length_boundary": {
                "decoder_max_possible_default_count": decoder_default_count,
                "decoder_max_possible_exception_count": decoder_exception_count,
                "copy_length_fields_retained_in_compact_recipe": copy_length_fields_retained,
                "encoder_target_max_decodable": gate32["summary"][
                    "encoder_target_max_decodable"
                ],
                "dependency_retained": gate32["summary"]["dependency_retained"],
            },
            "final_source_length_refresh": {
                "copy_event_count": gate71["summary"]["copy_event_count"],
                "encoder_targetmax_rule_improved": gate71["summary"][
                    "encoder_targetmax_rule_improved"
                ],
                "decoder_valid_joint_rule_improved": gate71["summary"][
                    "decoder_valid_joint_rule_improved"
                ],
                "declared_source_decoder_max_delta_after_partial_shifts": gate71[
                    "summary"
                ]["declared_source_decoder_max_delta_after_partial_shifts"],
                "unique_source_decoder_max_delta_after_partial_shifts": gate71[
                    "summary"
                ]["unique_source_decoder_max_delta_after_partial_shifts"],
                "previous_end_decoder_max_delta_after_partial_shifts": gate71[
                    "summary"
                ]["previous_end_decoder_max_delta_after_partial_shifts"],
                "structural_blocker": gate71["summary"]["structural_blocker"],
            },
            "promotes_length_generator": promotes_length_generator,
            "interpretation": (
                "Target positions are derived once the length sequence is known, "
                "and operation type is mostly derivable if target copy availability "
                "and the length atlas are allowed. The remaining blocker is the "
                "length sequence itself: current source-free length rules cover at "
                "most 116/261 operation lengths, copy-specific source-free rules "
                "cover only 55/208 copy lengths, literal length rules cover only "
                "5/53 literal lengths, and the compact recipe still retains all "
                "261 copy-length fields. The current model therefore explains "
                "positions and most type decisions downstream of length, but it "
                "does not yet generate the operation-length atlas."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "length_atlas_retained_generator_not_promoted",
            "skeleton_status": "position_and_type_partly_derived_length_sequence_retained",
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    b = s["copy_length_boundary"]
    f = s["final_source_length_refresh"]
    lines = [
        "# Operation Length Dependency Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This ledger consolidates the length side of the current skeleton",
        "frontier. It asks whether recent derivations remove the operation",
        "length atlas or merely make other fields downstream of that atlas.",
        "",
        "## Ledger",
        "",
        f"- Operations: `{s['operation_count']}`.",
        f"- Copies/literals: `{s['copy_count']}` / `{s['literal_count']}`.",
        f"- Current compression bound: `{s['current_compression_bound_bits']:.6f}` bits.",
        f"- Declared operation dependency fields: `{s['declared_operation_dependency_fields']}`.",
        f"- Target-start fields derived from lengths: `{s['target_start_fields_derived_from_lengths']}`.",
        f"- Op-type residual after availability/exception rule: `{s['op_type_residual_after_rule']}`.",
        f"- Length atlas records retained: `{s['length_atlas_records_retained']}`.",
        f"- Length records removed by current rules: `{s['length_records_removed_by_current_rules']}`.",
        f"- Type+length records after type rule: `{s['type_length_records_after_type_rule']}`.",
        f"- Length share of type+length ledger: `{s['length_blocker_record_share_after_type_rule']:.6f}`.",
        "",
        "## Rule Coverage",
        "",
        f"- Best source-free length rule: `{s['best_source_free_length_rule']['rule']}` = `{s['best_source_free_length_rule']['hits']}/{s['best_source_free_length_rule']['total']}`.",
        f"- Best source-free copy-length rule: `{s['best_source_free_copy_length_rule']['rule']}` = `{s['best_source_free_copy_length_rule']['hits']}/{s['best_source_free_copy_length_rule']['total']}`.",
        f"- Best source-free literal-length rule: `{s['best_source_free_literal_length_rule']['rule']}` = `{s['best_source_free_literal_length_rule']['hits']}/{s['best_source_free_literal_length_rule']['total']}`.",
        "",
        "## Copy-Length Boundary",
        "",
        f"- Decoder max-possible defaults/exceptions: `{b['decoder_max_possible_default_count']}` / `{b['decoder_max_possible_exception_count']}`.",
        f"- Copy-length fields retained in compact recipe: `{b['copy_length_fields_retained_in_compact_recipe']}`.",
        f"- Encoder target-max decodable: `{b['encoder_target_max_decodable']}`.",
        f"- Dependency retained: `{b['dependency_retained']}`.",
        "",
        "## Final Source/Length Refresh",
        "",
        f"- Copy events: `{f['copy_event_count']}`.",
        f"- Encoder target-max rule improved after partial shifts: `{f['encoder_targetmax_rule_improved']}`.",
        f"- Decoder-valid joint rule improved after partial shifts: `{f['decoder_valid_joint_rule_improved']}`.",
        f"- Declared-source + decoder-max delta: `{f['declared_source_decoder_max_delta_after_partial_shifts']}`.",
        f"- Unique-source + decoder-max delta: `{f['unique_source_decoder_max_delta_after_partial_shifts']}`.",
        f"- Previous-end + decoder-max delta: `{f['previous_end_decoder_max_delta_after_partial_shifts']}`.",
        f"- Structural blocker: `{f['structural_blocker']}`.",
        "",
        "## Decision",
        "",
        f"- Promotes length generator: `{s['promotes_length_generator']}`.",
        f"- {s['interpretation']}",
        "- No compression-bound change is introduced.",
        "- No formula is emitted.",
        "- Row0 remains unchanged and exogenous.",
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
