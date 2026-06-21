from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

CURRENT_FORMULA = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
GATE45 = TEST_RESULTS / "45_full_corpus_source_substitution_fourth_pass_gate.json"
SOURCE_SATURATION = TEST_RESULTS / "46_source_substitution_saturation_audit.json"
ROW0_BRIDGE = TEST_RESULTS / "47_row0_parallel_provenance_bridge_audit.json"
RECIPE_REPRESENTATION = TEST_RESULTS / "30_recipe_representation_dependency_gate.json"
SOURCE_SELECTION = TEST_RESULTS / "31_source_selection_derivation_boundary_gate.json"
COPY_LENGTH = TEST_RESULTS / "32_copy_length_derivation_boundary_gate.json"
LITERAL_AVAILABILITY = TEST_RESULTS / "28_literal_copy_availability_gate.json"
LITERAL_PAYLOAD = TEST_RESULTS / "29_literal_payload_model_gate.json"
CURRENT_PROFILE = TEST_RESULTS / "34_current_active_profile_boundary_gate.json"


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
        raise RuntimeError(f"{name} changed row0 origin status")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext status")


def roundtrip_formula(formula: dict[str, Any], books: dict[str, str]) -> list[str]:
    emitted = ""
    errors: list[str] = []
    for book in map(str, formula["policy"]["book_order"]):
        rendered = []
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "literal":
                chunk = op["text"]
            else:
                source = int(op["source_digit_pos"])
                length = int(op["length"])
                chunk = emitted[source : source + length]
            rendered.append(chunk)
            emitted += chunk
        if "".join(rendered) != books[book]:
            errors.append(book)
    return errors


def formula_dependency_counts(formula: dict[str, Any]) -> dict[str, Any]:
    literal_ops = []
    copy_ops = []
    for book, recipe in formula["book_recipes"].items():
        for op_index, op in enumerate(recipe["ops"]):
            if op["type"] == "literal":
                literal_ops.append((book, op_index, op))
            elif op["type"] == "copy":
                copy_ops.append((book, op_index, op))
            else:
                raise RuntimeError(f"unknown op type: {op['type']}")
    literal_digits = sum(len(op["text"]) for _, _, op in literal_ops)
    copied_digits = sum(int(op["length"]) for _, _, op in copy_ops)
    return {
        "book_count": len(formula["book_recipes"]),
        "op_count": len(literal_ops) + len(copy_ops),
        "literal_op_count": len(literal_ops),
        "copy_op_count": len(copy_ops),
        "literal_digits": literal_digits,
        "copied_digits": copied_digits,
        "total_emitted_digits": literal_digits + copied_digits,
        "literal_digit_fraction": literal_digits / (literal_digits + copied_digits),
        "copied_digit_fraction": copied_digits / (literal_digits + copied_digits),
        "declared_literal_text_fields": len(literal_ops),
        "declared_copy_source_fields": len(copy_ops),
        "declared_copy_length_fields": len(copy_ops),
    }


