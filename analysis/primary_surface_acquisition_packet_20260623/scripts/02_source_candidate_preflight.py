#!/usr/bin/env python3
"""Preflight candidate source classes before the v9 topology protocol.

This is not a web scraper and does not integrate any external source. It records
the admissibility gate for candidate surfaces so the next useful work can focus
on obtaining a rights-clean object layer instead of re-litigating public text
mirrors, community mappings, or leaked proprietary material.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "primary_surface_acquisition_packet_20260623"
OUT_DIR = FRONT / "reports" / "test_results"
JSON_OUT = OUT_DIR / "02_source_candidate_preflight.json"
MD_OUT = OUT_DIR / "02_source_candidate_preflight.md"
FINAL_OUT = FRONT / "reports" / "final_primary_surface_acquisition_packet.md"

REQUIRED_PASS_FIELDS = [
    "rights_clean",
    "primary_or_authorized",
    "object_layer_present",
    "matches_469_books",
    "has_container_or_bookcase_id",
    "has_slot_or_read_order",
    "has_version_or_date",
]

CANDIDATES: list[dict[str, Any]] = [
    {
        "candidate_id": "leaked_cipsoft_source_or_map_route",
        "source_class": "leaked_proprietary_source_or_map",
        "url_or_handle": "not_recorded_by_design",
        "rights_clean": False,
        "primary_or_authorized": False,
        "object_layer_present": True,
        "matches_469_books": "unknown_not_checked",
        "has_container_or_bookcase_id": "unknown_not_checked",
        "has_slot_or_read_order": "unknown_not_checked",
        "has_version_or_date": "unknown_not_checked",
        "prior_evidence": "community acceptance or alt-server reuse is not permission for this repository",
        "blocks": ["proprietary_leak", "not_rights_clean", "do_not_obtain_or_parse"],
    },
    {
        "candidate_id": "alt_server_or_otbm_derived_from_leak",
        "source_class": "unknown_or_leak_derived_object_layer",
        "url_or_handle": "otland_or_alt_server_map_threads",
        "rights_clean": False,
        "primary_or_authorized": False,
        "object_layer_present": "possible",
        "matches_469_books": "unknown_not_checked",
        "has_container_or_bookcase_id": "possible",
        "has_slot_or_read_order": "possible",
        "has_version_or_date": "weak_or_missing",
        "prior_evidence": "object layer may exist, but provenance is not clean enough for promotion",
        "blocks": ["unknown_rights", "likely_leak_lineage", "not_primary_authorized"],
    },
    {
        "candidate_id": "tibiawiki_hellgate_library_text",
        "source_class": "public_text_mirror_or_fan_solution",
        "url_or_handle": "https://tibia.fandom.com/wiki/Hellgate_Library",
        "rights_clean": "public_page",
        "primary_or_authorized": False,
        "object_layer_present": False,
        "matches_469_books": True,
        "has_container_or_bookcase_id": False,
        "has_slot_or_read_order": False,
        "has_version_or_date": "page_history_only",
        "prior_evidence": "book text corpus, not authoring/object topology",
        "blocks": ["no_object_layer", "no_slot_or_read_order", "not_primary_authoring_surface"],
    },
    {
        "candidate_id": "tibiawiki_hellgate_library_map_image",
        "source_class": "public_macro_map_or_marker_surface",
        "url_or_handle": "https://tibia.fandom.com/wiki/Hellgate_Library/map",
        "rights_clean": "public_page",
        "primary_or_authorized": False,
        "object_layer_present": False,
        "matches_469_books": False,
        "has_container_or_bookcase_id": False,
        "has_slot_or_read_order": False,
        "has_version_or_date": "page_history_only",
        "prior_evidence": "macro location/map clue only; no 70-book object layer",
        "blocks": ["no_book_text_match_rows", "no_object_layer", "no_slot_or_read_order"],
    },
    {
        "candidate_id": "s2ward_469_repository",
        "source_class": "public_community_text_and_theory_repository",
        "url_or_handle": "https://github.com/s2ward/469",
        "rights_clean": "public_repository",
        "primary_or_authorized": False,
        "object_layer_present": False,
        "matches_469_books": True,
        "has_container_or_bookcase_id": False,
        "has_slot_or_read_order": False,
        "has_version_or_date": "repository_history_only",
        "prior_evidence": "community corpus/theory surface, not object/container/slot provenance",
        "blocks": ["no_object_layer", "no_slot_or_read_order", "not_primary_authoring_surface"],
    },
    {
        "candidate_id": "arturo_bookcase_mapping_repository",
        "source_class": "licensed_community_bookcase_mapping",
        "url_or_handle": "https://github.com/arturoornelasb/tibia-bonelord-469-cipher",
        "rights_clean": True,
        "primary_or_authorized": False,
        "object_layer_present": False,
        "matches_469_books": True,
        "has_container_or_bookcase_id": "community_bookcase_ordinal",
        "has_slot_or_read_order": False,
        "has_version_or_date": "repository_history_only",
        "prior_evidence": "already tested: 63 unique matches and no positive heldout v9 saving",
        "blocks": ["posthoc_community_mapping", "no_fine_slot_layer", "v9_control_probe_rejected"],
    },
    {
        "candidate_id": "official_or_in_game_user_capture",
        "source_class": "official_cipsoft_public_or_in_game_capture",
        "url_or_handle": "not_acquired",
        "rights_clean": True,
        "primary_or_authorized": True,
        "object_layer_present": "required",
        "matches_469_books": "required",
        "has_container_or_bookcase_id": "required",
        "has_slot_or_read_order": "required",
        "has_version_or_date": "required",
        "prior_evidence": "admissible route if a capture supplies the clean topology worksheet fields",
        "blocks": ["not_yet_supplied"],
    },
    {
        "candidate_id": "user_authorized_metadata_csv_json",
        "source_class": "user_provided_authorized_metadata_csv_json",
        "url_or_handle": "not_acquired",
        "rights_clean": True,
        "primary_or_authorized": True,
        "object_layer_present": "required",
        "matches_469_books": "required",
        "has_container_or_bookcase_id": "required",
        "has_slot_or_read_order": "required",
        "has_version_or_date": "required",
        "prior_evidence": "admissible route if user provides rights-clean metadata for the 70 books",
        "blocks": ["not_yet_supplied"],
    },
    {
        "candidate_id": "public_licensed_object_layer_export",
        "source_class": "public_licensed_object_layer_data",
        "url_or_handle": "not_found",
        "rights_clean": "required",
        "primary_or_authorized": "required",
        "object_layer_present": "required",
        "matches_469_books": "required",
        "has_container_or_bookcase_id": "required",
        "has_slot_or_read_order": "required",
        "has_version_or_date": "required",
        "prior_evidence": "admissible route if license and object-level coverage are present",
        "blocks": ["not_yet_found"],
    },
]


def is_true(value: Any) -> bool:
    return value is True


def classify(candidate: dict[str, Any]) -> str:
    if "proprietary_leak" in candidate["blocks"] or candidate["source_class"] == "leaked_proprietary_source_or_map":
        return "REJECTED_SOURCE_ROUTE"
    if "likely_leak_lineage" in candidate["blocks"] or "unknown_rights" in candidate["blocks"]:
        return "REJECTED_PROVENANCE_CONTROL"
    if "not_yet_supplied" in candidate["blocks"] or "not_yet_found" in candidate["blocks"]:
        return "BLOCKED_NEEDS_PRIMARY_SOURCE"
    if "v9_control_probe_rejected" in candidate["blocks"]:
        return "REJECTED_PROVENANCE_CONTROL"
    if not candidate.get("object_layer_present"):
        return "REJECTED_FOR_TOPOLOGY_CONTROL"
    if not candidate.get("has_slot_or_read_order"):
        return "REJECTED_FOR_TOPOLOGY_CONTROL"
    if all(is_true(candidate.get(field)) for field in REQUIRED_PASS_FIELDS):
        return "PROMOTABLE_TO_V9_PROTOCOL_IF_HOLDOUT_CONTROLS_PASS"
    return "WEAK_PROVENANCE_CLUE"


def result() -> dict[str, Any]:
    rows = []
    for candidate in CANDIDATES:
        row = dict(candidate)
        row["classification"] = classify(candidate)
        row["can_enter_v9_protocol_now"] = row["classification"] == "PROMOTABLE_TO_V9_PROTOCOL_IF_HOLDOUT_CONTROLS_PASS"
        rows.append(row)

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1

    return {
        "schema": "source_candidate_preflight.v1",
        "scope": "analysis_only_primary_surface_source_preflight",
        "classification": "source_candidate_preflight_no_current_candidate_promoted",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "required_pass_fields": REQUIRED_PASS_FIELDS,
        "summary": {
            "candidate_count": len(rows),
            "can_enter_v9_protocol_now": sum(1 for row in rows if row["can_enter_v9_protocol_now"]),
            "classification_counts": counts,
            "external_surface_integrated": False,
            "v9_reduction_bits": 0.0,
        },
        "candidates": rows,
        "decision": {
            "external_surface_integrated": False,
            "v9_reduction_bits": 0.0,
            "next_step": "obtain a clean object-layer source or user-authorized metadata that passes all required fields before running the v9 protocol",
        },
    }


def write_markdown(data: dict[str, Any]) -> None:
    lines = [
        "# Source Candidate Preflight",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This preflight classifies candidate source surfaces before the clean topology v9 protocol.",
        "It does not acquire, download, parse, quote, or integrate leaked proprietary material.",
        f"Current candidates promotable into the v9 protocol now: `{data['summary']['can_enter_v9_protocol_now']}`.",
        "Net v9 reduction: `0.0` bits.",
        "",
        "## Required Pass Fields",
        "",
    ]
    for field in data["required_pass_fields"]:
        lines.append(f"- `{field}`")
    lines.extend(
        [
            "",
            "## Candidate Decisions",
            "",
            "| Candidate | Classification | Can enter v9 now | Blocks |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in data["candidates"]:
        blocks = ", ".join(row["blocks"])
        lines.append(
            f"| `{row['candidate_id']}` | `{row['classification']}` | `{row['can_enter_v9_protocol_now']}` | {blocks} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "`source_candidate_preflight_no_current_candidate_promoted`.",
            "",
            "A source can move forward only if it is rights-clean or user-authorized, exposes object/container/slot/order or versioned authoring fields, matches the 469 books, and then reduces v9 residual fields under holdout/permutation controls.",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def append_final() -> None:
    report = FINAL_OUT.read_text()
    marker = "## Source Candidate Preflight"
    if marker in report:
        return
    addition = [
        "",
        marker,
        "",
        "A candidate-source preflight now separates rejected leak/unknown-rights routes, weak public text or macro-topology clues, and admissible but not-yet-supplied clean object-layer routes before the v9 protocol is run.",
        "The current preflight has `0` candidates that can enter the v9 protocol now and integrates `0.0` bits.",
        "",
        "- [02_source_candidate_preflight.py](../scripts/02_source_candidate_preflight.py)",
        "- [02_source_candidate_preflight.json](test_results/02_source_candidate_preflight.json)",
        "- [02_source_candidate_preflight.md](test_results/02_source_candidate_preflight.md)",
    ]
    FINAL_OUT.write_text(report.rstrip() + "\n" + "\n".join(addition) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = result()
    JSON_OUT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    write_markdown(data)
    append_final()
    print(json.dumps(data["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
