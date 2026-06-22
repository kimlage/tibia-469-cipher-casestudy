from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

OUT_STEM = "01_skeleton_generation_route_review"

INPUTS = {
    "generation_boundary": ROOT
    / "analysis/generation_boundary_closure_audit_20260621/reports/test_results/01_generation_boundary_closure_audit.json",
    "source_free_skeleton": ROOT
    / "analysis/source_free_skeleton_generation_audit_20260621/reports/test_results/02_source_free_skeleton_grammar_gate.json",
    "operation_length_markov": ROOT
    / "analysis/operation_length_markov_audit_20260621/reports/test_results/01_operation_length_markov_gate.json",
    "operation_cutpoint_scaling": ROOT
    / "analysis/operation_cutpoint_scaling_audit_20260621/reports/test_results/01_operation_cutpoint_scaling_gate.json",
    "operation_cutpoint_lattice": ROOT
    / "analysis/operation_cutpoint_lattice_audit_20260621/reports/test_results/01_operation_cutpoint_lattice_gate.json",
    "operation_recursive_partition": ROOT
    / "analysis/operation_recursive_partition_audit_20260621/reports/test_results/01_operation_recursive_partition_gate.json",
    "target_digit_process": ROOT
    / "analysis/target_digit_process_audit_20260621/reports/test_results/01_target_digit_process_gate.json",
    "target_boundary_threshold": ROOT
    / "analysis/target_digit_boundary_threshold_audit_20260621/reports/test_results/01_target_digit_boundary_threshold_gate.json",
    "target_boundary_miss_residual": ROOT
    / "analysis/target_digit_boundary_miss_residual_audit_20260621/reports/test_results/01_target_digit_boundary_miss_residual_gate.json",
    "target_boundary_miss_transition": ROOT
    / "analysis/target_digit_boundary_miss_transition_audit_20260621/reports/test_results/01_target_digit_boundary_miss_transition_gate.json",
    "literal_payload": ROOT
    / "analysis/literal_payload_generation_audit_20260621/reports/test_results/02_literal_payload_context_gate.json",
    "copy_source": ROOT
    / "analysis/copy_source_generation_audit_20260621/reports/test_results/03_copy_source_context_gate.json",
}


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


