#!/usr/bin/env python3
"""Latent-state route synthesis audit.

After the executable tape frontier and the first joint chunk-origin pilots, the
remaining blocker is no longer a single residual field. This synthesis turns the
recent negative/weak gates into an operational route decision: stop local
length/content/source priors unless they are part of a latent/nonlocal state
program that reduces the executable ledger under holdout.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "latent_state_route_synthesis_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

EXEC_FRONTIER = (
    ROOT
    / "analysis"
    / "executable_program_frontier_synthesis_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_program_frontier_synthesis.json"
)
ROUTE_GATE = (
    ROOT
    / "analysis"
    / "joint_chunk_origin_route_audit_20260622"
    / "reports"
    / "test_results"
    / "01_joint_chunk_origin_route_gate.json"
)
BUCKET_PILOT = (
    ROOT
    / "analysis"
    / "joint_chunk_origin_beam_pilot_audit_20260622"
    / "reports"
    / "test_results"
    / "01_bucket_chunk_origin_beam_pilot.json"
)
LENGTH_PRIOR = (
    ROOT
    / "analysis"
    / "chunk_length_prior_integration_audit_20260622"
    / "reports"
    / "test_results"
    / "01_chunk_length_prior_integration_gate.json"
)
CONTENT_PRIOR = (
    ROOT
    / "analysis"
    / "markov_chunk_content_prior_audit_20260622"
    / "reports"
    / "test_results"
    / "01_markov_chunk_content_prior_gate.json"
)
STATEFUL_CONTROL = (
    ROOT
    / "analysis"
    / "stateful_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_stateful_control_program_gate.json"
)
UNIFIED_CONTROL = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_control_program_tests.json"
)

JSON_OUT = TEST_RESULTS / "01_latent_state_route_synthesis.json"
MD_OUT = TEST_RESULTS / "01_latent_state_route_synthesis.md"
FINAL_OUT = FRONT / "reports" / "final_latent_state_route_synthesis_audit.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    decision = data.get("decision", {})
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")


def make_result() -> dict[str, Any]:
    exec_frontier = load_json(EXEC_FRONTIER)
    route_gate = load_json(ROUTE_GATE)
    bucket = load_json(BUCKET_PILOT)
    length = load_json(LENGTH_PRIOR)
    content = load_json(CONTENT_PRIOR)
    stateful = load_json(STATEFUL_CONTROL)
    unified = load_json(UNIFIED_CONTROL)
    for name, data in [
        ("executable_frontier", exec_frontier),
        ("joint_chunk_origin_route", route_gate),
        ("bucket_chunk_origin_beam", bucket),
        ("chunk_length_prior", length),
        ("markov_content_prior", content),
        ("stateful_control_program", stateful),
        ("unified_control_program", unified),
    ]:
        assert_boundary(name, data)

    exec_summary = exec_frontier["summary"]
    bucket_summary = bucket["summary"]
    length_summary = length["summary"]
    content_summary = content["summary"]
    stateful_best_name = stateful["decision"]["best_by_bits"]
    stateful_best = stateful["models"][stateful_best_name]
    stateful_total_saving = sum(float(row["saving_bits"]) for row in stateful_best["cutoff_rows"])
    stateful_greedy_exact = sum(int(row["greedy_exact_books"]) for row in stateful_best["cutoff_rows"])
    stateful_beam_nontrivial = sum(
        int(row["beam20_nontrivial_exact_books"]) for row in stateful_best["cutoff_rows"]
    )
    unified_holdout = unified["unified_program_holdout"]["summary"]
    unified_coupling = unified["control_tape_coupling_gate"]

    route_rows = [
        {
            "route": "current_executable_tape_program",
            "status": "FRONTIER",
            "evidence": (
                f"roundtrip={exec_summary['roundtrip_70_70']}; "
                f"promoted_reductions={exec_summary['promoted_executable_tape_reductions']}; "
                f"external_bits_excluding_seed={exec_summary['external_bits_excluding_seed']:.3f}"
            ),
            "decision": "ledger retained, generator not promoted",
        },
        {
            "route": "joint_chunk_origin_route",
            "status": "OPEN_ROUTE",
            "evidence": (
                f"next_gate={route_gate['summary']['next_gate']}; "
                f"rejected_routes={route_gate['summary']['rejected_routes']}"
            ),
            "decision": "route remains aligned only if it becomes a joint state program",
        },
        {
            "route": "bucket_chunk_origin_rank",
            "status": "WEAK_CLUE_NOT_EXECUTABLE",
            "evidence": (
                f"rank_bits={bucket_summary['bucket_best_rank_bits']:.3f}; "
                f"exact_hint_bits={bucket_summary['exact_length_copy_hint_bits']:.3f}; "
                f"top80={bucket_summary['topk_hits']['80']}/{bucket_summary['copy_ops']}"
            ),
            "decision": "bucket-level candidate sets remain too broad",
        },
        {
            "route": "copy_length_prior_then_hint",
            "status": "POSTHOC_NOT_PROMOTED",
            "evidence": (
                f"full_fit_delta={length_summary['full_fit_delta_vs_current_composition_plus_hint']:.3f}; "
                f"holdout_positive={length_summary['holdout_positive_saving_cells']}/5"
            ),
            "decision": "simple length context cannot be the next route",
        },
        {
            "route": "prev2_content_prior_for_chunks",
            "status": "REJECTED_CONTROL",
            "evidence": (
                f"content_first_delta={content_summary['total_best_content_first_delta_vs_freq_recent']:.3f}; "
                f"beats_freq={content_summary['content_first_beats_freq_recent_cells']}/5"
            ),
            "decision": "prev2 remains digit/boundary clue, not chunk selector",
        },
        {
            "route": "observable_stateful_control",
            "status": "REJECTED_CONTROL",
            "evidence": (
                f"best_model={stateful_best_name}; "
                f"delta_vs_independent={stateful_total_saving:.3f}; "
                f"greedy_exact_books={stateful_greedy_exact}; "
                f"beam20_nontrivial={stateful_beam_nontrivial}"
            ),
            "decision": "observable previous/remaining state is not enough",
        },
        {
            "route": "unified_control_coupling",
            "status": "PARTIAL_CLUE_NOT_GENERATOR",
            "evidence": (
                f"exact_books_without_atlas={unified_holdout['exact_books_without_atlas']}; "
                f"exact_ops_without_atlas={unified_holdout['exact_ops_without_atlas']}; "
                f"promoted_couplings={len(unified_coupling['promoted_relations'])}"
            ),
            "decision": "coupling clue exists but does not generate program",
        },
    ]

    closed_local_routes = sum(
        row["status"] in {"POSTHOC_NOT_PROMOTED", "REJECTED_CONTROL", "WEAK_CLUE_NOT_EXECUTABLE"}
        for row in route_rows
    )
    next_gate = {
        "name": "latent_nonlocal_state_program_pilot",
        "purpose": (
            "test a hidden/nonlocal state that jointly emits or keeps in beam "
            "operation control, length/chunk origin, literal innovation, and copy "
            "availability, rather than scoring those fields independently"
        ),
        "granted": [
            "book order",
            "book lengths",
            "seed books 0..9",
            "row0 as exogenous substrate",
            "previous emitted material",
        ],
        "not_granted": [
            "exact operation skeleton",
            "exact type:length stream",
            "exact copy length",
            "exact target chunk",
            "copy source/hint tape",
            "literal payload as an independent tape",
        ],
        "minimum_success": [
            "nontrivial held-out exact book or exact operation subsequence without atlas correction",
            "or paid reduction of combined control+length+literal+copy-hint ledger under prefix/family holdout",
            "and stronger than same-multiset, same-length, digit-shuffled, and permuted-order controls",
        ],
        "immediate_negative_condition": [
            "if it decomposes into independent local priors for length, content, or source, classify as already closed",
            "if correction bits dominate direct external tape declaration, classify as parser clue only",
        ],
    }

    return {
        "case_reopened": False,
        "classification": "LATENT_NONLOCAL_STATE_ROUTE_REQUIRED",
        "compression_bound_status": "unchanged",
        "decision": {
            "continue_joint_chunk_origin": True,
            "local_prior_routes_closed": True,
            "next_gate": next_gate["name"],
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "bucket_chunk_origin_beam": rel(BUCKET_PILOT),
            "chunk_length_prior": rel(LENGTH_PRIOR),
            "executable_frontier": rel(EXEC_FRONTIER),
            "joint_chunk_origin_route": rel(ROUTE_GATE),
            "markov_content_prior": rel(CONTENT_PRIOR),
            "stateful_control_program": rel(STATEFUL_CONTROL),
            "unified_control_program": rel(UNIFIED_CONTROL),
        },
        "next_gate": next_gate,
        "plaintext_claim": False,
        "route_rows": route_rows,
        "schema": "latent_state_route_synthesis.v1",
        "scope": "analysis_only_route_synthesis_after_local_joint_chunk_origin_priors",
        "summary": {
            "closed_local_routes": closed_local_routes,
            "frontier_routes": sum(row["status"] == "FRONTIER" for row in route_rows),
            "open_routes": sum(row["status"] == "OPEN_ROUTE" for row in route_rows),
            "partial_clues": sum("CLUE" in row["status"] for row in route_rows),
            "next_gate": next_gate["name"],
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# Latent-State Route Synthesis",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Consolidate the executable frontier and the first joint chunk-origin pilots "
        "so the next work does not keep reopening independent local priors.",
        "",
        "## Route Matrix",
        "",
        "| Route | Status | Evidence | Decision |",
        "| --- | --- | --- | --- |",
    ]
    for row in result["route_rows"]:
        lines.append(
            f"| `{row['route']}` | `{row['status']}` | {row['evidence']} | {row['decision']} |"
        )
    gate = result["next_gate"]
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            f"- Name: `{gate['name']}`.",
            f"- Purpose: {gate['purpose']}.",
            "- Minimum success:",
        ]
    )
    for item in gate["minimum_success"]:
        lines.append(f"  - {item}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The next aligned work is a latent/nonlocal state program. A new gate should "
            "jointly reduce control, length/chunk origin, literal innovation, and copy "
            "availability. More isolated length, content, or source priors are closed "
            "unless embedded in that joint program.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Latent-State Route Synthesis Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "After the executable tape frontier and the first joint chunk-origin pilots, "
        "what representation can still plausibly move toward a real generator?",
        "",
        "## Evidence",
        "",
        f"- Closed local routes: `{s['closed_local_routes']}`.",
        f"- Frontier routes: `{s['frontier_routes']}`.",
        f"- Open representation routes: `{s['open_routes']}`.",
        f"- Next constructive gate: `{s['next_gate']}`.",
        "",
        "The recent local rescues do not promote: bucket chunk-origin is too broad, "
        "copy-length prior is posthoc under holdout, `prev2` content does not rank "
        "chunks, and observable stateful control remains worse than independent "
        "declaration.",
        "",
        "## Decision",
        "",
        "Continue only with a latent/nonlocal state program that jointly accounts for "
        "control, length/chunk origin, literal innovation, and copy availability. "
        "Do not continue independent length/content/source priors as a main route.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_latent_state_route_synthesis.py](../scripts/01_latent_state_route_synthesis.py)",
        "- [01_latent_state_route_synthesis.json](test_results/01_latent_state_route_synthesis.json)",
        "- [01_latent_state_route_synthesis.md](test_results/01_latent_state_route_synthesis.md)",
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
