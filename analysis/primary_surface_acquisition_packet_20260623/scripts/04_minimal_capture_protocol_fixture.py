#!/usr/bin/env python3
"""Exercise the v9 protocol path with the minimal capture batch.

The generated CSV is a synthetic engineering fixture, not an external source.
It exists to verify that the recommended minimal capture batch can pass schema,
book matching, coverage, and split construction in the existing v9 protocol.
Any target result from this fixture is non-evidential by construction.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "primary_surface_acquisition_packet_20260623"
OUT_DIR = FRONT / "reports" / "test_results"
DESIGN_JSON = OUT_DIR / "03_minimal_capture_design.json"
DESIGN_CSV = OUT_DIR / "03_minimal_capture_design.csv"
FIXTURE_CSV = OUT_DIR / "04_minimal_capture_protocol_fixture.csv"
JSON_OUT = OUT_DIR / "04_minimal_capture_protocol_fixture.json"
MD_OUT = OUT_DIR / "04_minimal_capture_protocol_fixture.md"
PROTOCOL_OUT_DIR = OUT_DIR / "minimal_capture_protocol_fixture"
NO_FLAG_OUT_DIR = OUT_DIR / "minimal_capture_protocol_fixture_no_flag"
FINAL_OUT = FRONT / "reports" / "final_primary_surface_acquisition_packet.md"
PROTOCOL_SCRIPT = ROOT / "analysis" / "external_authoring_surface_acquisition_audit_20260622" / "scripts" / "06_clean_topology_v9_control_protocol.py"


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def fixture_rows() -> list[dict[str, str]]:
    design = load_json(DESIGN_JSON)
    selected = set(design["batches"]["balanced_v9_probe_22_books"])
    rows = [row for row in load_rows(DESIGN_CSV) if int(row["canonical_book"]) in selected]
    rows.sort(key=lambda row: (row["capture_batch"], int(row["batch_order"])))

    fixture = []
    for index, row in enumerate(rows):
        book = int(row["canonical_book"])
        fixture.append(
            {
                "source_id": "synthetic_minimal_capture_protocol_fixture",
                "source_rights": "synthetic_test_fixture_not_external_evidence",
                "source_version_or_date": "fixture_2026-06-23",
                "book_text_or_exact_prefix": row["canonical_prefix_32"],
                "x": str(32000 + index),
                "y": str(31000 + (index % 6)),
                "z": "8",
                "container_or_bookcase_id": "fixture_single_container",
                "slot_or_read_order": str(index),
                "capture_method": "synthetic_fixture_for_protocol_path_only",
                "orientation_or_side": "fixture_none",
                "notes": f"non-evidential protocol path fixture for canonical_book {book}",
                "canonical_book": str(book),
                "capture_batch": row["capture_batch"],
                "batch_order": row["batch_order"],
            }
        )
    return fixture


def write_fixture(rows: list[dict[str, str]]) -> None:
    fields = [
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
        "orientation_or_side",
        "notes",
        "canonical_book",
        "capture_batch",
        "batch_order",
    ]
    with FIXTURE_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run_protocol(output_dir: Path, allow_fixture: bool) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "python3",
        str(PROTOCOL_SCRIPT.relative_to(ROOT)),
        "--input",
        str(FIXTURE_CSV.relative_to(ROOT)),
        "--output-dir",
        str(output_dir.relative_to(ROOT)),
    ]
    if allow_fixture:
        command.append("--allow-non-evidence-fixture")
    subprocess.run(command, cwd=ROOT, check=True)
    return load_json(output_dir / "06_clean_topology_v9_control_protocol.json")


def write_markdown(data: dict[str, Any]) -> None:
    protocol = data["underlying_protocol_summary"]
    lines = [
        "# Minimal Capture Protocol Fixture",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This is a synthetic, non-evidential engineering fixture for the minimal capture batch.",
        "It verifies the protocol path only: CSV schema, prefix matching, coverage floor, joined v9 rows, and split construction.",
        "It must not be used as an external topology source or v9 reduction claim.",
        "",
        "## Protocol Path Result",
        "",
        f"- Fixture rows: `{data['fixture_rows']}`",
        f"- Unique matches: `{protocol['unique_matches']}`",
        f"- Derived matches: `{protocol['derived_matches']}`",
        f"- Coverage ok: `{protocol['coverage_ok']}`",
        f"- Split count: `{protocol['split_count']}`",
        f"- Joined v9 rows: `{protocol['joined_v9_rows']}`",
        f"- Fixture flag accepted: `{protocol['protocol_allow_non_evidence_fixture']}`",
        f"- Underlying protocol classification: `{protocol['classification']}`",
        f"- No-flag guard validation errors: `{data['no_flag_guard_summary']['validation_errors']}`",
        f"- No-flag guard unique matches: `{data['no_flag_guard_summary']['unique_matches']}`",
        "",
        "## Decision",
        "",
        "`minimal_capture_protocol_fixture_path_verified_not_evidence`.",
        "",
        "The minimal capture design is operationally runnable once real authorized object-layer fields exist.",
        "No external source is integrated, and any synthetic target behavior is non-evidential by construction.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def append_final() -> None:
    report = FINAL_OUT.read_text()
    marker = "## Minimal Capture Protocol Fixture"
    if marker in report:
        return
    addition = [
        "",
        marker,
        "",
        "A synthetic protocol fixture now verifies that the `balanced_v9_probe_22_books` capture batch can enter the v9 protocol path with sufficient schema, book matching, coverage, joined rows, and splits.",
        "This fixture is explicitly non-evidential and integrates no source; it only tests that the acquisition design is runnable once real authorized object-layer fields are supplied.",
        "",
        "- [04_minimal_capture_protocol_fixture.py](../scripts/04_minimal_capture_protocol_fixture.py)",
        "- [04_minimal_capture_protocol_fixture.csv](test_results/04_minimal_capture_protocol_fixture.csv)",
        "- [04_minimal_capture_protocol_fixture.json](test_results/04_minimal_capture_protocol_fixture.json)",
        "- [04_minimal_capture_protocol_fixture.md](test_results/04_minimal_capture_protocol_fixture.md)",
        "- [minimal_capture_protocol_fixture/06_clean_topology_v9_control_protocol.json](test_results/minimal_capture_protocol_fixture/06_clean_topology_v9_control_protocol.json)",
        "- [minimal_capture_protocol_fixture/06_clean_topology_v9_control_protocol.md](test_results/minimal_capture_protocol_fixture/06_clean_topology_v9_control_protocol.md)",
        "- [minimal_capture_protocol_fixture_no_flag/06_clean_topology_v9_control_protocol.json](test_results/minimal_capture_protocol_fixture_no_flag/06_clean_topology_v9_control_protocol.json)",
        "- [minimal_capture_protocol_fixture_no_flag/06_clean_topology_v9_control_protocol.md](test_results/minimal_capture_protocol_fixture_no_flag/06_clean_topology_v9_control_protocol.md)",
    ]
    FINAL_OUT.write_text(report.rstrip() + "\n" + "\n".join(addition) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = fixture_rows()
    write_fixture(rows)
    protocol = run_protocol(PROTOCOL_OUT_DIR, allow_fixture=True)
    no_flag = run_protocol(NO_FLAG_OUT_DIR, allow_fixture=False)
    derived_matches = len(protocol["match_summary"]["derived_matched_books"])
    data = {
        "schema": "minimal_capture_protocol_fixture.v1",
        "scope": "analysis_only_protocol_path_fixture_not_external_evidence",
        "classification": "minimal_capture_protocol_fixture_path_verified_not_evidence",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "fixture_csv": str(FIXTURE_CSV.relative_to(ROOT)),
        "protocol_output_dir": str(PROTOCOL_OUT_DIR.relative_to(ROOT)),
        "no_flag_guard_output_dir": str(NO_FLAG_OUT_DIR.relative_to(ROOT)),
        "fixture_rows": len(rows),
        "synthetic_fixture_not_external_evidence": True,
        "protocol_invocation_requires_allow_non_evidence_fixture": True,
        "external_surface_integrated": False,
        "v9_reduction_bits": 0.0,
        "underlying_protocol_summary": {
            "classification": protocol["classification"],
            "validation_errors": len(protocol["validation_errors"]),
            "unique_matches": protocol["match_summary"]["unique_matches"],
            "derived_matches": derived_matches,
            "coverage_ok": protocol["coverage_ok"],
            "split_count": protocol["split_count"],
            "joined_v9_rows": protocol["joined_v9_rows"],
            "protocol_external_surface_integrated": protocol["decision"]["external_surface_integrated"],
            "protocol_promoted_targets": protocol["decision"]["promoted_targets"],
            "protocol_promoted_targets_before_fixture_block": protocol["decision"].get("promoted_targets_before_fixture_block", []),
            "protocol_decision_reason": protocol["decision"]["reason"],
            "protocol_non_evidential_fixture": protocol["non_evidential_fixture"],
            "protocol_allow_non_evidence_fixture": protocol["allow_non_evidence_fixture"],
        },
        "no_flag_guard_summary": {
            "classification": no_flag["classification"],
            "validation_errors": len(no_flag["validation_errors"]),
            "unique_matches": no_flag["match_summary"]["unique_matches"],
            "coverage_ok": no_flag["coverage_ok"],
            "non_evidential_fixture": no_flag["non_evidential_fixture"],
            "allow_non_evidence_fixture": no_flag["allow_non_evidence_fixture"],
            "decision_reason": no_flag["decision"]["reason"],
        },
        "decision": {
            "external_surface_integrated": False,
            "v9_reduction_bits": 0.0,
            "next_step": "replace synthetic fixture fields with clean authorized object-layer data and run the v9 protocol",
        },
    }
    JSON_OUT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    write_markdown(data)
    append_final()
    print(json.dumps(data["underlying_protocol_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
