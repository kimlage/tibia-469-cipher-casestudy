#!/usr/bin/env python3
"""Generative route frontier synthesis.

This audit is a decision artifact, not another local selector. It consolidates
the recent generation-frontier gates after several operation-token decomposition
routes failed controls:

- hidden/schedule state over joint operation tokens;
- book multiset versus within-book order;
- no-replacement ordering given true multiset;
- sequence mutation from previous books.

The purpose is to prevent recycling the same route under new names and to name
the remaining constructive route precisely.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "generative_route_frontier_synthesis_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

INPUTS = {
    "latent_nonlocal_state": ROOT
    / "analysis"
    / "latent_nonlocal_state_program_pilot_audit_20260622"
    / "reports"
    / "test_results"
    / "01_latent_nonlocal_state_program_pilot.json",
    "schedule_state_multistream": ROOT
    / "analysis"
    / "schedule_state_multistream_pilot_audit_20260622"
    / "reports"
    / "test_results"
    / "01_schedule_state_multistream_pilot.json",
    "book_multiset_order": ROOT
    / "analysis"
    / "book_multiset_order_factorization_audit_20260622"
    / "reports"
    / "test_results"
    / "01_book_multiset_order_factorization_gate.json",
    "within_book_order": ROOT
    / "analysis"
    / "within_book_order_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_within_book_order_program_gate.json",
    "sequence_mutation": ROOT
    / "analysis"
    / "sequence_mutation_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_sequence_mutation_program_gate.json",
    "innovation_stream_transducer": ROOT
    / "analysis"
    / "innovation_stream_transducer_audit_20260622"
    / "reports"
    / "test_results"
    / "14_generation_dependency_frontier_ledger.json",
    "minimal_external_tape": ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_decoder_contract.json",
}

JSON_OUT = TEST_RESULTS / "01_generative_route_frontier_synthesis.json"
MD_OUT = TEST_RESULTS / "01_generative_route_frontier_synthesis.md"
FINAL_OUT = FRONT / "reports" / "final_generative_route_frontier_synthesis_audit.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")


def route_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    latent = data["latent_nonlocal_state"]
    schedule = data["schedule_state_multistream"]
    multiset = data["book_multiset_order"]
    order = data["within_book_order"]
    mutation = data["sequence_mutation"]

    rows = [
        {
            "route": "latent_hmm_joint_operation_tokens",
            "classification": latent["classification"],
            "positive_signal": f"{latent['summary']['total_hmm_delta_vs_factorized']:.3f} bits vs factorized",
            "control_result": f"shuffle_p05 {latent['summary']['beats_shuffle_p05_cells']}/5",
            "external_dependency_reduced": False,
            "decision": "not_promoted_hidden_state_distribution_signal",
            "next_action": "do_not_repeat_hmm_without_new_decoder-visible_state",
        },
        {
            "route": "schedule_state_joint_operation_tokens",
            "classification": schedule["classification"],
            "positive_signal": f"{schedule['summary']['total_delta_vs_factorized']:.3f} bits vs factorized",
            "control_result": f"shuffle_p05 {schedule['summary']['beats_shuffle_p05_cells']}/5",
            "external_dependency_reduced": False,
            "decision": "not_promoted_schedule_distribution_signal",
            "next_action": "do_not_treat_schedule_bits_as_generator",
        },
        {
            "route": "book_multiset_then_order",
            "classification": multiset["classification"],
            "positive_signal": f"{multiset['summary']['bag_saving_vs_global']:.3f} bag bits vs global",
            "control_result": f"permuted_feature_p95 {multiset['summary']['beats_permuted_p95_cells']}/5",
            "external_dependency_reduced": False,
            "decision": "audit_only_bag_factorization",
            "next_action": "do_not_pursue_book_bag_as_standalone_program",
        },
        {
            "route": "within_book_order_given_true_multiset",
            "classification": order["classification"],
            "positive_signal": f"{order['summary']['total_saving_vs_uniform_order']:.3f} bits vs uniform order",
            "control_result": (
                f"shuffled_train_p95 {order['summary']['beats_shuffled_train_p95_cells']}/5; "
                f"shuffled_test_p95 {order['summary']['beats_shuffled_test_p95_cells']}/5"
            ),
            "external_dependency_reduced": False,
            "decision": "order_index_program_rejected",
            "next_action": "do_not_split_multiset_and_order_again",
        },
        {
            "route": "previous_book_sequence_mutation",
            "classification": mutation["classification"],
            "positive_signal": f"{mutation['summary']['total_saving_vs_sequence_unigram']:.3f} bits vs sequence unigram",
            "control_result": (
                f"shuffled_train_p95 {mutation['summary']['beats_shuffled_train_p95_cells']}/5; "
                f"random_source_p95 {mutation['summary']['beats_random_source_p95_cells']}/5"
            ),
            "external_dependency_reduced": False,
            "decision": "whole_sequence_mutation_rejected_even_as_lower_bound",
            "next_action": "do_not_use_book-level_sequence_reuse_as_main_route",
        },
    ]
    return rows


def make_result() -> dict[str, Any]:
    data = {name: load_json(path) for name, path in INPUTS.items()}
    for name, loaded in data.items():
        if isinstance(loaded, dict):
            assert_boundary(name, loaded)
    rows = route_rows(data)
    closed_routes = [row["route"] for row in rows if row["external_dependency_reduced"] is False]
    open_route = {
        "name": "digit_level_content_boundary_transducer",
        "why": (
            "operation-token distribution routes compress or factor the ledger but do not "
            "reduce declared dependencies under controls; the remaining positive evidence "
            "sits at digit/content-boundary level: innovation tape structure, book-start "
            "candidate clues, copy-availability when target-conditioned, and internal "
            "op-start generation as the explicit blocker"
        ),
        "must_not_grant": [
            "operation_token_sequence",
            "book_multiset",
            "within_book_order",
            "target_conditioned_copy_availability",
            "exact_internal_op_starts",
        ],
        "may_grant_for_next_pilot": [
            "book_order",
            "book_length",
            "seed_books_0_9",
            "literal_innovation_tape_as_paid_input",
            "previously_emitted_digits",
        ],
        "promotion_requirements": [
            "reduce internal operation-start or copy/literal trigger fields after paid corrections",
            "generate nontrivial held-out books or operation starts above shuffled/permuted controls",
            "avoid target-text availability except as a separately labeled diagnostic lower bound",
            "keep row0/plaintext/translation unchanged",
        ],
    }
    return {
        "case_reopened": False,
        "classification": "GENERATION_ROUTE_FRONTIER_SYNTHESIS",
        "compression_bound_status": "unchanged",
        "decision": {
            "closed_route_family": "operation_token_decomposition_and_sequence_reuse",
            "generator_promoted": False,
            "next_route": open_route["name"],
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {name: rel(path) for name, path in INPUTS.items()},
        "open_route": open_route,
        "plaintext_claim": False,
        "route_rows": rows,
        "schema": "generative_route_frontier_synthesis.v1",
        "scope": "analysis_only_decision_synthesis_after_operation_token_route_failures",
        "summary": {
            "closed_routes": closed_routes,
            "operation_token_family_closed": True,
            "promoted_generators": 0,
            "routes_reviewed": len(rows),
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# Generative Route Frontier Synthesis",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Consolidate recent operation-token generation routes before opening another "
        "gate. This synthesis asks whether the whole family should remain the main "
        "route after hidden state, schedule state, multiset/order, within-book "
        "ordering, and sequence mutation all failed promotion criteria.",
        "",
        "## Route Matrix",
        "",
        "| Route | Classification | Signal | Controls | Decision |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result["route_rows"]:
        lines.append(
            f"| `{row['route']}` | `{row['classification']}` | `{row['positive_signal']}` | "
            f"`{row['control_result']}` | `{row['decision']}` |"
        )
    open_route = result["open_route"]
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The operation-token route family is closed as the main route under current "
            "evidence. It can still provide diagnostics, but not the next generator "
            "attempt.",
            "",
            f"Next constructive route: `{open_route['name']}`.",
            "",
            "It should work at digit/content-boundary level and must not grant the "
            "operation-token sequence, book multiset, within-book order, target-conditioned "
            "copy availability, or exact internal starts.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    open_route = result["open_route"]
    lines = [
        "# Final Generative Route Frontier Synthesis Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "After the recent operation-token route failures, should the next main "
        "attempt still decompose operation tokens, or should it move back to a "
        "digit/content-boundary transducer?",
        "",
        "## Result",
        "",
        f"`{result['summary']['routes_reviewed']}` recent operation-token routes were "
        "reviewed. Promoted generators: `0`. The closed family is "
        "`operation_token_decomposition_and_sequence_reuse`.",
        "",
        "## Decision",
        "",
        f"The next constructive route is `{open_route['name']}`: a digit-level "
        "content/boundary transducer that pays an innovation tape and tries to "
        "derive internal operation starts and copy/literal triggers without "
        "target-conditioned copy availability.",
        "",
        "Row0, plaintext, translation, and compression_bound remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_generative_route_frontier_synthesis.py](../scripts/01_generative_route_frontier_synthesis.py)",
        "- [01_generative_route_frontier_synthesis.json](test_results/01_generative_route_frontier_synthesis.json)",
        "- [01_generative_route_frontier_synthesis.md](test_results/01_generative_route_frontier_synthesis.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
