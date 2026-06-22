#!/usr/bin/env python3
"""Parser/decoder frontier synthesis.

This audit exists to avoid opening another local residual-field gate after the
paid-control context route failed. It compiles the current executable-decoder,
segmentation, beam-selector, and innovation-tape evidence into one route ledger.

The output is a direction-setting artifact: it promotes no generator and changes
no compression bound. Its value is to make the remaining blocker explicit enough
that the next experiment can target representation change rather than another
selector table.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "parser_decoder_frontier_synthesis_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

INPUTS = {
    "executable_program_frontier": ROOT
    / "analysis"
    / "executable_program_frontier_synthesis_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_program_frontier_synthesis.json",
    "paid_control_context_payload_codec": ROOT
    / "analysis"
    / "paid_control_context_payload_codec_audit_20260622"
    / "reports"
    / "test_results"
    / "01_paid_control_context_payload_codec_gate.json",
    "branch_choice_frontier_closure": ROOT
    / "analysis"
    / "segmentation_decision_audit_20260621"
    / "reports"
    / "test_results"
    / "36_branch_choice_frontier_closure_audit.json",
    "beam_survival_budget": ROOT
    / "analysis"
    / "segmentation_decision_audit_20260621"
    / "reports"
    / "test_results"
    / "58_beam_survival_budget_gate.json",
    "beam_rank_selector": ROOT
    / "analysis"
    / "segmentation_decision_audit_20260621"
    / "reports"
    / "test_results"
    / "59_beam_rank_selector_gate.json",
    "beam_markov_state_selector": ROOT
    / "analysis"
    / "segmentation_decision_audit_20260621"
    / "reports"
    / "test_results"
    / "63_beam_markov_state_selector_gate.json",
    "generation_dependency_frontier": ROOT
    / "analysis"
    / "innovation_stream_transducer_audit_20260622"
    / "reports"
    / "test_results"
    / "14_generation_dependency_frontier_ledger.json",
    "length_control_tape": ROOT
    / "analysis"
    / "innovation_stream_transducer_audit_20260622"
    / "reports"
    / "test_results"
    / "15_length_control_tape_gate.json",
    "joint_type_length_control_tape": ROOT
    / "analysis"
    / "innovation_stream_transducer_audit_20260622"
    / "reports"
    / "test_results"
    / "16_joint_type_length_control_tape_gate.json",
}

JSON_OUT = TEST_RESULTS / "01_parser_decoder_frontier_synthesis.json"
MD_OUT = TEST_RESULTS / "01_parser_decoder_frontier_synthesis.md"
FINAL_OUT = FRONT / "reports" / "final_parser_decoder_frontier_synthesis_audit.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changes translation boundary")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduces plaintext claim")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopens case")
    decision = data.get("decision", {})
    row0 = decision.get("row0_status") or decision.get("row0_origin_status")
    if row0 not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changes row0 status: {row0}")


def load_inputs() -> dict[str, dict[str, Any]]:
    loaded = {}
    for name, path in INPUTS.items():
        data = load_json(path)
        assert_boundary(name, data)
        loaded[name] = data
    return loaded


def route_rows(data: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    executable = data["executable_program_frontier"]["summary"]
    paid = data["paid_control_context_payload_codec"]["summary"]
    branch = data["branch_choice_frontier_closure"]["summary"]
    beam_survival = data["beam_survival_budget"]["summary"]
    beam_rank = data["beam_rank_selector"]["summary"]
    beam_markov = data["beam_markov_state_selector"]["summary"]
    frontier = data["generation_dependency_frontier"]["summary"]
    length = data["length_control_tape"]["summary"]
    joint = data["joint_type_length_control_tape"]["summary"]

    return [
        {
            "route": "current_executable_external_tape_program",
            "status": "closed_needs_representation_change",
            "evidence": (
                f"roundtrip_70_70={executable['roundtrip_70_70']}; "
                f"promoted_tape_reductions={executable['promoted_executable_tape_reductions']}; "
                f"external_bits_including_seed={executable['external_bits_including_seed']:.3f}"
            ),
            "reason": "The contract is executable and useful as ledger, but no tested macro/source/controller route reduces paid tapes.",
        },
        {
            "route": "paid_control_context_payload_codec",
            "status": "closed_negative",
            "evidence": (
                "promoted_targets="
                f"{paid['promoted_targets']}; "
                "savings="
                f"{ {k: round(v['saving_bits'], 3) for k, v in paid['target_summaries'].items()} }"
            ),
            "reason": "Already-paid coarse/book/op contexts do not reduce literal payload, copy-hint, or composition residual streams.",
        },
        {
            "route": "local_branch_choice_and_residual_selector",
            "status": "closed_saturated",
            "evidence": (
                f"gates={branch['gate_count']}; complete_promoted={branch['complete_promoted_parser_rules']}; "
                f"partial_promoted={branch['partial_promoted_rule_count']}; next_blocker={branch['next_blocker']}"
            ),
            "reason": "Residual branch choices are oracle-repairable, but tested observable selectors either overfit, miss residuals, or become lookup patches.",
        },
        {
            "route": "small_beam_path_state",
            "status": "retained_weak_clue_not_program",
            "evidence": (
                f"best_objective={beam_survival['best_objective']}; width={beam_survival['best_residual_max_rank']}; "
                f"survival_cells={beam_survival['prequential_residual_survived_at_train_width_cells']}/{beam_survival['prequential_cells']}; "
                f"fixed_width_net_vs_lookup={beam_survival['fixed_width_net_vs_lookup_bits']:.3f}"
            ),
            "reason": "A width-5 beam keeps stable residual branches alive, but paying fixed width is worse than lookup and no stable selector is promoted.",
        },
        {
            "route": "beam_rank_or_markov_selector",
            "status": "closed_selector_not_promoted",
            "evidence": (
                f"rank_cover_all_cells={beam_rank['prequential_cover_all_test_cells']}/{beam_rank['prequential_cells']}; "
                f"rank_zero_clean_cells={beam_rank['prequential_zero_clean_false_change_cells']}/{beam_rank['prequential_cells']}; "
                f"markov_cover_all_cells={beam_markov['prequential_cover_all_test_cells']}/{beam_markov['prequential_cells']}; "
                f"markov_zero_clean_cells={beam_markov['prequential_zero_clean_false_change_cells']}/{beam_markov['prequential_cells']}"
            ),
            "reason": "Full-fit selectors see the right branch, but context tables and Markov state fail holdout/clean-control requirements.",
        },
        {
            "route": "innovation_tape_closed_loop_transducer",
            "status": "retained_clues_main_blocker_internal_starts",
            "evidence": (
                f"closed_loop_exact_books={frontier['closed_loop_exact_books']}; "
                f"target_conditioned_replay_exact_books={frontier['target_conditioned_replay_exact_books']}; "
                f"internal_ops={frontier['internal_ops']}; "
                f"right_ge4_missed_internal_starts={frontier['right_ge4_missed_internal_starts']}; "
                f"tape_structure_promoted={frontier['tape_structure_promoted']}"
            ),
            "reason": "Tape shape is real, but closed-loop generation fails and internal operation starts remain unresolved without target-future oracle.",
        },
        {
            "route": "length_or_joint_type_length_control_tape",
            "status": "retained_predictive_clue_not_skeleton_replacement",
            "evidence": (
                f"length_beats_shuffle_p95={length['beats_shuffle_paid_p95_cutoffs']}/{len(length['cutoffs_tested'])}; "
                f"length_beats_composition={length['beats_fixed_op_composition_cutoffs']}; "
                f"joint_beats_shuffle_p95={joint['beats_shuffle_paid_pair_p95_cutoffs']}/{len(joint['cutoffs_tested'])}; "
                f"joint_beats_skeleton_composition={joint['beats_skeleton_composition_cutoffs']}"
            ),
            "reason": "Control streams have prefix-holdout structure versus shuffled controls, but do not replace the fixed-op cutpoint/type composition ledger.",
        },
    ]


def make_result() -> dict[str, Any]:
    data = load_inputs()
    rows = route_rows(data)

    closed_routes = [row["route"] for row in rows if row["status"].startswith("closed")]
    retained_clues = [row["route"] for row in rows if row["status"].startswith("retained")]
    promoted_generators: list[str] = []

    classification = "PARSER_DECODER_FRONTIER_REQUIRES_INTERNAL_START_REPRESENTATION_CHANGE"
    next_route = (
        "target_free_internal_operation_start_program: combine the retained "
        "innovation-tape shape, joint type:length control clue, and small-beam "
        "survival into an executable decoder that pays missed-start and rank "
        "corrections explicitly; do not open another isolated selector/codec gate."
    )

    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "generator_promoted": False,
            "next_aligned_route": next_route,
            "promoted_generators": promoted_generators,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {name: rel(path) for name, path in INPUTS.items()},
        "plaintext_claim": False,
        "route_rows": rows,
        "schema": "parser_decoder_frontier_synthesis.v1",
        "scope": "analysis_only_route_frontier_synthesis",
        "summary": {
            "classification": classification,
            "closed_routes": closed_routes,
            "main_blocker": "target_free_internal_operation_starts",
            "promoted_generator_count": len(promoted_generators),
            "retained_clues": retained_clues,
            "routes_audited": len(rows),
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Parser/Decoder Frontier Synthesis",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "After the paid-control context codec failed, which route still plausibly "
        "moves the project toward an executable generative mechanism, and which "
        "routes should be treated as closed under current evidence?",
        "",
        "## Route Ledger",
        "",
        "| Route | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for row in result["route_rows"]:
        lines.append(f"| `{row['route']}` | `{row['status']}` | {row['evidence']} |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"Promoted generators: `{result['decision']['promoted_generators']}`.",
            "",
            f"Next aligned route: {result['decision']['next_aligned_route']}",
            "",
            "This is a route frontier synthesis, not a new formula. It preserves "
            "`row0`, plaintext, translation, and `compression_bound` boundaries.",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result, MD_OUT)
    write_markdown(result, FINAL_OUT)


if __name__ == "__main__":
    main()
