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
    "nonlocal_event_policy": ROOT
    / "analysis/nonlocal_event_policy_program_audit_20260622/reports/test_results/01_nonlocal_event_policy_program_gate.json",
    "causal_content_aware_event_policy": ROOT
    / "analysis/causal_content_aware_event_policy_audit_20260622/reports/test_results/01_causal_content_aware_event_policy_gate.json",
    "global_content_objective": ROOT
    / "analysis/global_content_objective_event_program_audit_20260622/reports/test_results/01_global_content_objective_event_program_gate.json",
    "primary_surface_search": ROOT
    / "analysis/primary_authoring_surface_search_audit_20260622/reports/test_results/01_primary_authoring_surface_search_gate.json",
    "innovation_demand_coupling": ROOT
    / "analysis/innovation_demand_coupling_audit_20260622/reports/test_results/01_innovation_demand_coupling_gate.json",
    "numeric_innovation_source": ROOT
    / "analysis/numeric_innovation_source_audit_20260622/reports/test_results/01_numeric_innovation_source_gate.json",
    "external_numeric_anchor_source": ROOT
    / "analysis/external_numeric_anchor_source_audit_20260622/reports/test_results/01_external_numeric_anchor_source_gate.json",
    "chayenne_external_holdout": ROOT
    / "analysis/chayenne_external_holdout_innovation_replay_audit_20260622/reports/test_results/01_chayenne_external_holdout_innovation_replay_gate.json",
    "chayenne_holdout_boundary_alignment": ROOT
    / "analysis/chayenne_holdout_boundary_alignment_audit_20260622/reports/test_results/01_chayenne_holdout_boundary_alignment_gate.json",
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
    nonlocal_event = data["nonlocal_event_policy"]
    content_event = data["causal_content_aware_event_policy"]
    global_objective = data["global_content_objective"]
    primary_search = data["primary_surface_search"]
    demand_coupling = data["innovation_demand_coupling"]
    numeric_source = data["numeric_innovation_source"]
    external_anchor_source = data["external_numeric_anchor_source"]
    chayenne_holdout = data["chayenne_external_holdout"]
    chayenne_alignment = data["chayenne_holdout_boundary_alignment"]

    require(v9["classification"] == "PROMOTED_EXECUTABLE_V9_INNOVATION_COPY_CONTINUATION_LEDGER", "v9 not promoted")
    require(v9["summary"]["v9_external_bits_total_content_included"] < v9["summary"]["v8_external_bits_total_content_included"], "v9 not an improvement")
    require(post_v9["summary"]["new_program_promoted"] is False, "post-v9 unexpectedly promoted a program")
    require(innovation["summary"]["promoted"] is False, "innovation replay policy unexpectedly promoted")
    require(tales["decision"]["v9_reduction_bits"] == 0.0, "Tales probe unexpectedly reduces v9")
    require(arturo["decision"]["v9_reduction_bits"] == 0.0, "Arturo probe unexpectedly reduces v9")
    require(control_protocol["decision"]["v9_reduction_bits"] == 0.0, "clean topology protocol unexpectedly reduces v9")
    require("reject" in leaked_boundary["classification"].lower() or leaked_boundary["decision"]["external_surface_integrated"] is False, "leak boundary unexpectedly integrated")
    require(nonlocal_event["decision"]["nonlocal_event_policy_promoted"] is False, "nonlocal event policy unexpectedly promoted")
    require(content_event["decision"]["causal_content_aware_policy_promoted"] is False, "content-aware event policy unexpectedly promoted")
    require(global_objective["decision"]["global_content_objective_promoted"] is False, "global content objective unexpectedly promoted")
    require(primary_search["classification"] == "primary_authoring_surface_not_found_targeted_search", "targeted primary surface search unexpected classification")
    require(primary_search["summary"]["promoted_primary_surfaces"] == 0, "targeted primary surface search unexpectedly promoted a source")
    require(primary_search["decision"]["external_surface_integrated"] is False, "targeted primary surface unexpectedly integrated")
    require(primary_search["decision"]["leak_route_accepted"] is False, "leak route unexpectedly accepted")
    require(demand_coupling["decision"]["innovation_demand_coupling_promoted"] is False, "innovation demand coupling unexpectedly promoted")
    require(demand_coupling["decision"]["external_field_reduced"] is False, "innovation demand coupling unexpectedly reduced a field")
    require(numeric_source["decision"]["numeric_innovation_source_promoted"] is False, "numeric innovation source unexpectedly promoted")
    require(numeric_source["decision"]["external_field_reduced"] is False, "numeric innovation source unexpectedly reduced a field")
    require(external_anchor_source["decision"]["external_numeric_anchor_source_promoted"] is False, "external numeric anchor source unexpectedly promoted")
    require(external_anchor_source["decision"]["external_field_reduced"] is False, "external numeric anchor source unexpectedly reduced a field")
    require(chayenne_holdout["classification"] == "PROMOTED_CHAYENNE_EXTERNAL_HOLDOUT_VALIDATION", "Chayenne holdout validation not promoted")
    require(chayenne_holdout["decision"]["origin_source_promoted"] is False, "Chayenne unexpectedly promoted as origin")
    require(chayenne_holdout["decision"]["external_field_reduced"] is False, "Chayenne holdout unexpectedly reduced a field")
    require(chayenne_alignment["decision"]["subspan_module_holdout_clue_promoted"] is True, "Chayenne subspan holdout clue not promoted")
    require(chayenne_alignment["decision"]["event_boundary_policy_promoted"] is False, "Chayenne unexpectedly promoted event boundary policy")
    require(chayenne_alignment["decision"]["external_field_reduced"] is False, "Chayenne alignment unexpectedly reduced a field")

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
        {
            "source": "targeted_primary_authoring_surface_search",
            "classification": primary_search["classification"],
            "coverage": f"{primary_search['summary']['candidate_count']} public candidates, {primary_search['summary']['official_candidates_checked']} official-domain candidates",
            "blocking_issue": primary_search["decision"]["classification_reason"],
            "v9_reduction_bits": primary_search["summary"]["v9_reduction_bits"],
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
            "route": "targeted_primary_surface_search",
            "status": "TESTED_NO_SOURCE_FOUND",
            "evidence": {
                "candidate_count": primary_search["summary"]["candidate_count"],
                "official_candidates_checked": primary_search["summary"]["official_candidates_checked"],
                "community_candidates_checked": primary_search["summary"]["community_candidates_checked"],
                "promoted_primary_surfaces": primary_search["summary"]["promoted_primary_surfaces"],
                "leak_route_accepted": primary_search["decision"]["leak_route_accepted"],
                "next_acceptable_input": primary_search["decision"]["next_acceptable_input"],
            },
            "counts_as_next_progress": False,
            "reason": "targeted public search found no admissible primary object-layer/control surface; leaked proprietary material remains rejected",
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
            "route": "simple_nonlocal_event_sequence_program",
            "status": "TESTED_NOT_PROMOTED",
            "evidence": {
                "main_stream": nonlocal_event["decision"]["main_stream"],
                "main_total_saving_bits": nonlocal_event["streams"]["type_length_sourcebucket"]["summary"]["total_saving_bits"],
                "main_positive_splits": nonlocal_event["streams"]["type_length_sourcebucket"]["summary"]["positive_splits"],
                "main_exact_suffix_beam_hits": nonlocal_event["streams"]["type_length_sourcebucket"]["summary"]["exact_suffix_beam_hits"],
            },
            "counts_as_next_progress": False,
            "reason": "n-gram/phase sequence models over replay events do not reduce the joint event policy stream or keep true suffixes in beam",
        },
        {
            "route": "causal_content_aware_event_policy_program",
            "status": "WEAK_RANK_CLUE_NOT_EXECUTABLE_PROGRAM",
            "evidence": {
                "total_rank_saving_bits": content_event["summary"]["total_saving_bits"],
                "positive_splits": content_event["summary"]["positive_splits"],
                "beam_exact_splits": content_event["summary"]["beam_exact_splits"],
                "top20_total": content_event["summary"]["top20_total"],
            },
            "counts_as_next_progress": False,
            "reason": "content-aware candidate ranking reduces loose raw-choice cost but does not keep true event suffixes in beam",
        },
        {
            "route": "simple_global_content_objective_event_program",
            "status": "TESTED_NOT_PROMOTED",
            "evidence": {
                "exact_beam_splits": global_objective["summary"]["exact_beam_splits"],
                "max_true_action_survives": global_objective["summary"]["max_true_action_survives"],
                "best_exact_prefix_digits": global_objective["summary"]["best_exact_prefix_digits"],
                "target_digits": global_objective["summary"]["target_digits"],
            },
            "counts_as_next_progress": False,
            "reason": "target-free cost minimization over literal/copy events does not keep the true suffix in beam",
        },
        {
            "route": "innovation_demand_coupling_state",
            "status": "WEAK_CLUE_NOT_EXECUTABLE_PROGRAM",
            "evidence": {
                "classification": demand_coupling["classification"],
                "event_boundary_demand_hits": demand_coupling["summary"]["event_boundary_demand_hits"],
                "internal_event_boundaries": demand_coupling["summary"]["internal_event_boundaries"],
                "events_within_single_consumer_segment": demand_coupling["summary"]["events_within_single_consumer_segment"],
                "innovation_events": demand_coupling["summary"]["innovation_events"],
                "demand_boundary_saving_bits": demand_coupling["summary"]["demand_boundary_saving_bits"],
                "weak_within_segment_clue": demand_coupling["summary"]["weak_within_segment_clue"],
            },
            "counts_as_next_progress": False,
            "reason": "downstream demand segments weakly contain replay events but do not derive replay boundaries or reduce v9 fields",
        },
        {
            "route": "simple_numeric_innovation_source",
            "status": "TESTED_NOT_PROMOTED",
            "evidence": {
                "classification": numeric_source["classification"],
                "source_count": numeric_source["source_bank"]["source_count"],
                "source_digits_each": numeric_source["source_bank"]["source_digits_each"],
                "copied_digits": numeric_source["summary"]["copied_digits"],
                "innovation_digits": numeric_source["summary"]["innovation_digits"],
                "delta_vs_raw_bits": numeric_source["summary"]["delta_vs_raw_bits"],
                "positive_holdouts": numeric_source["summary"]["positive_holdouts"],
                "holdout_count": numeric_source["summary"]["holdout_count"],
                "beats_random_source_p05": numeric_source["summary"]["beats_random_source_p05"],
                "beats_shuffled_target_p05": numeric_source["summary"]["beats_shuffled_target_p05"],
            },
            "counts_as_next_progress": False,
            "reason": "mathematical constants/simple sequences/fixed PRNG controls do not provide the innovation content source after paid costs and controls",
        },
        {
            "route": "known_external_numeric_anchor_content_source",
            "status": "WEAK_CHAYENNE_CLUE_NOT_ORIGIN_SOURCE",
            "evidence": {
                "classification": external_anchor_source["classification"],
                "promotable_sources_copied_digits": external_anchor_source["summary"]["promotable_sources_copied_digits"],
                "promotable_sources_delta_vs_raw_bits": external_anchor_source["summary"]["promotable_sources_delta_vs_raw_bits"],
                "chayenne_copied_digits": external_anchor_source["summary"]["chayenne_copied_digits"],
                "chayenne_delta_vs_raw_bits": external_anchor_source["summary"]["chayenne_delta_vs_raw_bits"],
                "positive_holdouts": external_anchor_source["summary"]["positive_holdouts"],
                "holdout_count": external_anchor_source["summary"]["holdout_count"],
            },
            "counts_as_next_progress": False,
            "reason": "Chayenne overlaps the innovation tape as secondary corpus-compatible validation, while promotable external anchors copy zero digits",
        },
        {
            "route": "chayenne_external_holdout_module_bank_validation",
            "status": "PROMOTED_EXTERNAL_HOLDOUT_VALIDATION_NOT_ORIGIN",
            "evidence": {
                "classification": chayenne_holdout["classification"],
                "chayenne_copied_digits": chayenne_holdout["summary"]["chayenne_copied_digits"],
                "chayenne_digits": chayenne_holdout["summary"]["chayenne_digits"],
                "chayenne_delta_vs_raw_bits": chayenne_holdout["summary"]["chayenne_delta_vs_raw_bits"],
                "beats_shuffled_target_p05": chayenne_holdout["summary"]["chayenne_beats_shuffled_target_p05"],
                "beats_random_source_p05": chayenne_holdout["summary"]["chayenne_beats_random_source_p05"],
                "your_true_colour_copied_digits": chayenne_holdout["summary"]["your_true_colour_copied_digits"],
                "avar_tar_copied_digits": chayenne_holdout["summary"]["avar_tar_copied_digits"],
            },
            "counts_as_next_progress": False,
            "reason": "validates the innovation tape as a module bank on one external holdout, but does not generate event policy or content origin",
        },
        {
            "route": "chayenne_holdout_boundary_alignment",
            "status": "PROMOTED_SUBSPAN_MODULE_CLUE_NOT_EVENT_POLICY",
            "evidence": {
                "classification": chayenne_alignment["classification"],
                "chayenne_copy_spans": chayenne_alignment["summary"]["chayenne_copy_spans"],
                "replay_boundary_aligned_spans": chayenne_alignment["summary"]["replay_boundary_aligned_spans"],
                "consumer_boundary_aligned_spans": chayenne_alignment["summary"]["consumer_boundary_aligned_spans"],
                "contained_in_single_replay_event": chayenne_alignment["summary"]["contained_in_single_replay_event"],
                "contained_in_single_consumer_segment": chayenne_alignment["summary"]["contained_in_single_consumer_segment"],
            },
            "counts_as_next_progress": False,
            "reason": "locates the Chayenne validation at internal subspan/module level rather than replay-event boundary policy",
        },
        {
            "route": "primary_authoring_surface_or_new_causal_state",
            "status": "OPEN_REQUIRES_NEW_INFORMATION",
            "evidence": {
                "blocker": post_v9["decision"]["next_blocker"],
                "rejected_simple_routes": [
                    "simple_nonlocal_event_sequence_program",
                    "causal_content_aware_event_policy_program",
                    "simple_global_content_objective_event_program",
                    "innovation_demand_coupling_state",
                    "simple_numeric_innovation_source",
                    "known_external_numeric_anchor_content_source",
                ],
                "validated_but_not_solved": [
                    "chayenne_external_holdout_module_bank_validation",
                    "chayenne_holdout_boundary_alignment",
                ],
                "must_use_new_information": [
                    "external authoring surface not already covered by targeted public/community search",
                    "new causal state beyond emitted-content/literal-tape/copy-lineage/downstream-demand segments",
                    "event beam survival rather than rank-only trace",
                    "paid corrections with prefix/family holdout",
                ],
            },
            "counts_as_next_progress": True,
            "promotion_test": "must keep/generate replay event suffixes in prefix/family holdout using new causal state, or integrate a primary source that reduces declared external fields after paying program/corrections",
        },
    ]
    return {
        "route_ledger": route_ledger,
        "next_work_contract": {
            "do_next": [
                "acquire/test a genuinely new rights-clean primary object/slot/order or versioned authoring source using the existing CSV/control protocol",
                "introduce new causal state beyond emitted content/literal tape/copy lineage, or integrate a primary authoring source",
            ],
            "do_not_count_as_progress": [
                "another public text mirror or community topology list without new fields",
                "another broad public search over the same official-generic/community surfaces without new terms or evidence",
                "leaked proprietary source/map data",
                "local source/length/copy-hint/literal subcodec with small bit gain",
                "simple n-gram/phase event grammar over replay events",
                "rank-only content-aware event traces that do not survive beam decoding",
                "target-free literal/copy cost minimization that loses the true suffix immediately",
                "demand-segment containment clues that do not derive replay boundaries or reduce decoder fields",
                "small banks of constants/simple numeric sequences/PRNG controls that do not reduce the innovation tape after paid costs",
                "known short external numeric anchors where only Chayenne overlaps, because Chayenne is secondary validation rather than origin",
                "Chayenne module-bank validation reported as an origin source, plaintext, or v9 reduction",
                "Chayenne subspan validation reported as replay-event policy derivation",
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
        "It does not promote a new formula. It narrows the live work to one real route class: new information, either from a primary authoring surface or from a causal state not yet represented.",
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
        "Public/community external surfaces have now been tested at the useful levels available: text mirrors, map/marker surfaces, Tales/LIBSearch, licensed community bookcase mapping, and a targeted official/community primary-surface search.",
        "None reduces v9 residual fields under the required controls.",
        "The targeted search also records the source boundary: leaked proprietary Tibia source/map material is not an admissible evidence route even if reused by alt-server communities.",
        "",
        "The route frontier is therefore narrowed rather than solved: either obtain a genuinely primary/rights-clean authoring surface outside the already-tested public/community set, or introduce a causal state not already captured by emitted content, literal tape, and copy lineage.",
        "Simple n-gram/phase sequence grammars, rank-only content-aware event traces, target-free literal/copy cost minimization, downstream-demand segment coupling, simple numeric-source content banks, and known short external numeric anchors are now tested and not promoted as executable programs.",
        "Chayenne is the important positive exception: it is promoted as external holdout validation of the innovation module bank, but explicitly not as an origin source, v9 reduction, or translation.",
        "",
        "## Decision",
        "",
        "`post_external_generator_route_frontier_narrowed_no_formula_promoted`.",
        "",
        "No new formula is promoted. No external source is integrated. The next useful work requires new admissible information or a genuinely new causal state, not more residual-field subcodecs.",
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
