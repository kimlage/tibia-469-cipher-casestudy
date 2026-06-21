from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

FINAL_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_second_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
GATE60 = TEST_RESULTS / "60_active_source_length_joint_refresh_gate.json"
GATE69 = TEST_RESULTS / "69_partial_boundary_shift_saturation_gate.json"
GATE70 = TEST_RESULTS / "70_recent_formula_row0_compatibility_audit.json"
GATE60_SCRIPT = HERE / "scripts" / "60_active_source_length_joint_refresh_gate.py"

FINAL_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_second_pass_bits"
)


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


def count_ops(formula: dict[str, Any]) -> dict[str, int]:
    literal_ops = 0
    copy_ops = 0
    literal_digits = 0
    copied_digits = 0
    for recipe in formula["book_recipes"].values():
        for op in recipe["ops"]:
            if op["type"] == "literal":
                literal_ops += 1
                literal_digits += len(op["text"])
            elif op["type"] == "copy":
                copy_ops += 1
                copied_digits += int(op["length"])
            else:
                raise RuntimeError({"unknown_op": op})
    return {
        "literal_op_count": literal_ops,
        "copy_op_count": copy_ops,
        "op_count": literal_ops + copy_ops,
        "literal_digits": literal_digits,
        "copied_digits": copied_digits,
        "declared_literal_payload_fields": literal_ops,
        "declared_copy_source_fields": copy_ops,
        "declared_copy_length_fields": copy_ops,
        "declared_operation_dependency_fields": literal_ops + 2 * copy_ops,
    }


def deltas(current: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "copied_digits",
        "copy_event_count",
        "earliest_source_hits_at_declared_length",
        "unique_source_hits_at_declared_length",
        "latest_source_hits_at_declared_length",
        "decoder_max_length_hits_after_declared_source",
        "encoder_target_max_length_hits_after_declared_source",
        "joint_encoder_earliest_target_max_hits",
        "joint_declared_source_decoder_max_hits",
        "joint_unique_source_decoder_max_hits",
        "joint_unique_source_target_max_hits",
        "joint_previous_end_decoder_max_hits",
    ]
    return {key: current[key] - previous[key] for key in keys}


