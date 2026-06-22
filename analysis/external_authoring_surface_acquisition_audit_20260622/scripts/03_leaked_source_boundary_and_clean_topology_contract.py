#!/usr/bin/env python3
"""Document the source-boundary for topology acquisition.

The project needs object/container/slot metadata, but leaked proprietary source
or map data is not an acceptable acquisition route. This gate records the clean
contract for any future topology source so a usable dataset can be tested
without contaminating the evidence chain.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/test_results"
FINAL_REPORT = ROOT / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/final_external_authoring_surface_acquisition_audit.md"


REQUIRED_FIELDS = [
    {
        "field": "source_id",
        "required": True,
        "description": "Stable identifier for the provided dataset or capture.",
    },
    {
        "field": "source_rights",
        "required": True,
        "description": "License/permission statement or proof that the data is user-owned/authorized/publicly licensed.",
    },
    {
        "field": "source_version_or_date",
        "required": True,
        "description": "Client/game/map version or capture date.",
    },
    {
        "field": "book_text_or_exact_prefix",
        "required": True,
        "description": "Exact numeric text or prefix sufficient to match a canonical 469 book.",
    },
    {
        "field": "x",
        "required": True,
        "description": "World X coordinate or equivalent local coordinate.",
    },
    {
        "field": "y",
        "required": True,
        "description": "World Y coordinate or equivalent local coordinate.",
    },
    {
        "field": "z",
        "required": True,
        "description": "Floor/depth coordinate.",
    },
    {
        "field": "container_or_bookcase_id",
        "required": True,
        "description": "Bookcase/container object identity, not just a public ordinal.",
    },
    {
        "field": "slot_or_read_order",
        "required": True,
        "description": "Slot inside the container, item stack position, or observed read order.",
    },
    {
        "field": "orientation_or_side",
        "required": False,
        "description": "Shelf side/orientation when available.",
    },
    {
        "field": "capture_method",
        "required": True,
        "description": "Official/in-game capture, user-generated observation, licensed map export, or other allowed route.",
    },
]


SOURCE_POLICIES = [
    {
        "source_class": "leaked_proprietary_source_or_map",
        "status": "REJECTED_SOURCE_ROUTE",
        "can_use": False,
        "reason": "unauthorized proprietary leak would contaminate provenance and cannot be used as project evidence",
        "allowed_action": "do not obtain, download, parse, quote, or integrate",
    },
    {
        "source_class": "official_cipsoft_public_or_in_game_capture",
        "status": "PROMOTABLE_IF_FIELDS_AND_CONTROLS_PASS",
        "can_use": True,
        "reason": "primary or directly observed in-game evidence can establish topology provenance",
        "allowed_action": "parse into the clean topology contract and test against v9 fields with controls",
    },
    {
        "source_class": "user_provided_authorized_metadata_csv_json",
        "status": "PROMOTABLE_IF_RIGHTS_FIELDS_AND_CONTROLS_PASS",
        "can_use": True,
        "reason": "metadata can be tested if the provider has rights/permission and includes required fields",
        "allowed_action": "validate schema, match canonical books, then run holdout/permutation controls",
    },
    {
        "source_class": "public_licensed_community_map_or_marker_data",
        "status": "AUDIT_ONLY_UNLESS_OBJECT_LAYER_PRESENT",
        "can_use": True,
        "reason": "map/marker data is useful only if it exposes book objects/slots, not just floor imagery",
        "allowed_action": "record provenance and test only fields present in the clean contract",
    },
    {
        "source_class": "public_text_mirror_or_fan_solution",
        "status": "REJECTED_FOR_TOPOLOGY_CONTROL",
        "can_use": True,
        "reason": "text mirrors can verify corpus strings but not object topology or authoring control",
        "allowed_action": "use as corpus provenance only; do not promote as generator evidence",
    },
]


TEST_PROTOCOL = [
    "validate rights/provenance and required fields",
    "match each row to canonical 469 book by exact text/prefix",
    "separate unique, ambiguous, and unmatched book rows",
    "derive coordinate/order variables without looking at v9 residual targets",
    "test prediction of v9 fields: book_order_topology, event_schedule/coarse_control, copy_literal_decision_policy",
    "compare against shuffled coordinates, permuted book order, same-bookcase controls, and public-bookcase baseline",
    "promote only if the clean source reduces declared external fields after model/correction costs",
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "schema": "leaked_source_boundary_and_clean_topology_contract.v1",
        "scope": "analysis_only_source_boundary_for_topology_acquisition",
        "classification": "leaked_source_route_rejected_clean_topology_contract_ready",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "decision": {
            "can_get_or_use_leaked_tibia_source": False,
            "reason": "unauthorized proprietary leak is not an acceptable evidence source",
            "clean_route_available": True,
            "v9_reduction_bits": 0.0,
            "next_acceptable_input": "authorized object/container/slot/order metadata as CSV/JSON, official/in-game capture, or public licensed object-layer data",
        },
        "required_fields": REQUIRED_FIELDS,
        "source_policies": SOURCE_POLICIES,
        "test_protocol": TEST_PROTOCOL,
        "example_clean_row": {
            "source_id": "example_authorized_capture_YYYYMMDD",
            "source_rights": "user_owned_or_public_license_reference",
            "source_version_or_date": "Tibia version/date",
            "book_text_or_exact_prefix": "9457655996704672611",
            "x": 0,
            "y": 0,
            "z": 0,
            "container_or_bookcase_id": "bookcase_object_or_container_id",
            "slot_or_read_order": 1,
            "orientation_or_side": "unknown_allowed_if_absent",
            "capture_method": "official/in_game/user_authorized/public_licensed",
        },
    }

    json_path = OUT_DIR / "03_leaked_source_boundary_and_clean_topology_contract.json"
    md_path = OUT_DIR / "03_leaked_source_boundary_and_clean_topology_contract.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines: list[str] = []
    lines.append("# Leaked Source Boundary and Clean Topology Contract")
    lines.append("")
    lines.append("Classification: `leaked_source_route_rejected_clean_topology_contract_ready`")
    lines.append("Translation delta: `NONE`")
    lines.append("Plaintext claim: `False`")
    lines.append("Case reopened: `False`")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append(
        "The project should not obtain, download, parse, quote, or integrate leaked proprietary Tibia source/map data."
    )
    lines.append("")
    lines.append("Community reuse in alt servers is not sufficient provenance or permission for this repository.")
    lines.append("")
    lines.append(
        "A clean route remains available: authorized object/container/slot/order metadata, official/in-game capture, or public licensed object-layer data."
    )
    lines.append("")
    lines.append("Net v9 reduction from this gate: `0.0` bits.")
    lines.append("")
    lines.append("## Required Clean Fields")
    lines.append("")
    lines.append("| Field | Required | Purpose |")
    lines.append("| --- | --- | --- |")
    for field in REQUIRED_FIELDS:
        lines.append(f"| `{field['field']}` | `{field['required']}` | {field['description']} |")
    lines.append("")
    lines.append("## Source Policy")
    lines.append("")
    lines.append("| Source Class | Status | Can Use | Allowed Action |")
    lines.append("| --- | --- | --- | --- |")
    for policy in SOURCE_POLICIES:
        lines.append(
            f"| `{policy['source_class']}` | `{policy['status']}` | `{policy['can_use']}` | {policy['allowed_action']} |"
        )
    lines.append("")
    lines.append("## Test Protocol")
    lines.append("")
    for index, step in enumerate(TEST_PROTOCOL, start=1):
        lines.append(f"{index}. {step}")
    lines.append("")
    lines.append("`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.")
    md_path.write_text("\n".join(lines) + "\n")

    report = FINAL_REPORT.read_text() if FINAL_REPORT.exists() else ""
    marker = "## Leaked Source Boundary"
    if marker not in report:
        addition = [
            "",
            marker,
            "",
            "A source-boundary gate answers whether the old Tibia source-code/map leak should be used for topology.",
            "It should not: leaked proprietary material is rejected as an evidence route.",
            "Community reuse in alt servers is not sufficient provenance or permission for this repository.",
            "The usable path is an authorized CSV/JSON object-layer contract with book text/prefix, coordinates, container/bookcase identity, slot/read order, version/date, and rights/provenance.",
            "No source is integrated into v9 and net v9 reduction remains `0.0` bits.",
            "",
            "- [03_leaked_source_boundary_and_clean_topology_contract.py](../scripts/03_leaked_source_boundary_and_clean_topology_contract.py)",
            "- [03_leaked_source_boundary_and_clean_topology_contract.json](test_results/03_leaked_source_boundary_and_clean_topology_contract.json)",
            "- [03_leaked_source_boundary_and_clean_topology_contract.md](test_results/03_leaked_source_boundary_and_clean_topology_contract.md)",
        ]
        FINAL_REPORT.write_text(report.rstrip() + "\n" + "\n".join(addition) + "\n")


if __name__ == "__main__":
    main()
