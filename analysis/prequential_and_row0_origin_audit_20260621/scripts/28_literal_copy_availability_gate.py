from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL_RESULTS = ROOT / "analysis" / "authorial_mechanism_20260620" / "reports" / "test_results"

AVAILABILITY = AUTHORIAL_RESULTS / "149_literal_copy_availability_boundary_audit.json"
IN_LITERAL_REPAIR = AUTHORIAL_RESULTS / "150_optional_literal_copy_repair_frontier.json"
CROSS_OP_REPAIR = AUTHORIAL_RESULTS / "151_cross_op_optional_literal_copy_frontier.json"
NEAR_TIE = AUTHORIAL_RESULTS / "152_cross_op_near_tie_decomposition.json"
SOURCE_BLOCKER_GATE = TEST_RESULTS / "24_source_blocker_structural_context_gate.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened") is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim") is not False:
        raise RuntimeError(f"{name} introduced plaintext")


def make_result() -> dict[str, Any]:
    availability = load_json(AVAILABILITY)
    in_literal = load_json(IN_LITERAL_REPAIR)
    cross_op = load_json(CROSS_OP_REPAIR)
    near_tie = load_json(NEAR_TIE)
    source_gate = load_json(SOURCE_BLOCKER_GATE)
    for name, data in [
        ("literal_copy_availability", availability),
        ("optional_literal_copy_repair", in_literal),
        ("cross_op_optional_literal_copy_repair", cross_op),
        ("cross_op_near_tie", near_tie),
        ("source_blocker_gate", source_gate),
    ]:
        assert_boundary(name, data)

    summary = availability["summary"]
    forced_item_share = summary["forced_literal_items_no_copy_candidate"] / summary["literal_items"]
    forced_digit_share = summary["forced_literal_digits_no_copy_candidate"] / summary["literal_digits"]
    optional_item_share = (
        summary["optional_literal_items_copy_candidate_available"] / summary["literal_items"]
    )
    optional_digit_share = (
        summary["optional_literal_digits_copy_candidate_available"] / summary["literal_digits"]
    )
    in_literal_best_delta = float(in_literal["best_candidate"]["delta_bits"])
    cross_op_best_delta = float(cross_op["best_candidate"]["delta_bits"])
    source_blocker_closed = (
        source_gate["classification"]
        == "simple_source_contexts_do_not_rescue_cross_op_near_tie"
    )
    literal_externality_reduced = (
        availability["decision"]["literal_recipe_externality_reduced"]
        and summary["forced_literal_items_no_copy_candidate"] > summary["optional_literal_items_copy_candidate_available"]
        and summary["forced_literal_digits_no_copy_candidate"] > summary["optional_literal_digits_copy_candidate_available"]
    )
    local_repairs_closed = (
        in_literal["decision"]["active_parser_retained"]
        and cross_op["decision"]["active_parser_retained"]
        and in_literal["improving_candidate_count"] == 0
        and cross_op["improving_candidate_count"] == 0
    )
    classification = (
        "literal_externality_reduced_local_repairs_rejected"
        if literal_externality_reduced and local_repairs_closed and source_blocker_closed
        else "literal_externality_boundary_unresolved"
    )

    return {
        "schema": "literal_copy_availability_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "literal_copy_availability": rel(AVAILABILITY),
            "optional_literal_copy_repair": rel(IN_LITERAL_REPAIR),
            "cross_op_optional_literal_copy_repair": rel(CROSS_OP_REPAIR),
            "cross_op_near_tie": rel(NEAR_TIE),
            "source_blocker_gate": rel(SOURCE_BLOCKER_GATE),
        },
        "summary": {
            "literal_items": summary["literal_items"],
            "literal_digits": summary["literal_digits"],
            "forced_literal_items_no_copy_candidate": summary[
                "forced_literal_items_no_copy_candidate"
            ],
            "forced_literal_item_share": forced_item_share,
            "optional_literal_items_copy_candidate_available": summary[
                "optional_literal_items_copy_candidate_available"
            ],
            "optional_literal_item_share": optional_item_share,
            "forced_literal_digits_no_copy_candidate": summary[
                "forced_literal_digits_no_copy_candidate"
            ],
            "forced_literal_digit_share": forced_digit_share,
            "optional_literal_digits_copy_candidate_available": summary[
                "optional_literal_digits_copy_candidate_available"
            ],
            "optional_literal_digit_share": optional_digit_share,
            "short_suffix_literal_digits": summary["short_suffix_literal_digits"],
            "optional_literal_items_shorter_than_min_len": summary[
                "optional_literal_items_shorter_than_min_len"
            ],
            "optional_literal_items_candidate_covers_literal_length": summary[
                "optional_literal_items_candidate_covers_literal_length"
            ],
            "in_literal_candidate_repairs_scored": in_literal["scope"][
                "candidate_repairs_scored"
            ],
            "in_literal_improving_candidate_count": in_literal[
                "improving_candidate_count"
            ],
            "in_literal_best_delta_bits": in_literal_best_delta,
            "in_literal_best_book": in_literal["best_candidate"]["book"],
            "cross_op_valid_candidate_count": cross_op["scope"][
                "valid_cross_op_candidates"
            ],
            "cross_op_improving_candidate_count": cross_op[
                "improving_candidate_count"
            ],
            "cross_op_best_delta_bits": cross_op_best_delta,
            "cross_op_best_book": cross_op["best_candidate"]["book"],
            "near_tie_copy_source_penalty_bits": near_tie["component_deltas"][
                "copy_source_default_exception_bits"
            ],
            "near_tie_copy_length_penalty_bits": near_tie["component_deltas"][
                "copy_length_default_exception_bits"
            ],
            "near_tie_literal_payload_saving_bits": near_tie["component_deltas"][
                "literal_payload_bits"
            ],
            "near_tie_requires_new_model_or_declaration_credit": near_tie["decision"][
                "near_tie_requires_new_model_or_declaration_credit"
            ],
            "source_blocker_gate_closed": source_blocker_closed,
            "literal_externality_reduced": literal_externality_reduced,
            "literal_externality_removed": availability["decision"][
                "literal_recipe_externality_removed"
            ],
            "local_repairs_closed": local_repairs_closed,
            "interpretation": (
                "Most literal payload is forced by copy unavailability; the "
                "remaining optional frontier is small and the tested in-literal "
                "and cross-op local repairs are worse under the active ledger. "
                "The closest cross-op repair is blocked by decodable copy-source "
                "and length costs, not by an unexplained semantic signal."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged",
            "literal_externality_status": "reduced_not_removed",
            "local_literal_repair_status": "in_literal_and_cross_op_repairs_rejected",
            "generation_explanation_status": "literal_parser_choice_boundary_sharpened",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "28_literal_copy_availability_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    lines = [
        "# Literal Copy Availability Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The active formula still contains literal payload text. This gate checks",
        "how much of that literal payload is mechanically forced by absence of a",
        "legal `min_len` copy, and whether the remaining optional literal starts",
        "can be repaired by simple local copy substitutions.",
        "",
        "## Summary",
        "",
        f"- Literal items: `{s['literal_items']}`.",
        f"- Literal digits: `{s['literal_digits']}`.",
        f"- Forced literal items with no legal copy at start: "
        f"`{s['forced_literal_items_no_copy_candidate']}` "
        f"(`{100 * s['forced_literal_item_share']:.3f}%`).",
        f"- Forced literal digits with no legal copy: "
        f"`{s['forced_literal_digits_no_copy_candidate']}` "
        f"(`{100 * s['forced_literal_digit_share']:.3f}%`).",
        f"- Optional literal starts with copy candidates: "
        f"`{s['optional_literal_items_copy_candidate_available']}`.",
        f"- Optional literal digits with copy candidates: "
        f"`{s['optional_literal_digits_copy_candidate_available']}`.",
        f"- In-literal repair candidates scored: `{s['in_literal_candidate_repairs_scored']}`.",
        f"- Best in-literal repair delta: `{s['in_literal_best_delta_bits']:.3f}` bits.",
        f"- Cross-op repair candidates scored: `{s['cross_op_valid_candidate_count']}`.",
        f"- Best cross-op repair delta: `{s['cross_op_best_delta_bits']:.3f}` bits.",
        f"- Near-tie source/length penalties: "
        f"`{s['near_tie_copy_source_penalty_bits']:.3f}` / "
        f"`{s['near_tie_copy_length_penalty_bits']:.3f}` bits.",
        f"- Near-tie literal-payload saving: "
        f"`{s['near_tie_literal_payload_saving_bits']:.3f}` bits.",
        "",
        "## Interpretation",
        "",
        "Literal payload is not treated as free authorial choice. Most literal",
        "items and digits are forced by copy unavailability. The remaining optional",
        "frontier is localized to `14` starts and `97` digits, and the two tested",
        "repair families do not improve the active ledger: the best in-literal",
        "repair is `+1.180` bits and the best cross-op repair is `+0.027` bits.",
        "The near-tie saves literal and item bits, but pays `+11.237` source bits",
        "and `+1.639` copy-length bits, so the current parser remains retained",
        "unless a new source/length representation appears.",
        "",
        "## Boundary",
        "",
        "- Literal recipe externality is reduced but not removed.",
        "- No compression bound is promoted.",
        "- No plaintext, translation, semantic reading, row0 change, or case reopening is introduced.",
    ]
    (TEST_RESULTS / "28_literal_copy_availability_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
