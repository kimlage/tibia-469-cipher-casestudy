#!/usr/bin/env python3
"""Joint chunk-origin route audit.

The executable tape representation reached a frontier. This gate does not open
another local residual-field codec. It aggregates the current route evidence and
derives falsifiable requirements for the next representation change: a joint
chunk-origin program that explains target chunks, source choice, segmentation,
and innovation together.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "joint_chunk_origin_route_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

FRONTIER = (
    ROOT
    / "analysis"
    / "executable_program_frontier_synthesis_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_program_frontier_synthesis.json"
)
CHUNK_DICT = (
    ROOT
    / "analysis"
    / "target_chunk_dictionary_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_chunk_dictionary_gate.json"
)
CHUNK_SIGNATURE = (
    ROOT
    / "analysis"
    / "target_chunk_signature_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_chunk_signature_gate.json"
)
SOURCE_COLLAPSE = (
    ROOT
    / "analysis"
    / "target_conditioned_source_collapse_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_conditioned_source_collapse_gate.json"
)
SEGMENTATION = (
    ROOT
    / "analysis"
    / "segmentation_decision_audit_20260621"
    / "reports"
    / "test_results"
    / "02_structural_segmentation_hypothesis_audit.json"
)
SOURCE_BOUNDARY = (
    ROOT
    / "analysis"
    / "segmentation_decision_audit_20260621"
    / "reports"
    / "test_results"
    / "15_source_boundary_alignment_audit.json"
)

JSON_OUT = TEST_RESULTS / "01_joint_chunk_origin_route_gate.json"
MD_OUT = TEST_RESULTS / "01_joint_chunk_origin_route_gate.md"
FINAL_OUT = FRONT / "reports" / "final_joint_chunk_origin_route_audit.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def maybe(path: Path) -> Any | None:
    return load_json(path) if path.exists() else None


def build_result() -> dict:
    frontier = load_json(FRONTIER)
    chunk_dict = load_json(CHUNK_DICT)
    chunk_sig = load_json(CHUNK_SIGNATURE)
    source_collapse = maybe(SOURCE_COLLAPSE)
    segmentation = maybe(SEGMENTATION)
    source_boundary = maybe(SOURCE_BOUNDARY)

    dict_summary = chunk_dict["summary"]
    sig_summary = chunk_sig["summary"]
    frontier_summary = frontier["summary"]

    route_rows = [
        {
            "route": "exact_target_chunk_dictionary",
            "status": "REJECTED",
            "evidence": (
                f"unique chunks {dict_summary['all_unique_chunks']}/{dict_summary['operation_chunk_count']}; "
                f"copy unique {dict_summary['copy_unique_chunks']}/{dict_summary['copy_chunk_count']}; "
                f"dictionary delta {dict_summary['all_chunk_dictionary_delta_vs_baseline']:.3f} bits"
            ),
            "reason": "mostly declares target payload rather than generating chunks",
        },
        {
            "route": "coarse_target_chunk_signature",
            "status": "REJECTED",
            "evidence": (
                f"best non-payload family {sig_summary['best_non_payload_family']} has "
                f"{sig_summary['best_non_payload_signature_count']} signatures and "
                f"{sig_summary['best_non_payload_singleton_rows']} singleton rows; payload signatures rely on target digits"
            ),
            "reason": "non-payload signatures leave exact chunks unresolved; payload signatures are target-text oracles",
        },
        {
            "route": "current_external_tape_program",
            "status": "FRONTIER",
            "evidence": (
                f"roundtrip {frontier_summary['roundtrip_70_70']}; promoted executable reductions "
                f"{frontier_summary['promoted_executable_tape_reductions']}; rejected routes "
                f"{frontier_summary['rejected_executable_program_routes']}"
            ),
            "reason": "valid ledger but no tape reducer promotes inside decoder",
        },
        {
            "route": "target_conditioned_source_collapse",
            "status": "LOWER_BOUND_ONLY",
            "evidence": "source choice collapses after target chunk is granted, but target chunk remains the missing generator",
            "reason": "useful lower bound for a future joint program, not decoder-visible",
        },
        {
            "route": "operation_boundary_chunk_reuse",
            "status": "REJECTED",
            "evidence": "prior source-boundary alignment found no single-prior-chunk copy explanation and source starts/end rarely align to op boundaries",
            "reason": "operation chunks are not reused as simple block units",
        },
    ]

    requirements = [
        {
            "requirement": "generate_or_keep_target_chunks_without_exact_chunk_dictionary",
            "testable_gate": "prefix/family holdout must keep true chunk stream in beam above same-length/chunk-shuffled controls",
            "failure_condition": "if exact chunks must be declared or payload signatures are used, route collapses to rejected dictionary/signature accounts",
        },
        {
            "requirement": "choose_source_and_length_jointly_after_chunk_hypothesis",
            "testable_gate": "given generated chunk candidates, earliest-source collapse should reduce source tape with paid exceptions",
            "failure_condition": "if source policy still needs future target text outside the generated chunk candidate, source remains external",
        },
        {
            "requirement": "consume_literal_innovation_as_part_of_chunk_origin",
            "testable_gate": "literal/copy chunk candidates must share one innovation process and improve over separate literal payload + composition/source tapes",
            "failure_condition": "if literal tape remains a separate payload declaration, representation has not changed enough",
        },
        {
            "requirement": "execute_decoder_without_atlas_corrections_dominating",
            "testable_gate": "controller must reduce executable ledger after model, beam-rank, and correction costs",
            "failure_condition": "if corrections exceed direct external tape declaration, it is only a predictive clue",
        },
        {
            "requirement": "survive_controls",
            "testable_gate": "prefix holdout, public-bookcase family holdout, same-multiset chunk shuffle, same-length random chunks, and permuted train controls",
            "failure_condition": "if gains vanish under controls, classify as parser/compressor artifact",
        },
    ]

    next_gate = {
        "name": "joint_chunk_origin_beam_pilot",
        "purpose": "construct a beam over chunk-origin hypotheses instead of field tapes",
        "granted": [
            "book order",
            "book_length",
            "seed books 0..9",
            "row0 as exogenous substrate",
        ],
        "not_granted": [
            "exact target chunks",
            "copy source tape",
            "exact coarse sequence atlas",
            "composition index",
            "literal payload as separate tape",
        ],
        "minimum_success": [
            "at least one nontrivial held-out book exact without full atlas correction",
            "or reduction of combined chunk/source/literal external ledger after paid corrections",
            "and stronger than same-length/chunk-shuffled controls",
        ],
    }

    return {
        "case_reopened": False,
        "classification": "JOINT_CHUNK_ORIGIN_ROUTE_REQUIRED",
        "compression_bound_status": "unchanged",
        "decision": {
            "next_frontier": next_gate["name"],
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "chunk_dictionary": rel(CHUNK_DICT),
            "chunk_signature": rel(CHUNK_SIGNATURE),
            "executable_frontier": rel(FRONTIER),
            "segmentation": rel(SEGMENTATION) if SEGMENTATION.exists() else None,
            "source_boundary": rel(SOURCE_BOUNDARY) if SOURCE_BOUNDARY.exists() else None,
            "source_collapse": rel(SOURCE_COLLAPSE) if SOURCE_COLLAPSE.exists() else None,
        },
        "next_gate": next_gate,
        "plaintext_claim": False,
        "requirements": requirements,
        "route_rows": route_rows,
        "scope": "analysis_only_joint_chunk_origin_route_selection",
        "summary": {
            "rejected_routes": sum(row["status"] == "REJECTED" for row in route_rows),
            "frontier_routes": sum(row["status"] == "FRONTIER" for row in route_rows),
            "lower_bound_only_routes": sum(row["status"] == "LOWER_BOUND_ONLY" for row in route_rows),
            "next_gate": next_gate["name"],
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict) -> None:
    lines = [
        "# Joint Chunk-Origin Route Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Select the next representation route after the executable tape ledger reached "
        "a practical frontier. This gate does not promote a formula; it prevents the "
        "next work from repeating exact chunk dictionaries, shallow signatures, or "
        "local tape codecs that have already failed.",
        "",
        "## Route Matrix",
        "",
        "| Route | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for row in result["route_rows"]:
        lines.append(f"| `{row['route']}` | `{row['status']}` | {row['evidence']} |")

    lines.extend(
        [
            "",
            "## Requirements For The Next Gate",
            "",
        ]
    )
    for req in result["requirements"]:
        lines.append(
            f"- `{req['requirement']}`: {req['testable_gate']} Failure: {req['failure_condition']}"
        )

    next_gate = result["next_gate"]
    lines.extend(
        [
            "",
            "## Next Constructive Gate",
            "",
            f"- Name: `{next_gate['name']}`.",
            f"- Purpose: {next_gate['purpose']}.",
            f"- Minimum success: `{'; '.join(next_gate['minimum_success'])}`.",
            "",
            "## Decision",
            "",
            "The aligned next route is a joint chunk-origin beam pilot. It must explain "
            "chunk candidates, source choice, segmentation, and innovation together. "
            "Exact chunks, shallow signatures, current external tapes, and operation "
            "boundary block reuse are not sufficient under current evidence.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict) -> None:
    s = result["summary"]
    lines = [
        "# Final Joint Chunk-Origin Route Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "After the executable tape representation reached a frontier, what is the "
        "next representation change that can plausibly move toward a generative "
        "mechanism without reopening rejected local routes?",
        "",
        "## Evidence",
        "",
        f"- Rejected routes consolidated: `{s['rejected_routes']}`.",
        f"- Frontier routes: `{s['frontier_routes']}`.",
        f"- Lower-bound-only routes: `{s['lower_bound_only_routes']}`.",
        f"- Next constructive gate: `{s['next_gate']}`.",
        "",
        "Exact target-chunk dictionaries and shallow chunk signatures are rejected. "
        "The executable external-tape program is useful as a ledger, but has no "
        "promoted tape reductions. Target-conditioned source collapse remains only "
        "a lower bound because it grants the missing target chunk.",
        "",
        "## Decision",
        "",
        "The next aligned route is `joint_chunk_origin_beam_pilot`: a representation "
        "that proposes chunk-origin hypotheses jointly with source choice, length, "
        "and literal innovation. Promotion should require nontrivial held-out exact "
        "books/ops or a paid reduction of the combined chunk/source/literal ledger, "
        "above chunk-shuffled and same-length controls.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_joint_chunk_origin_route_gate.py](../scripts/01_joint_chunk_origin_route_gate.py)",
        "- [01_joint_chunk_origin_route_gate.json](test_results/01_joint_chunk_origin_route_gate.json)",
        "- [01_joint_chunk_origin_route_gate.md](test_results/01_joint_chunk_origin_route_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = build_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