def make_result() -> dict[str, Any]:
    formula = load_json(CURRENT_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    errors = roundtrip_formula(formula, books)
    if errors:
        raise RuntimeError(f"formula roundtrip failed: {errors[:10]}")

    gate45 = load_json(GATE45)
    source_saturation = load_json(SOURCE_SATURATION)
    row0_bridge = load_json(ROW0_BRIDGE)
    recipe_representation = load_json(RECIPE_REPRESENTATION)
    source_selection = load_json(SOURCE_SELECTION)
    copy_length = load_json(COPY_LENGTH)
    literal_availability = load_json(LITERAL_AVAILABILITY)
    literal_payload = load_json(LITERAL_PAYLOAD)
    current_profile = load_json(CURRENT_PROFILE)

    for name, data in [
        ("gate45", gate45),
        ("source_saturation", source_saturation),
        ("row0_bridge", row0_bridge),
        ("recipe_representation", recipe_representation),
        ("source_selection", source_selection),
        ("copy_length", copy_length),
        ("literal_availability", literal_availability),
        ("literal_payload", literal_payload),
        ("current_profile", current_profile),
    ]:
        assert_boundary(name, data)

    counts = formula_dependency_counts(formula)
    representation = recipe_representation["summary"]
    if counts["declared_literal_text_fields"] != representation[
        "remaining_declared_dependencies"
    ]["literal_text_fields"]:
        raise RuntimeError("literal dependency count mismatch")
    if counts["declared_copy_source_fields"] != representation[
        "remaining_declared_dependencies"
    ]["copy_source_fields"]:
        raise RuntimeError("copy source dependency count mismatch")
    if counts["declared_copy_length_fields"] != representation[
        "remaining_declared_dependencies"
    ]["copy_length_fields"]:
        raise RuntimeError("copy length dependency count mismatch")

    rows = [
        {
            "dependency": "row0_table",
            "declared_units": 99,
            "coverage": "99 ordered codes / 55 unordered pair rows",
            "current_status": "exogenous_substrate",
            "evidence": {
                "parallel_verdict": row0_bridge["summary"]["parallel_verdict"],
                "paid_anchor_decision": row0_bridge["summary"]["paid_anchor_decision"],
                "all_anchors_explicit_pair_label_net_bits": row0_bridge["summary"][
                    "all_anchors_explicit_pair_label_net_bits"
                ],
            },
            "blocker": "No primary CipSoft/source artifact or paid row0-origin formula.",
            "next_testable_unlock": "Primary source, fixed external source, or paid holdout-capable row0 algorithm.",
            "mainline_priority": "external_or_provenance",
        },
        {
            "dependency": "copy_source",
            "declared_units": counts["declared_copy_source_fields"],
            "coverage": f"{counts['copied_digits']} copied digits",
            "current_status": "encoder_canonical_decoder_declared",
            "evidence": {
                "earliest_source_hits": source_selection["summary"]["earliest_source_hits"],
                "copy_items": source_selection["summary"]["copy_items"],
                "ambiguous_source_candidate_ops": source_selection["summary"][
                    "ambiguous_source_candidate_ops"
                ],
                "distance_replacement_penalty_bits": source_selection["summary"][
                    "distance_replacement_total_worse_than_active_bits"
                ],
                "state_free_penalty_bits": source_selection["summary"][
                    "best_state_free_total_penalty_bits"
                ],
                "local_source_frontier_saturated": source_saturation["summary"][
                    "frontier_saturated"
                ],
            },
            "blocker": "Earliest-source regularity depends on future target text; state-free and distance replacements lose.",
            "next_testable_unlock": "Joint source/length parser with decoder-known state, not same-chunk local substitution.",
            "mainline_priority": "structural_parser",
        },
        {
            "dependency": "copy_length",
            "declared_units": counts["declared_copy_length_fields"],
            "coverage": f"{counts['copied_digits']} copied digits",
            "current_status": "partly_decodable_declared_exceptions_retained",
            "evidence": {
                "decoder_default_count": copy_length["summary"][
                    "decoder_max_possible_default_count"
                ],
                "decoder_exception_count": copy_length["summary"][
                    "decoder_max_possible_exception_count"
                ],
                "encoder_target_max_match_count": copy_length["summary"][
                    "encoder_target_max_match_count"
                ],
                "encoder_target_max_decodable": copy_length["summary"][
                    "encoder_target_max_decodable"
                ],
                "midpoint_prefix_frozen_win_count": copy_length["summary"][
                    "midpoint_prefix_frozen_win_count"
                ],
            },
            "blocker": "High-coverage target-max is encoder-only; decoder model still carries 201 exceptions.",
            "next_testable_unlock": "Decoder-computable length rule or joint source/length objective that pays its exceptions.",
            "mainline_priority": "structural_parser",
        },
        {
            "dependency": "literal_payload",
            "declared_units": counts["declared_literal_text_fields"],
            "coverage": f"{counts['literal_digits']} literal digits",
            "current_status": "mostly_forced_payload_model_retained",
            "evidence": {
                "forced_literal_digits": literal_availability["summary"][
                    "forced_literal_digits_no_copy_candidate"
                ],
                "optional_literal_digits": literal_availability["summary"][
                    "optional_literal_digits_copy_candidate_available"
                ],
                "best_cross_op_delta_bits": literal_availability["summary"][
                    "cross_op_best_delta_bits"
                ],
                "active_literal_payload_bits": literal_payload["summary"][
                    "active_literal_payload_bits"
                ],
                "order1_full_delta_bits": literal_payload["summary"][
                    "order1_full_corpus_delta_vs_order2_bits"
                ],
                "best_modal_default_delta_bits": literal_payload["summary"][
                    "best_modal_default_delta_vs_active_bits"
                ],
            },
            "blocker": "Most literals are forced by copy unavailability; remaining simplifications and repairs are worse.",
            "next_testable_unlock": "Only a new source/length representation can plausibly absorb the small optional literal frontier.",
            "mainline_priority": "downstream_of_structural_parser",
        },
        {
            "dependency": "item_type_stream",
            "declared_units": current_profile["summary"]["event_counts"]["item_type"],
            "coverage": "item/copy-literal shape stream",
            "current_status": "learned_stream_retained_not_compact_op_type_field",
            "evidence": {
                "item_type_stream_bits": current_profile["summary"]["component_stream_bits"][
                    "item_type_stream_bits"
                ],
                "removed_type_fields": representation["removed_type_fields"],
                "score_delta_bits_after_type_derivation": representation[
                    "score_delta_bits"
                ],
            },
            "blocker": "Compact op type is derivable, but the learned item-type sequence remains part of the score.",
            "next_testable_unlock": "Only revisit if a full parser derives operation sequence under holdout.",
            "mainline_priority": "parser_sequence_later",
        },
    ]

    priority_order = [
        "structural_parser",
        "downstream_of_structural_parser",
        "parser_sequence_later",
        "external_or_provenance",
    ]
    return {
        "schema": "current_formula_dependency_scoreboard.v1",
        "classification": "current_formula_dependencies_mapped_no_new_bound",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "current_formula": rel(CURRENT_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "gate45": rel(GATE45),
            "source_saturation": rel(SOURCE_SATURATION),
            "row0_bridge": rel(ROW0_BRIDGE),
            "recipe_representation": rel(RECIPE_REPRESENTATION),
            "source_selection": rel(SOURCE_SELECTION),
            "copy_length": rel(COPY_LENGTH),
            "literal_availability": rel(LITERAL_AVAILABILITY),
            "literal_payload": rel(LITERAL_PAYLOAD),
            "current_profile": rel(CURRENT_PROFILE),
        },
        "current_formula": {
            "classification": formula["classification"],
            "roundtrip_book_count": len(books) - len(errors),
            "roundtrip_errors": errors,
            "current_local_source_bound_bits": gate45["summary"]["candidate_total_bits"],
            "dependency_counts": counts,
        },
        "rows": rows,
        "summary": {
            "remaining_declared_recipe_dependencies": [
                "literal_payload",
                "copy_source",
                "copy_length",
            ],
            "row0_status": "exogenous_substrate",
            "source_substitution_status": source_saturation["classification"],
            "literal_optional_frontier_digits": literal_availability["summary"][
                "optional_literal_digits_copy_candidate_available"
            ],
            "copy_source_encoder_canonical_hits": source_selection["summary"][
                "earliest_source_hits"
            ],
            "copy_length_encoder_target_max_hits": copy_length["summary"][
                "encoder_target_max_match_count"
            ],
            "priority_order": priority_order,
            "mainline_next_step": (
                "Attempt a structural decoder-known source/length parser or "
                "objective; do not resume local same-chunk source micro-sweeps."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8160_825608",
            "generation_explanation_status": "remaining_dependencies_mapped",
            "next_mainline_status": "structural_source_length_parser_before_literal_payload_or_item_type",
            "row0_origin_status": "exogenous_under_current_evidence",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "48_current_formula_dependency_scoreboard.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    current = result["current_formula"]
    counts = current["dependency_counts"]
    lines = [
        "# Current Formula Dependency Scoreboard",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This audit re-counts the dependencies of the current local-source-bound",
        "formula and maps each retained declaration to the gate that explains why",
        "it is not yet derived. It does not change the compression bound.",
        "",
        "## Current Formula",
        "",
        f"- Formula: `{Path(result['inputs']['current_formula']).name}`.",
        f"- Formula classification: `{current['classification']}`.",
        f"- Current local-source bound: `{current['current_local_source_bound_bits']:.6f}` bits.",
        f"- Roundtrip: `{current['roundtrip_book_count']}/70` books.",
        f"- Ops: `{counts['op_count']}` total, `{counts['literal_op_count']}` literal, `{counts['copy_op_count']}` copy.",
        f"- Literal digits: `{counts['literal_digits']}` (`{counts['literal_digit_fraction']:.6f}`).",
        f"- Copied digits: `{counts['copied_digits']}` (`{counts['copied_digit_fraction']:.6f}`).",
        "",
        "## Dependency Ledger",
        "",
        "| Dependency | Units | Coverage | Status | Mainline priority |",
        "|---|---:|---|---|---|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['dependency']}` | `{row['declared_units']}` | "
            f"{row['coverage']} | `{row['current_status']}` | "
            f"`{row['mainline_priority']}` |"
        )
    lines.extend(
        [
            "",
            "## Blockers",
            "",
        ]
    )
    for row in result["rows"]:
        lines.extend(
            [
                f"### {row['dependency']}",
                "",
                f"- Blocker: {row['blocker']}",
                f"- Next testable unlock: {row['next_testable_unlock']}",
                f"- Evidence: `{row['evidence']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            "",
            "- Compression bound is unchanged at `8160.825608` bits.",
            "- Local same-chunk source substitution is already saturated.",
            "- The next mainline mechanical work should be a structural decoder-known source/length parser or objective.",
            "- Literal payload and item-type work are downstream unless that structural parser changes available copy choices.",
            "- Row0 remains exogenous and requires primary provenance or a paid origin formula.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- No row0-origin formula is promoted.",
            "- No new book-generation formula is emitted.",
        ]
    )
    (TEST_RESULTS / "48_current_formula_dependency_scoreboard.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
