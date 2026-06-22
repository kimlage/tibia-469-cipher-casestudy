#!/usr/bin/env python3
"""Synthesize the current 469 generator route frontier.

This is a decision audit, not another residual codec. It reads the promoted v9
ledger, post-v9/internal policy gates, and the latest external-surface probes to
decide which routes can still plausibly move the project toward a real
mechanical generator.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/generator_route_decision_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
FINAL_REPORT = FRONT / "reports/final_generator_route_decision_audit.md"

INPUTS = {
    "v9": ROOT
    / "analysis/executable_v9_innovation_copy_continuation_audit_20260622/reports/test_results/01_executable_v9_innovation_copy_continuation_gate.json",
    "post_v9": ROOT
    / "analysis/post_v9_generator_frontier_synthesis_audit_20260622/reports/test_results/01_post_v9_generator_frontier_synthesis.json",
    "innovation_policy": ROOT
    / "analysis/innovation_replay_policy_frontier_audit_20260622/reports/test_results/01_innovation_replay_policy_frontier_gate.json",
    "external_01": ROOT
    / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/test_results/01_external_authoring_surface_acquisition_gate.json",
    "external_02": ROOT
    / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/test_results/02_github_exact_book_source_hunt.json",
    "external_03": ROOT
    / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/test_results/03_leaked_source_boundary_and_clean_topology_contract.json",
    "external_04": ROOT
    / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/test_results/04_clean_topology_contract_validator.json",
    "external_05": ROOT
    / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/test_results/05_clean_topology_v9_integration_harness.json",
    "external_06": ROOT
    / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/test_results/06_clean_topology_v9_control_protocol.json",
    "external_07": ROOT
    / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/test_results/07_tales_libsearch_book_database_probe.json",
    "external_08": ROOT
    / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/test_results/08_arturo_bookcase_mapping_control_probe.json",
}


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def build_route_ledger(data: dict[str, Any]) -> dict[str, Any]:
    v9 = data["v9"]
    post_v9 = data["post_v9"]
    innovation = data["innovation_policy"]
    tales = data["external_07"]
    arturo = data["external_08"]
    control_protocol = data["external_06"]
    leaked_boundary = data["external_03"]

    require(v9["classification"] == "PROMOTED_EXECUTABLE_V9_INNOVATION_COPY_CONTINUATION_LEDGER", "v9 not promoted")
    require(v9["summary"]["v9_external_bits_total_content_included"] < v9["summary"]["v8_external_bits_total_content_included"], "v9 not an improvement")
    require(post_v9["summary"]["new_program_promoted"] is False, "post-v9 unexpectedly promoted a program")
    require(innovation["summary"]["promoted"] is False, "innovation replay policy unexpectedly promoted")
    require(tales["decision"]["v9_reduction_bits"] == 0.0, "Tales probe unexpectedly reduces v9")
    require(arturo["decision"]["v9_reduction_bits"] == 0.0, "Arturo probe unexpectedly reduces v9")
    require(control_protocol["decision"]["v9_reduction_bits"] == 0.0, "clean topology protocol unexpectedly reduces v9")
    require("reject" in leaked_boundary["classification"].lower() or leaked_boundary["decision"]["external_surface_integrated"] is False, "leak boundary unexpectedly integrated")

    public_surface_rows = [
        {
            "source": "tibiamaps_historical_map_data",
            "classification": data["external_01"]["candidate_matrix"][0]["classification"],
            "coverage": "historical map PNG folders",
            "blocking_issue": data["external_01"]["candidate_matrix"][0]["blocking_issue"],
            "v9_reduction_bits": 0.0,
        },
        {
            "source": "github_exact_book_hits",
            "classification": data["external_02"]["classification"],
            "coverage": f"{data['external_02']['summary']['exact_text_hit_count']} exact hits across {data['external_02']['summary']['unique_repositories']} repos",
            "blocking_issue": data["external_02"]["decision"]["reason"],
            "v9_reduction_bits": data["external_02"]["decision"]["decoder_v9_reduction_bits"],
        },
        {
            "source": "tales_libsearch_book_database",
            "classification": tales["classification"],
            "coverage": f"{tales['contract_assessment']['unique_matched_books']} books, {tales['joined_v9_rows']} v9 rows",
            "blocking_issue": tales["decision"]["reason"],
            "v9_reduction_bits": tales["decision"]["v9_reduction_bits"],
        },
        {
            "source": "arturo_bookcase_mapping",
            "classification": arturo["classification"],
            "coverage": f"{arturo['match_summary']['unique_matched_books']} books, {arturo['joined_v9_rows']} v9 rows",
            "blocking_issue": arturo["decision"]["classification_reason"],
            "v9_reduction_bits": arturo["decision"]["v9_reduction_bits"],
        },
    ]

    route_ledger = [
        {
            "route": "current_executable_decoder",
            "status": "PROMOTED_BASELINE_NOT_FINAL_GENERATOR",
            "evidence": {
                "frontier": "v9 innovation copy-continuation ledger",
                "content_included_bits": v9["summary"]["v9_external_bits_total_content_included"],
                "delta_vs_v8_bits": v9["summary"]["delta_vs_v8_total_bits"],
                "next_blocker": v9["decision"]["next_blocker"],
            },
            "counts_as_next_progress": False,
            "reason": "baseline is executable and promoted, but event policy and non-continuation source/length remain external",
        },
        {
            "route": "more_internal_micro_codecs",
            "status": "REJECTED_AS_MAINLINE_PROGRESS",
            "evidence": {
                "copy_length_default_net_bits": post_v9["summary"]["copy_length_default_net_bits"],
                "copy_length_default_status": post_v9["summary"]["copy_length_default_status"],
            },
            "counts_as_next_progress": False,
            "reason": "small positive defaults are below promotion threshold/control-close and do not create a parser/generator",
        },
        {
            "route": "simple_online_innovation_replay_policy",
            "status": "TESTED_NOT_PROMOTED",
            "evidence": {
                "best_policy": innovation["summary"]["best_policy"],
                "best_exact_prefix": innovation["summary"]["best_exact_prefix"],
                "target_digits": innovation["summary"]["target_digits"],
                "delta_vs_v7_payload_replay_bits": innovation["summary"]["best_delta_vs_v7_payload_replay_bits"],
            },
            "counts_as_next_progress": False,
            "reason": "literal-only/online policies do not recover the event schedule or source-length choices",
        },
        {
            "route": "public_or_community_external_surfaces",
            "status": "SATURATED_UNDER_CURRENT_EVIDENCE",
            "evidence": public_surface_rows,
            "counts_as_next_progress": False,
            "reason": "tested surfaces either lack object/slot/versioned authoring data or fail v9 residual controls",
        },
        {
            "route": "rights_clean_primary_authoring_surface",
            "status": "OPEN_REQUIRES_NEW_SOURCE",
            "evidence": {
                "clean_contract_ready": data["external_04"]["decision"]["clean_contract_ready"],
                "control_protocol_ready": data["external_06"]["classification"],
                "minimum_total_books": data["external_06"]["protocol"]["minimum_coverage"]["total_matched_books"],
                "minimum_derived_books": data["external_06"]["protocol"]["minimum_coverage"]["derived_matched_books"],
            },
            "counts_as_next_progress": True,
            "promotion_test": "source must be rights-clean/primary or user-authorized, match books, expose object/container/slot/order or versioned authoring fields, and reduce v9 residual streams in holdout above permutations",
        },
        {
            "route": "nonlocal_event_policy_program",
            "status": "OPEN_INTERNAL_ROUTE",
            "evidence": {
                "blocker": post_v9["decision"]["next_blocker"],
                "must_not_retest": [
                    "copy-length defaults alone",
                    "literal payload Markov alone",
                    "bookcase/order metadata without new provenance",
                    "row0/plaintext/translation",
                ],
            },
            "counts_as_next_progress": True,
            "promotion_test": "must generate replay event schedule and copy/literal/source-length choices in prefix/family holdout, or reduce declared external fields after paying program/corrections",
        },
    ]
    return {
        "route_ledger": route_ledger,
        "next_work_contract": {
            "do_next": [
                "acquire/test a genuinely new rights-clean primary object/slot/order or versioned authoring source using the existing CSV/control protocol",
                "design a nonlocal event-policy program over v9 replay events, with train-prefix/family holdout and paid corrections",
            ],
            "do_not_count_as_progress": [
                "another public text mirror or community topology list without new fields",
                "leaked proprietary source/map data",
                "local source/length/copy-hint/literal subcodec with small bit gain",
                "semantic/plaintext/row0 reopening",
            ],
            "completion_not_achieved_reason": "no current route generates the 70 books source-free or removes the replay event policy; v9 remains a strong executable ledger, not a final authorial formula",
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# Generator Route Decision Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit consolidates the current generator frontier after v9 and the public external-surface probes.",
        "It does not promote a new formula. It narrows the live work to two routes: a rights-clean primary authoring surface, or a nonlocal event-policy program.",
        "",
        "## Route Ledger",
        "",
        "| Route | Status | Counts As Next Progress | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for route in result["route_ledger"]:
        lines.append(
            f"| `{route['route']}` | `{route['status']}` | `{route['counts_as_next_progress']}` | {route.get('reason') or route.get('promotion_test')} |"
        )
    lines.extend(
        [
            "",
            "## Next Work Contract",
            "",
            "Progress now means one of:",
            "",
        ]
    )
    for item in result["next_work_contract"]["do_next"]:
        lines.append(f"- {item}")
    lines.extend(["", "Do not count as progress:", ""])
    for item in result["next_work_contract"]["do_not_count_as_progress"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "`post_external_generator_route_frontier_narrowed_no_formula_promoted`",
            "",
            result["next_work_contract"]["completion_not_achieved_reason"],
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    (OUT_DIR / "01_generator_route_decision_ledger.md").write_text("\n".join(lines) + "\n")


def write_final_report(result: dict[str, Any]) -> None:
    lines = [
        "# Final Generator Route Decision Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "The current executable frontier remains v9, not a final authorial generator.",
        "Public/community external surfaces have now been tested at the useful levels available: text mirrors, map/marker surfaces, Tales/LIBSearch, and licensed community bookcase mapping.",
        "None reduces v9 residual fields under the required controls.",
        "",
        "The route frontier is therefore narrowed rather than solved: either obtain a genuinely primary/rights-clean authoring surface, or build a nonlocal event-policy program for the v9 innovation replay.",
        "",
        "## Decision",
        "",
        "`post_external_generator_route_frontier_narrowed_no_formula_promoted`.",
        "",
        "No new formula is promoted. No external source is integrated. The next useful internal work must attack event policy jointly, not residual fields one by one.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_generator_route_decision_ledger.py](../scripts/01_generator_route_decision_ledger.py)",
        "- [01_generator_route_decision_ledger.json](test_results/01_generator_route_decision_ledger.json)",
        "- [01_generator_route_decision_ledger.md](test_results/01_generator_route_decision_ledger.md)",
    ]
    FINAL_REPORT.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = {name: load_json(path) for name, path in INPUTS.items()}
    built = build_route_ledger(data)
    result = {
        "schema": "generator_route_decision_ledger.v1",
        "scope": "analysis_only_route_decision",
        "classification": "post_external_generator_route_frontier_narrowed_no_formula_promoted",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "inputs": {name: str(path.relative_to(ROOT)) for name, path in INPUTS.items()},
        **built,
    }
    (OUT_DIR / "01_generator_route_decision_ledger.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final_report(result)


if __name__ == "__main__":
    main()