def route_rows(data: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    boundary = data["generation_boundary"]["summary"]
    source_free = data["source_free_skeleton"]["summary"]
    length_markov = data["operation_length_markov"]["summary"]
    scaling = data["operation_cutpoint_scaling"]["summary"]
    lattice = data["operation_cutpoint_lattice"]["summary"]
    recursive = data["operation_recursive_partition"]["summary"]
    digit = data["target_digit_process"]["summary"]
    threshold = data["target_boundary_threshold"]["summary"]
    residual = data["target_boundary_miss_residual"]["summary"]
    transition = data["target_boundary_miss_transition"]["summary"]
    literal = data["literal_payload"]["summary"]
    source = data["copy_source"]["summary"]
    return [
        {
            "route": "dependency_boundary",
            "status": "OPEN_BLOCKER",
            "evidence": (
                f"promoted_generators={boundary['promoted_generator_count']}/5; "
                f"materialized_unit_floor={boundary['total_materialized_units_floor']}; "
                "next_blocker=operation_skeleton"
            ),
            "next_action": "keep operation_skeleton as first-class blocker",
        },
        {
            "route": "simple_source_free_skeleton_grammar",
            "status": "REJECTED_CONTROL",
            "evidence": (
                f"best_exact_books={source_free['best_exact_books']}/"
                f"{source_free['best_total_books']}; "
                f"op_hits={source_free['best_op_hits']}/"
                f"{source_free['op_count']}; "
                f"preq_cover_all={source_free['prequential_cover_all_test_books_cells']}/"
                f"{source_free['prequential_cells']}"
            ),
            "next_action": "do not continue simple context grammar sweeps",
        },
        {
            "route": "operation_length_contexts",
            "status": "REJECTED_CONTROL",
            "evidence": (
                f"best_exact_books={length_markov['best_full_exact_books']}/"
                f"{length_markov['book_count']}; "
                f"rowwise_exact_lengths={length_markov['best_rowwise_exact_lengths']}/"
                f"{length_markov['operation_count']}; "
                f"preq_cover_all={length_markov['prequential_cover_all_cells']}/"
                f"{length_markov['prequential_cells']}"
            ),
            "next_action": "do not rerun local length Markov/context policies",
        },
        {
            "route": "scaled_or_lattice_cutpoint_geometry",
            "status": "REJECTED_CONTROL",
            "evidence": (
                f"scaling_exact_books={scaling['best_exact_books']}/"
                f"{scaling['book_count']} but record_delta={scaling['best_delta_vs_exact_atlas_records']}; "
                f"lattice_hits={lattice['best_hits']}/{lattice['internal_cutpoint_count']} "
                f"below_random_mean_lift={lattice['best_hit_lift_vs_random_mean']:.3f}; "
                f"recursive_hits={recursive['best_hits']}/{recursive['internal_cutpoint_count']}"
            ),
            "next_action": "do not continue proportional grid/recursive split paths",
        },
        {
            "route": "target_digit_stream",
            "status": "PROMOTED_MECHANICAL_CLUE_NOT_GENERATOR",
            "evidence": (
                f"best_model={digit['derived60_best_model']}; "
                f"derived60_bpd={digit['derived60_best_test_bpd']:.6f}; "
                f"beats_shuffled={digit['derived60_beats_shuffled_best_p95']}; "
                f"promotes_generator={digit['promotes_digit_process_generator']}"
            ),
            "next_action": "promote only as target-stream prior; exact residual still required",
        },
        {
            "route": "target_digit_boundary_candidates",
            "status": "PROMOTED_DEPENDENCY_REDUCTION_NOT_GENERATOR",
            "evidence": (
                f"best_policy={threshold['best_policy']}; "
                f"saving={threshold['best_saving_after_policy']:.3f}; "
                f"tp_fp_fn={threshold['best_true_positive']}/"
                f"{threshold['best_false_positive']}/{threshold['best_false_negative']}; "
                f"exact_books={threshold['best_exact_books']}/{threshold['book_count']}"
            ),
            "next_action": "retain as pruning/coding clue only",
        },
        {
            "route": "boundary_residual_labels",
            "status": "WEAK_OR_REJECTED",
            "evidence": (
                f"residual_delta={residual['best_delta_vs_threshold_bits']:.3f} "
                f"but preq={residual['prequential_positive_delta_cells']}/"
                f"{residual['prequential_cells']}; "
                f"transition_best={transition['best_feature']} "
                f"beats_random_p95={transition['best_beats_random_p95']}"
            ),
            "next_action": "stop treating miss labels as the next generator route",
        },
        {
            "route": "downstream_after_exact_skeleton",
            "status": "DEFERRED_REJECTED_UNTIL_SKELETON_GENERATED",
            "evidence": (
                f"literal_promoted={literal['promotes_literal_payload_generator']}; "
                f"copy_source_promoted={source['promotes_copy_source_generator']}; "
                "both assume exact skeleton is granted"
            ),
            "next_action": "defer source/payload work until skeleton dependency falls",
        },
    ]


def make_result() -> dict[str, Any]:
    data = {name: load_json(path) for name, path in INPUTS.items()}
    for name, payload in data.items():
        assert_boundary(name, payload)
    routes = route_rows(data)
    summary = {
        "route_count": len(routes),
        "promoted_generator_routes": sum(
            1 for row in routes if row["status"].startswith("PROMOTED_GENERATOR")
        ),
        "promoted_dependency_or_clue_routes": sum(
            1
            for row in routes
            if row["status"] in {
                "PROMOTED_MECHANICAL_CLUE_NOT_GENERATOR",
                "PROMOTED_DEPENDENCY_REDUCTION_NOT_GENERATOR",
            }
        ),
        "rejected_or_weak_routes": sum(
            1
            for row in routes
            if row["status"] in {
                "REJECTED_CONTROL",
                "WEAK_OR_REJECTED",
                "DEFERRED_REJECTED_UNTIL_SKELETON_GENERATED",
            }
        ),
        "open_blocker": "operation_skeleton",
        "continue_route": "joint_target_stream_parser_or_latent_state",
        "stop_routes": [
            "simple_source_free_skeleton_grammar",
            "local_operation_length_context_sweeps",
            "proportional_cutpoint_grids",
            "boundary_miss_label_classification",
            "downstream_source_payload_before_skeleton",
        ],
        "decision": (
            "The current evidence says to stop local cutpoint/length/miss-label "
            "sweeps. The only live route that still aligns with a generator is a "
            "joint target-stream/parser or explicit latent-state account that "
            "emits digits and boundaries together, rather than choosing endpoints "
            "after the target text is known."
        ),
    }
    return {
        "schema": "skeleton_generation_route_review_v1",
        "scope": "analysis_only_route_selection_after_boundary_frontier",
        "inputs": {name: rel(path) for name, path in INPUTS.items()},
        "routes": routes,
        "summary": summary,
        "classification": "skeleton_generation_route_review_boundary_frontier_saturated",
        "decision": {
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
            "recommended_next_route": summary["continue_route"],
            "case_reopened": False,
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Skeleton Generation Route Review",
        "",
        "Classification: `skeleton_generation_route_review_boundary_frontier_saturated`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Step back from local boundary and length probes and decide which route,",
        "if any, still moves toward a mechanical generator for the 70 books.",
        "",
        "## Summary",
        "",
        f"- Routes reviewed: `{s['route_count']}`.",
        f"- Promoted generator routes: `{s['promoted_generator_routes']}`.",
        f"- Promoted clue/dependency routes: `{s['promoted_dependency_or_clue_routes']}`.",
        f"- Rejected/weak/deferred routes: `{s['rejected_or_weak_routes']}`.",
        f"- Open blocker: `{s['open_blocker']}`.",
        f"- Recommended next route: `{s['continue_route']}`.",
        "",
        s["decision"],
        "",
        "## Route Ledger",
        "",
        "| Route | Status | Evidence | Next action |",
        "| --- | --- | --- | --- |",
    ]
    for row in result["routes"]:
        lines.append(
            f"| `{row['route']}` | `{row['status']}` | {row['evidence']} | {row['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Stop Routes",
            "",
        ]
    )
    for route in s["stop_routes"]:
        lines.append(f"- `{route}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Do not promote any new skeleton generator.",
            "- Retain `prev2` target-digit and boundary threshold evidence only as mechanical clues/dependency reducers.",
            "- Stop local boundary-miss and simple length/cutpoint rule sweeps unless a new latent state or joint target-stream parser is introduced.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(result)
    print(json.dumps({"output": rel(TEST_RESULTS / f"{OUT_STEM}.json")}, indent=2))


if __name__ == "__main__":
    main()