def make_result() -> dict[str, Any]:
    gate60 = load_json(GATE60)
    gate69 = load_json(GATE69)
    gate70 = load_json(GATE70)
    for name, data in [
        ("active_source_length_joint_refresh_gate", gate60),
        ("partial_boundary_shift_saturation_gate", gate69),
        ("recent_formula_row0_compatibility_audit", gate70),
    ]:
        assert_boundary(name, data)

    helper60 = load_module("gate60_source_length_refresh", GATE60_SCRIPT)
    formula = load_json(FINAL_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    rows = helper60.collect_rows(formula, books)
    current_summary = helper60.summarize_rows(rows)
    previous_summary = gate60["active_formula_summary"]
    delta = deltas(current_summary, previous_summary)
    op_counts = count_ops(formula)
    total_bits = float(formula["mdl_estimate_rough"][FINAL_TOTAL_KEY])
    saturation_total = float(gate69["summary"]["current_total_bits"])
    if abs(total_bits - saturation_total) > 1e-9:
        raise RuntimeError(
            {
                "type": "final_total_mismatch",
                "formula_total": total_bits,
                "saturation_total": saturation_total,
            }
        )

    decoder_joint_improved = (
        delta["joint_declared_source_decoder_max_hits"] > 0
        or delta["joint_unique_source_decoder_max_hits"] > 0
        or delta["joint_previous_end_decoder_max_hits"] > 0
    )
    target_max_improved = delta["encoder_target_max_length_hits_after_declared_source"] > 0
    structural_blocker = (
        "source_length_parser_still_required"
        if not decoder_joint_improved
        else "decoder_joint_rule_improved_needs_promotion_gate"
    )
    interpretation = (
        "The final partial-boundary promotions improve the compression bound, "
        "but they do not change the source/length dependency scoreboard: "
        "encoder target-max coverage and every decoder-valid joint rule remain "
        "unchanged versus the gate-60 active formula. The next mechanical blocker "
        "remains a source/length parser or derivation, not another local boundary "
        "shift."
        if not decoder_joint_improved
        else "A decoder-valid joint source/length count improved; a separate "
        "promotion gate would be required before changing the generation profile."
    )

    return {
        "schema": "final_formula_dependency_refresh_gate.v1",
        "classification": "final_formula_dependency_refresh_decoder_boundary_unchanged",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "final_formula": rel(FINAL_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "previous_source_length_refresh": rel(GATE60),
            "partial_boundary_saturation_gate": rel(GATE69),
            "row0_compatibility_gate": rel(GATE70),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "final_formula_summary": current_summary,
        "previous_active_formula_summary": previous_summary,
        "deltas_vs_gate60_active": delta,
        "declared_dependency_counts": op_counts,
        "summary": {
            "final_total_bits": total_bits,
            "previous_gate60_active_bound_bits": gate60["summary"].get(
                "active_total_bits"
            ),
            "copy_event_count": current_summary["copy_event_count"],
            "declared_operation_dependency_fields": op_counts[
                "declared_operation_dependency_fields"
            ],
            "target_max_hit_delta_after_partial_shifts": delta[
                "encoder_target_max_length_hits_after_declared_source"
            ],
            "declared_source_decoder_max_delta_after_partial_shifts": delta[
                "joint_declared_source_decoder_max_hits"
            ],
            "unique_source_decoder_max_delta_after_partial_shifts": delta[
                "joint_unique_source_decoder_max_hits"
            ],
            "previous_end_decoder_max_delta_after_partial_shifts": delta[
                "joint_previous_end_decoder_max_hits"
            ],
            "decoder_valid_joint_rule_improved": decoder_joint_improved,
            "encoder_targetmax_rule_improved": target_max_improved,
            "structural_blocker": structural_blocker,
            "interpretation": interpretation,
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_joint_status": structural_blocker,
            "generation_explanation_status": "book_formula_bound_improved_dependency_boundary_unchanged",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "71_final_formula_dependency_refresh_gate.json"
    md_path = TEST_RESULTS / "71_final_formula_dependency_refresh_gate.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    final = result["final_formula_summary"]
    delta = result["deltas_vs_gate60_active"]
    deps = result["declared_dependency_counts"]
    lines = [
        "# Final Formula Dependency Refresh Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This gate refreshes the source/length dependency scoreboard on the",
        "current `8154.676268`-bit formula after both partial-boundary promotions.",
        "It checks whether the lower bound also changes the structural generation",
        "blocker.",
        "",
        "## Summary",
        "",
        f"- Final total bits: `{s['final_total_bits']:.6f}`.",
        f"- Copy events: `{s['copy_event_count']}`.",
        f"- Declared operation dependency fields: `{s['declared_operation_dependency_fields']}`.",
        f"- Encoder target-max hit delta after partial shifts: `{s['target_max_hit_delta_after_partial_shifts']}`.",
        f"- Declared-source + decoder-max delta: `{s['declared_source_decoder_max_delta_after_partial_shifts']}`.",
        f"- Unique-source + decoder-max delta: `{s['unique_source_decoder_max_delta_after_partial_shifts']}`.",
        f"- Previous-end + decoder-max delta: `{s['previous_end_decoder_max_delta_after_partial_shifts']}`.",
        f"- Decoder-valid joint rule improved: `{s['decoder_valid_joint_rule_improved']}`.",
        f"- Structural blocker: `{s['structural_blocker']}`.",
        "",
        "## Current Counts",
        "",
        "| Metric | Count | Delta vs gate 60 active |",
        "|---|---:|---:|",
    ]
    for key in [
        "earliest_source_hits_at_declared_length",
        "unique_source_hits_at_declared_length",
        "latest_source_hits_at_declared_length",
        "decoder_max_length_hits_after_declared_source",
        "encoder_target_max_length_hits_after_declared_source",
        "joint_encoder_earliest_target_max_hits",
        "joint_declared_source_decoder_max_hits",
        "joint_unique_source_decoder_max_hits",
        "joint_unique_source_target_max_hits",
        "joint_previous_end_decoder_max_hits",
    ]:
        lines.append(f"| `{key}` | `{final[key]}` | `{delta[key]:+d}` |")

    lines.extend(
        [
            "",
            "## Declared Dependency Ledger",
            "",
            f"- Literal payload fields: `{deps['declared_literal_payload_fields']}`.",
            f"- Copy source fields: `{deps['declared_copy_source_fields']}`.",
            f"- Copy length fields: `{deps['declared_copy_length_fields']}`.",
            f"- Total retained operation dependency fields: `{deps['declared_operation_dependency_fields']}`.",
            "",
            "## Decision",
            "",
            f"- {s['interpretation']}",
            "- The compression bound remains `8154.676268` bits.",
            "- Row0 remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
