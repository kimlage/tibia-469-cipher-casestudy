from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE99 = TEST_RESULTS / "99_exact_skeleton_dependency_ledger.json"
GATE103 = TEST_RESULTS / "103_copy_availability_type_exception_ledger.json"
GATE105 = TEST_RESULTS / "105_optional_literal_exception_rule_audit.json"
GATE106 = TEST_RESULTS / "106_prequential_optional_literal_rule_validation.json"


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
    gate103 = load_json(GATE103)
    gate105 = load_json(GATE105)
    gate106 = load_json(GATE106)
    assert_boundary("exact_skeleton_dependency_ledger", gate99)
    assert_boundary("copy_availability_type_exception_ledger", gate103)
    assert_boundary("optional_literal_exception_rule_audit", gate105)
    assert_boundary("prequential_optional_literal_rule_validation", gate106)

    op_count = int(gate103["summary"]["op_count"])
    copy_count = int(gate103["summary"]["copy_count"])
    literal_count = int(gate103["summary"]["literal_count"])
    forced_literal_rows = int(gate103["summary"]["forced_literal_rows"])
    optional_literal_exceptions = int(gate103["summary"]["optional_literal_exceptions"])
    residual_rule_errors = int(gate105["summary"]["best_rule_errors"])
    rule_tp = int(gate105["summary"]["best_rule_tp"])
    rule_fp = int(gate105["summary"]["best_rule_fp"])
    rule_fn = int(gate105["summary"]["best_rule_fn"])
    exact_skeleton_atlas_records = int(gate99["summary"]["skeleton_atlas_records"])
    exact_skeleton_total_records = int(gate99["summary"]["skeleton_total_materialized_records"])
    length_atlas_records = op_count
    op_type_residual_records = residual_rule_errors
    type_length_records_after_rule = length_atlas_records + op_type_residual_records
    total_records_after_type_rule = (
        type_length_records_after_rule
        + int(gate99["summary"]["copy_items"])
        + int(gate99["summary"]["literal_runs"])
    )
    explicit_op_type_fields_before_rule = op_count
    explicit_op_type_residual_after_rule = residual_rule_errors
    conceptual_type_field_delta = (
        explicit_op_type_residual_after_rule - explicit_op_type_fields_before_rule
    )

    promotes_type_generator = (
        residual_rule_errors == 0
        and gate103["scope"].get("target_text_dependency_retained") is False
        and gate106["summary"]["promotes_prequential_rule"] is True
    )
    classification = (
        "operation_type_generator_promotable"
        if promotes_type_generator
        else "operation_type_dependency_reduced_not_promoted"
    )

    return {
        "schema": "operation_type_dependency_ledger.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate99_exact_skeleton_dependency_ledger": rel(GATE99),
            "gate103_copy_availability_type_exception": rel(GATE103),
            "gate105_optional_literal_exception_rule": rel(GATE105),
            "gate106_prequential_optional_literal_rule": rel(GATE106),
        },
        "scope": {
            "analysis_only": True,
            "ledger_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "target_text_dependency_retained": True,
            "length_atlas_dependency_retained": True,
        },
        "summary": {
            "operation_count": op_count,
            "copy_count": copy_count,
            "literal_count": literal_count,
            "forced_literal_rows_from_no_copy_availability": forced_literal_rows,
            "optional_literal_exceptions_before_rule": optional_literal_exceptions,
            "optional_literal_exception_rule": gate105["summary"]["best_rule"],
            "optional_literal_exception_rule_tp_fp_fn": [rule_tp, rule_fp, rule_fn],
            "residual_type_errors_after_rule": residual_rule_errors,
            "explicit_op_type_fields_before_rule": explicit_op_type_fields_before_rule,
            "explicit_op_type_residual_after_rule": explicit_op_type_residual_after_rule,
            "conceptual_type_field_delta": conceptual_type_field_delta,
            "length_atlas_records_retained": length_atlas_records,
            "type_length_records_after_rule": type_length_records_after_rule,
            "exact_skeleton_atlas_records": exact_skeleton_atlas_records,
            "record_delta_vs_exact_skeleton_atlas": (
                type_length_records_after_rule - exact_skeleton_atlas_records
            ),
            "exact_skeleton_total_materialized_records": exact_skeleton_total_records,
            "total_materialized_records_after_type_rule": total_records_after_type_rule,
            "record_delta_vs_gate99_total_materialized": (
                total_records_after_type_rule - exact_skeleton_total_records
            ),
            "prequential_support": {
                "evaluated_splits": gate106["summary"]["evaluated_splits"],
                "train_selected_better_than_baseline_splits": gate106["summary"][
                    "train_selected_better_than_baseline_splits"
                ],
                "max_train_selected_oracle_gap_errors": gate106["summary"][
                    "max_train_selected_oracle_gap_errors"
                ],
                "promotes_prequential_rule": gate106["summary"][
                    "promotes_prequential_rule"
                ],
            },
            "promotes_type_generator": promotes_type_generator,
            "interpretation": (
                "Operation type is mostly derivable once target copy availability "
                "and the length atlas are allowed: no-availability forces 36 "
                "literals, availability covers all 208 copies, and a short rule "
                "reduces the 17 optional literal exceptions to 3 residual errors. "
                "This reduces explicit op-type dependency conceptually from 261 "
                "fields to 3 residual fields, with prequential support, but it "
                "does not reduce the materialized atlas because the 261 length "
                "rows, target copy availability, copy sources, and literal "
                "payload remain external."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "op_type_dependency_reduced_generator_not_promoted",
            "skeleton_status": "type_mostly_derived_length_atlas_retained",
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "107_operation_type_dependency_ledger.json"
    md_path = TEST_RESULTS / "107_operation_type_dependency_ledger.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    ps = s["prequential_support"]
    lines = [
        "# Operation Type Dependency Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gates 103-106 show that operation type is strongly constrained by",
        "copy availability and optional-literal rules. This ledger separates",
        "conceptual op-type dependency reduction from actual generator promotion.",
        "",
        "## Ledger",
        "",
        f"- Operations: `{s['operation_count']}`.",
        f"- Copies/literals: `{s['copy_count']}` / `{s['literal_count']}`.",
        f"- Forced literals from no copy availability: `{s['forced_literal_rows_from_no_copy_availability']}`.",
        f"- Optional literal exceptions before rule: `{s['optional_literal_exceptions_before_rule']}`.",
        f"- Optional literal rule: `{s['optional_literal_exception_rule']}`.",
        f"- Rule TP/FP/FN: `{s['optional_literal_exception_rule_tp_fp_fn']}`.",
        f"- Residual type errors after rule: `{s['residual_type_errors_after_rule']}`.",
        f"- Explicit op-type fields before/after rule: `{s['explicit_op_type_fields_before_rule']}` / `{s['explicit_op_type_residual_after_rule']}`.",
        f"- Conceptual op-type field delta: `{s['conceptual_type_field_delta']}`.",
        f"- Length atlas records retained: `{s['length_atlas_records_retained']}`.",
        f"- Type+length records after rule: `{s['type_length_records_after_rule']}`.",
        f"- Record delta vs exact skeleton atlas: `{s['record_delta_vs_exact_skeleton_atlas']}`.",
        f"- Total materialized record delta vs gate 99: `{s['record_delta_vs_gate99_total_materialized']}`.",
        "",
        "## Prequential Support",
        "",
        f"- Evaluated splits: `{ps['evaluated_splits']}`.",
        f"- Train-selected beats baseline splits: `{ps['train_selected_better_than_baseline_splits']}`.",
        f"- Max train-selected oracle gap: `{ps['max_train_selected_oracle_gap_errors']}`.",
        f"- Promotes prequential rule: `{ps['promotes_prequential_rule']}`.",
        "",
        "## Decision",
        "",
        f"- Promotes type generator: `{s['promotes_type_generator']}`.",
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
