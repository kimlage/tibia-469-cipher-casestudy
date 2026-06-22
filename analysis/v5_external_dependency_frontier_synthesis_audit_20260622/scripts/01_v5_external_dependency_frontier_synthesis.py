#!/usr/bin/env python3
"""V5 external dependency frontier synthesis.

This is a route-selection audit, not a new formula. It consolidates the v5
executable ledger, the post-v5 rejected copy-origin routes, and the already
closed literal-payload routes to decide what representation can still plausibly
move toward a real generator.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "v5_external_dependency_frontier_synthesis_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

EXECUTABLE_V5 = (
    ROOT
    / "analysis"
    / "executable_v5_source_endpoint_memory_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v5_source_endpoint_memory_gate.json"
)
V5_ROBUSTNESS = (
    ROOT
    / "analysis"
    / "executable_v5_source_endpoint_memory_robustness_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v5_source_endpoint_memory_robustness_gate.json"
)
V5_CASCADE = (
    ROOT
    / "analysis"
    / "v5_endpoint_cascade_stability_audit_20260622"
    / "reports"
    / "test_results"
    / "01_v5_endpoint_cascade_stability_gate.json"
)
NEAR_MARK = (
    ROOT
    / "analysis"
    / "v5_near_source_mark_offset_audit_20260622"
    / "reports"
    / "test_results"
    / "01_v5_near_source_mark_offset_gate.json"
)
MARK_IDENTITY = (
    ROOT
    / "analysis"
    / "v5_mark_identity_stream_audit_20260622"
    / "reports"
    / "test_results"
    / "01_v5_mark_identity_stream_gate.json"
)
LITERAL_GENERATION_FINAL = (
    ROOT
    / "analysis"
    / "literal_payload_generation_audit_20260621"
    / "reports"
    / "final_literal_payload_generation_audit.md"
)
LITERAL_REFERENCE_FINAL = (
    ROOT
    / "analysis"
    / "literal_payload_reference_subcodec_audit_20260621"
    / "reports"
    / "final_literal_payload_reference_subcodec_audit.md"
)
SHARED_TAPE = (
    ROOT
    / "analysis"
    / "shared_innovation_tape_audit_20260622"
    / "reports"
    / "test_results"
    / "01_shared_literal_length_tape_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_v5_external_dependency_frontier_synthesis.json"
MD_OUT = TEST_RESULTS / "01_v5_external_dependency_frontier_synthesis.md"
FINAL_OUT = FRONT / "reports" / "final_v5_external_dependency_frontier_synthesis_audit.md"


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


def make_result() -> dict[str, Any]:
    v5 = load_json(EXECUTABLE_V5)
    robust = load_json(V5_ROBUSTNESS)
    cascade = load_json(V5_CASCADE)
    near = load_json(NEAR_MARK)
    mark = load_json(MARK_IDENTITY)
    shared = load_json(SHARED_TAPE)
    for name, data in [
        ("executable_v5", v5),
        ("v5_robustness", robust),
        ("v5_endpoint_cascade", cascade),
        ("near_source_mark_offset", near),
        ("mark_identity_stream", mark),
        ("shared_literal_length_tape", shared),
    ]:
        assert_boundary(name, data)

    v5_summary = v5["summary"]
    mark_summary = mark["summary"]
    near_summary = near["summary"]
    paid_components = {
        "copy_fallback_hint_bits": float(mark_summary["copy_hint_bits"]),
        "literal_payload_bits": float(v5_summary["literal_payload_bits"]),
        "residual_composition_bits": float(v5_summary["residual_composition_bits"]),
        "seed_payload_bits": float(v5_summary["seed_payload_bits"]),
        "online_x64_coarse_bits": float(v5_summary["online_x64_coarse_bits"]),
        "representation_declaration_bits": float(v5_summary["representation_declaration_bits"]),
    }
    blocker_components = {
        key: paid_components[key]
        for key in [
            "copy_fallback_hint_bits",
            "literal_payload_bits",
            "residual_composition_bits",
            "seed_payload_bits",
        ]
    }
    route_ledger = [
        {
            "route": "executable_v5_source_endpoint_memory",
            "status": "promoted",
            "evidence": (
                f"external excluding seed {v5_summary['v4_external_bits_excluding_seed']:.3f} -> "
                f"{v5_summary['v5_external_bits_excluding_seed']:.3f}; robust={robust['summary']['robust']}"
            ),
        },
        {
            "route": "v5_endpoint_priority_cascade",
            "status": "weak_fullfit_only_not_promoted",
            "evidence": (
                f"full-fit delta {cascade['summary']['best_delta_after_declaration_vs_v5']:.3f}; "
                f"prefix positive {cascade['summary']['positive_prefix_splits']}/5"
            ),
        },
        {
            "route": "near_source_mark_offset",
            "status": "rejected_lower_bound_only",
            "evidence": (
                f"offset-only delta {near_summary['invalid_source_offset_only_delta']:.3f}; "
                f"paid source delta {near_summary['paid_source_delta']:.3f}"
            ),
        },
        {
            "route": "source_mark_identity_stream",
            "status": "rejected_exact_stream",
            "evidence": (
                f"best valid {mark_summary['best_valid_model']} delta "
                f"{mark_summary['best_valid_delta_vs_copy_hint']:.3f}; invalid bucket lower bound "
                f"{mark_summary['model_deltas_vs_copy_hint']['invalid_rank_bucket_plus_offset_lower_bound']:.3f}"
            ),
        },
        {
            "route": "literal_payload_generation",
            "status": "closed_not_promoted",
            "evidence": "source-free literal payload generator rejected; prefix/holdout exact chunks 0/5",
        },
        {
            "route": "literal_reference_subcodec",
            "status": "closed_not_promoted",
            "evidence": "prior-reference recurrence loses after mode/source cost",
        },
        {
            "route": "shared_literal_length_tape",
            "status": "weak_clue_not_promoted",
            "evidence": (
                f"saving_vs_uniform {shared['summary']['saving_vs_uniform_residual_bits']:.3f} bits"
                if "summary" in shared and "saving_vs_uniform_residual_bits" in shared["summary"]
                else "literal tape retained only as weak shared-innovation clue"
            ),
        },
    ]
    next_route = {
        "name": "joint_content_origin_program",
        "description": (
            "A future constructive route must jointly model exact copy-origin mark "
            "identity and literal innovation payload as content-origin choices. "
            "Local endpoint priority, local offsets, exact rank-delta streams, and "
            "literal reference subcodecs are closed under current evidence."
        ),
        "promotion_requirements": [
            "reduce copy_fallback_hint_bits or literal_payload_bits after paying exact identity/payload costs",
            "survive prefix/suffix holdout or shuffled/source-mark controls",
            "remain executable with 70/70 roundtrip and no target-content oracle",
        ],
    }
    return {
        "case_reopened": False,
        "classification": "V5_EXTERNAL_DEPENDENCY_FRONTIER_SYNTHESIS",
        "compression_bound_status": "unchanged",
        "decision": {
            "next_constructive_route": next_route["name"],
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "blocker_components": blocker_components,
        "paid_components": paid_components,
        "inputs": {
            "executable_v5": rel(EXECUTABLE_V5),
            "literal_payload_generation_final": rel(LITERAL_GENERATION_FINAL),
            "literal_payload_reference_final": rel(LITERAL_REFERENCE_FINAL),
            "mark_identity_stream": rel(MARK_IDENTITY),
            "near_source_mark_offset": rel(NEAR_MARK),
            "shared_literal_length_tape": rel(SHARED_TAPE),
            "v5_endpoint_cascade": rel(V5_CASCADE),
            "v5_robustness": rel(V5_ROBUSTNESS),
        },
        "next_route": next_route,
        "plaintext_claim": False,
        "route_ledger": route_ledger,
        "row0_status": "unchanged_exogenous",
        "schema": "v5_external_dependency_frontier_synthesis.v1",
        "scope": "analysis_only_v5_external_dependency_frontier_synthesis",
        "summary": {
            "largest_nonseed_blocker_components": sorted(
                [
                    {"component": key, "bits": value}
                    for key, value in blocker_components.items()
                    if key != "seed_payload_bits"
                ],
                key=lambda row: row["bits"],
                reverse=True,
            ),
            "largest_nonseed_paid_components": sorted(
                [
                    {"component": key, "bits": value}
                    for key, value in paid_components.items()
                    if key != "seed_payload_bits"
                ],
                key=lambda row: row["bits"],
                reverse=True,
            ),
            "promoted_frontier": "executable_v5_source_endpoint_memory",
            "v5_external_bits_excluding_seed": float(v5_summary["v5_external_bits_excluding_seed"]),
            "v5_external_bits_including_seed": float(v5_summary["v5_external_bits_including_seed"]),
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# V5 External Dependency Frontier Synthesis",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Frontier",
        "",
        f"- Promoted frontier: `{s['promoted_frontier']}`.",
        f"- V5 external bits excluding seed: `{s['v5_external_bits_excluding_seed']:.3f}`.",
        f"- V5 external bits including seed: `{s['v5_external_bits_including_seed']:.3f}`.",
        "",
        "## Largest Non-Seed Blocker Components",
        "",
        "| Component | Bits |",
        "| --- | ---: |",
    ]
    for row in s["largest_nonseed_blocker_components"]:
        lines.append(f"| `{row['component']}` | `{row['bits']:.3f}` |")
    lines.extend(
        [
            "",
            "## Largest Non-Seed Paid Components",
            "",
            "| Component | Bits |",
            "| --- | ---: |",
        ]
    )
    for row in s["largest_nonseed_paid_components"]:
        lines.append(f"| `{row['component']}` | `{row['bits']:.3f}` |")
    lines.extend(
        [
            "",
            "## Route Ledger",
            "",
            "| Route | Status | Evidence |",
            "| --- | --- | --- |",
        ]
    )
    for row in result["route_ledger"]:
        lines.append(f"| `{row['route']}` | `{row['status']}` | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## Next Route",
            "",
            f"`{result['next_route']['name']}`: {result['next_route']['description']}",
            "",
            "Promotion requires:",
        ]
    )
    for item in result["next_route"]["promotion_requirements"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    largest = s["largest_nonseed_blocker_components"][:3]
    lines = [
        "# Final V5 External Dependency Frontier Synthesis Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This synthesis consolidates the current v5 executable frontier and the "
        "post-v5 negative gates. V5 remains the promoted executable program. "
        "The largest remaining non-seed blocker components are "
        + ", ".join(f"`{row['component']}` `{row['bits']:.3f}` bits" for row in largest)
        + ".",
        "",
        "The copy-origin local routes are now closed under current evidence: endpoint "
        "priority is full-fit only, near-mark offsets are a lower bound unless mark "
        "identity is granted, and exact mark-rank streams remain more expensive than "
        "copy hints. Literal payload generator/reference routes are also closed or "
        "weak under paid costs.",
        "",
        "## Decision",
        "",
        "`V5_EXTERNAL_DEPENDENCY_FRONTIER_SYNTHESIS`.",
        "",
        "The next aligned route is `joint_content_origin_program`: a representation "
        "that jointly models exact copy-origin mark identity and literal innovation "
        "payload as content-origin choices. More local endpoint/source selectors "
        "should not be the main path unless they introduce a new source of exact "
        "identity and clear holdout/controls.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_v5_external_dependency_frontier_synthesis.py](../scripts/01_v5_external_dependency_frontier_synthesis.py)",
        "- [01_v5_external_dependency_frontier_synthesis.json](test_results/01_v5_external_dependency_frontier_synthesis.json)",
        "- [01_v5_external_dependency_frontier_synthesis.md](test_results/01_v5_external_dependency_frontier_synthesis.md)",
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
