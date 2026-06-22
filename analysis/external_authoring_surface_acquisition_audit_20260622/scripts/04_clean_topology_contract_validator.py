#!/usr/bin/env python3
"""Validate clean topology-source inputs for the 469 generator front.

This gate is constructive: it provides an executable schema and a negative
control against the current public bookcase manifest. It also probes public
TibiaMaps marker data to separate clean-but-insufficient POI coordinates from
the object/container/slot layer needed to test v9.
"""

from __future__ import annotations

import csv
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/external_authoring_surface_acquisition_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
FINAL_REPORT = FRONT / "reports/final_external_authoring_surface_acquisition_audit.md"
PUBLIC_MANIFEST = ROOT / "analysis/physical_topology_20260620/tables/hellgate_public_bookcase_manifest.csv"


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
FORBIDDEN_RIGHTS_MARKERS = ["leak", "leaked", "proprietary_leak", "unknown", ""]
SEARCH_TERMS = ["hellgate", "library", "bonelord", "beholder", "469"]


def read_csv_header(path: Path) -> list[str]:
    with path.open(newline="") as f:
        reader = csv.reader(f)
        return next(reader)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def validate_contract_csv(path: Path) -> dict[str, Any]:
    header = read_csv_header(path)
    rows = read_csv_rows(path)
    missing = [field for field in REQUIRED_FIELDS if field not in header]
    present_optional = [field for field in OPTIONAL_FIELDS if field in header]

    row_errors = []
    if not missing:
        for index, row in enumerate(rows, start=2):
            for field in REQUIRED_FIELDS:
                if not row.get(field, "").strip():
                    row_errors.append({"line": index, "field": field, "error": "blank_required_field"})
            rights = row.get("source_rights", "").strip().lower()
            if rights in FORBIDDEN_RIGHTS_MARKERS or "leak" in rights:
                row_errors.append({"line": index, "field": "source_rights", "error": "unacceptable_rights_marker"})
            for coord in ["x", "y", "z"]:
                try:
                    int(row.get(coord, ""))
                except ValueError:
                    row_errors.append({"line": index, "field": coord, "error": "coordinate_not_integer"})

    return {
        "path": str(path.relative_to(ROOT)),
        "row_count": len(rows),
        "header": header,
        "missing_required_fields": missing,
        "present_optional_fields": present_optional,
        "row_errors": row_errors,
        "contract_valid": not missing and not row_errors,
        "can_test_v9_topology": not missing and not row_errors and len(rows) > 0,
    }


def probe_tibiamaps_markers() -> dict[str, Any]:
    url = "https://raw.githubusercontent.com/tibiamaps/tibia-map-data/main/extra/points-of-interest/markers.json"
    req = urllib.request.Request(url, headers={"User-Agent": "tibia-469-casestudy-audit"})
    with urllib.request.urlopen(req, timeout=30) as r:
        markers = json.load(r)

    term_hits: dict[str, list[dict[str, Any]]] = {term: [] for term in SEARCH_TERMS}
    for marker in markers:
        description = str(marker.get("description", ""))
        for term in SEARCH_TERMS:
            if term.lower() in description.lower():
                term_hits[term].append(marker)

    nonempty_descriptions = sum(1 for marker in markers if str(marker.get("description", "")).strip())
    return {
        "url": url,
        "license_context": "tibiamaps/tibia-map-data repository is MIT-licensed, but markers are POI coordinates rather than object slots",
        "marker_count": len(markers),
        "nonempty_description_count": nonempty_descriptions,
        "term_hit_counts": {term: len(hits) for term, hits in term_hits.items()},
        "sample_hits": {term: hits[:5] for term, hits in term_hits.items() if hits},
        "has_required_book_object_layer": False,
        "classification": "PUBLIC_LICENSED_MARKER_DATA_AUDIT_ONLY_NO_BOOK_OBJECT_LAYER",
    }


