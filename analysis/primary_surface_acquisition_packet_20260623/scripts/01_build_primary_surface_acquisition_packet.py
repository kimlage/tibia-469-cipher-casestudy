#!/usr/bin/env python3
"""Build the fillable acquisition packet for the remaining primary-surface route.

The internal generator route is no longer the main front. This script prepares a
rights-clean object-layer collection worksheet for all 70 canonical books so a
future official/in-game/user-authorized/public-licensed capture can be tested by
the existing clean topology harness without guessing which data to collect.

No source is integrated here. Blank required fields are intentional.
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "primary_surface_acquisition_packet_20260623"
OUT_DIR = FRONT / "reports" / "test_results"
FINAL_OUT = FRONT / "reports" / "final_primary_surface_acquisition_packet.md"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

WORKSHEET = OUT_DIR / "01_primary_surface_acquisition_worksheet.csv"
JSON_OUT = OUT_DIR / "01_primary_surface_acquisition_packet.json"
MD_OUT = OUT_DIR / "01_primary_surface_acquisition_packet.md"

REQUIRED_FIELDS = [
    "source_id",
    "source_rights",
    "source_version_or_date",
    "book_text_or_exact_prefix",
    "x",
    "y",
    "z",
    "container_or_bookcase_id",
    "slot_or_read_order",
    "capture_method",
]
OPTIONAL_FIELDS = ["orientation_or_side", "notes"]
HELPER_FIELDS = ["canonical_book", "canonical_book_length", "canonical_prefix_20", "canonical_prefix_32"]
FORBIDDEN_SOURCE_CLASSES = [
    "leaked_proprietary_source_or_map",
    "unknown_rights_export",
    "fan_solution_without_object_layer",
]
ACCEPTABLE_SOURCE_CLASSES = [
    "official_cipsoft_public_or_in_game_capture",
    "user_provided_authorized_metadata_csv_json",
    "public_licensed_object_layer_data",
    "versioned_authoring_artifact_with_rights",
]


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def build_rows() -> list[dict[str, str]]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    rows: list[dict[str, str]] = []
    for book in range(70):
        digits = books[book]
        rows.append(
            {
                "source_id": "",
                "source_rights": "",
                "source_version_or_date": "",
                "book_text_or_exact_prefix": digits[:32],
                "x": "",
                "y": "",
                "z": "",
                "container_or_bookcase_id": "",
                "slot_or_read_order": "",
                "capture_method": "",
                "orientation_or_side": "",
                "notes": "",
                "canonical_book": str(book),
                "canonical_book_length": str(len(digits)),
                "canonical_prefix_20": digits[:20],
                "canonical_prefix_32": digits[:32],
            }
        )
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    fields = REQUIRED_FIELDS + OPTIONAL_FIELDS + HELPER_FIELDS
    with WORKSHEET.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# Primary Surface Acquisition Packet",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "This is the operational handoff for the only remaining main route: a clean primary or rights-cleared object-layer surface.",
        "The worksheet pre-fills all 70 canonical books with matching prefixes and leaves only provenance/topology fields for an authorized capture.",
        "",
        "## Required Real Fields",
        "",
    ]
    for field in REQUIRED_FIELDS:
        lines.append(f"- `{field}`")
    lines.extend(
        [
            "",
            "## Accepted Source Classes",
            "",
        ]
    )
    for item in ACCEPTABLE_SOURCE_CLASSES:
        lines.append(f"- `{item}`")
    lines.extend(["", "Rejected source classes:", ""])
    for item in FORBIDDEN_SOURCE_CLASSES:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Validation Command",
            "",
            "After filling the worksheet with real authorized object-layer data, run:",
            "",
            "```bash",
            "python3 analysis/external_authoring_surface_acquisition_audit_20260622/scripts/06_clean_topology_v9_control_protocol.py --input analysis/primary_surface_acquisition_packet_20260623/reports/test_results/01_primary_surface_acquisition_worksheet.csv",
            "```",
            "",
            "The current worksheet intentionally has blank required fields, so it is not a valid source yet and integrates `0.0` v9 bits.",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    lines = [
        "# Final Primary Surface Acquisition Packet",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "The internal route is saturated as the main front. This packet makes the remaining external route executable by providing a fillable worksheet for all 70 canonical books.",
        f"The worksheet has `{result['summary']['worksheet_rows']}` rows and pre-fills canonical prefixes, but it intentionally contains blank provenance/topology fields.",
        "",
        "No source is integrated. This is an acquisition interface for future official/in-game/user-authorized/public-licensed object-layer data.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "Progress now requires filling this worksheet or an equivalent CSV with clean source rights, version/date, coordinates, container identity, and slot/read order, then running the existing v9 control protocol.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_build_primary_surface_acquisition_packet.py](../scripts/01_build_primary_surface_acquisition_packet.py)",
        "- [01_primary_surface_acquisition_worksheet.csv](test_results/01_primary_surface_acquisition_worksheet.csv)",
        "- [01_primary_surface_acquisition_packet.json](test_results/01_primary_surface_acquisition_packet.json)",
        "- [01_primary_surface_acquisition_packet.md](test_results/01_primary_surface_acquisition_packet.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    write_csv(rows)
    result: dict[str, Any] = {
        "schema": "primary_surface_acquisition_packet.v1",
        "scope": "analysis_only_primary_surface_acquisition_handoff",
        "classification": "primary_surface_acquisition_packet_ready_no_source_integrated",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "worksheet": str(WORKSHEET.relative_to(ROOT)),
        "summary": {
            "worksheet_rows": len(rows),
            "required_fields": REQUIRED_FIELDS,
            "helper_fields": HELPER_FIELDS,
            "currently_valid_source": False,
            "external_surface_integrated": False,
            "v9_reduction_bits": 0.0,
        },
        "accepted_source_classes": ACCEPTABLE_SOURCE_CLASSES,
        "forbidden_source_classes": FORBIDDEN_SOURCE_CLASSES,
        "validation_command": [
            "python3",
            "analysis/external_authoring_surface_acquisition_audit_20260622/scripts/06_clean_topology_v9_control_protocol.py",
            "--input",
            str(WORKSHEET.relative_to(ROOT)),
        ],
        "decision": {
            "external_surface_integrated": False,
            "v9_reduction_bits": 0.0,
            "next_step": "fill worksheet with clean primary/authorized object-layer data and run the v9 control protocol",
        },
    }
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