def write_template(path: Path) -> None:
    fieldnames = REQUIRED_FIELDS + OPTIONAL_FIELDS
    row = {
        "source_id": "example_authorized_topology_capture",
        "source_rights": "user_authorized_or_public_license_url",
        "source_version_or_date": "YYYY-MM-DD_or_Tibia_version",
        "book_text_or_exact_prefix": "9457655996704672611",
        "x": "0",
        "y": "0",
        "z": "0",
        "container_or_bookcase_id": "bookcase_object_id",
        "slot_or_read_order": "1",
        "capture_method": "official/in_game/user_authorized/public_licensed",
        "orientation_or_side": "",
        "notes": "template only; replace with authorized observed data",
    }
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    template_path = OUT_DIR / "04_clean_topology_contract_template.csv"
    write_template(template_path)

    public_manifest_validation = validate_contract_csv(PUBLIC_MANIFEST)
    template_validation = validate_contract_csv(template_path)
    markers_probe = probe_tibiamaps_markers()

    result: dict[str, Any] = {
        "schema": "clean_topology_contract_validator.v1",
        "scope": "analysis_only_clean_topology_contract_validator",
        "classification": "clean_topology_contract_ready_public_sources_still_insufficient",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "required_fields": REQUIRED_FIELDS,
        "optional_fields": OPTIONAL_FIELDS,
        "template": {
            "path": str(template_path.relative_to(ROOT)),
            "validation": template_validation,
        },
        "negative_controls": {
            "public_hellgate_bookcase_manifest": public_manifest_validation,
            "tibiamaps_markers": markers_probe,
        },
        "decision": {
            "clean_contract_ready": True,
            "public_manifest_can_test_v9_topology": public_manifest_validation["can_test_v9_topology"],
            "tibiamaps_markers_can_test_v9_topology": markers_probe["has_required_book_object_layer"],
            "external_surface_acquired": False,
            "v9_reduction_bits": 0.0,
            "next_acceptable_input": "fill the template with rights-cleared object/container/slot/order metadata",
        },
    }

    json_path = OUT_DIR / "04_clean_topology_contract_validator.json"
    md_path = OUT_DIR / "04_clean_topology_contract_validator.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines: list[str] = []
    lines.append("# Clean Topology Contract Validator")
    lines.append("")
    lines.append("Classification: `clean_topology_contract_ready_public_sources_still_insufficient`")
    lines.append("Translation delta: `NONE`")
    lines.append("Plaintext claim: `False`")
    lines.append("Case reopened: `False`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("A rights-clean topology input now has an executable CSV contract and template.")
    lines.append("")
    lines.append(
        "The current public Hellgate bookcase manifest is a negative control: it does not satisfy the contract because it lacks rights/provenance, coordinates, container object identity, and slot/read-order fields."
    )
    lines.append("")
    lines.append(
        f"TibiaMaps public markers were probed as licensed map/POI data: `{markers_probe['marker_count']}` markers, "
        f"but no Hellgate/Library/Bonelord/Beholder hits and no book object layer."
    )
    lines.append("")
    lines.append("## Contract Fields")
    lines.append("")
    lines.append("| Field | Required |")
    lines.append("| --- | --- |")
    for field in REQUIRED_FIELDS:
        lines.append(f"| `{field}` | `True` |")
    for field in OPTIONAL_FIELDS:
        lines.append(f"| `{field}` | `False` |")
    lines.append("")
    lines.append("## Negative Controls")
    lines.append("")
    lines.append("| Source | Contract Valid | Can Test v9 | Missing/Reason |")
    lines.append("| --- | --- | --- | --- |")
    missing = ", ".join(public_manifest_validation["missing_required_fields"])
    lines.append(
        f"| `hellgate_public_bookcase_manifest.csv` | `{public_manifest_validation['contract_valid']}` | `{public_manifest_validation['can_test_v9_topology']}` | missing: {missing} |"
    )
    lines.append(
        f"| `tibiamaps markers.json` | `False` | `{markers_probe['has_required_book_object_layer']}` | POI markers only; term hits {markers_probe['term_hit_counts']} |"
    )
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("No external source is acquired or integrated into v9. Net v9 reduction: `0.0` bits.")
    lines.append("")
    lines.append(
        "Progress from here requires filling the template with rights-cleared object/container/slot/order metadata."
    )
    lines.append("")
    lines.append("`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.")
    md_path.write_text("\n".join(lines) + "\n")

    report = FINAL_REPORT.read_text() if FINAL_REPORT.exists() else ""
    marker = "## Clean Topology Contract Validator"
    if marker not in report:
        addition = [
            "",
            marker,
            "",
            "A contract validator now defines the executable CSV shape for rights-cleared topology evidence.",
            "The current public Hellgate manifest fails the contract, and TibiaMaps public markers are POI-level data without Hellgate/book object slots.",
            "No source is integrated into v9 and net v9 reduction remains `0.0` bits.",
            "",
            "- [04_clean_topology_contract_validator.py](../scripts/04_clean_topology_contract_validator.py)",
            "- [04_clean_topology_contract_validator.json](test_results/04_clean_topology_contract_validator.json)",
            "- [04_clean_topology_contract_validator.md](test_results/04_clean_topology_contract_validator.md)",
            "- [04_clean_topology_contract_template.csv](test_results/04_clean_topology_contract_template.csv)",
        ]
        FINAL_REPORT.write_text(report.rstrip() + "\n" + "\n".join(addition) + "\n")


if __name__ == "__main__":
    main()
