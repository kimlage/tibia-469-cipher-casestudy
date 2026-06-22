#!/usr/bin/env python3
"""External authoring-surface acquisition audit.

This front does not test another internal residual codec. It triages external
sources that could, in principle, reduce v9's remaining declared dependencies.
The key distinction is map/topology imagery vs object-layer provenance: v9 needs
event/source/order controls, not just a visible map.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/test_results"
FINAL_REPORT = ROOT / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/final_external_authoring_surface_acquisition_audit.md"


def fetch_json(url: str) -> tuple[Any | None, str | None]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "tibia-469-casestudy-audit"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.load(r), None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, repr(exc)


def fetch_text(url: str) -> tuple[str | None, str | None]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "tibia-469-casestudy-audit"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read().decode("utf-8"), None
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as exc:
        return None, repr(exc)


def github_dir_probe(repo: str, path: str = "") -> dict[str, Any]:
    suffix = f"/{path}" if path else ""
    url = f"https://api.github.com/repos/{repo}/contents{suffix}"
    data, error = fetch_json(url)
    if error:
        return {"repo": repo, "path": path, "url": url, "error": error, "entries": []}
    entries = [
        {
            "name": item.get("name"),
            "type": item.get("type"),
            "size": item.get("size"),
        }
        for item in data
    ]
    return {"repo": repo, "path": path, "url": url, "error": None, "entries": entries}


def summarize_historical_map_repo() -> dict[str, Any]:
    repo = "tibiamaps/tibia-historical-map-data"
    root = github_dir_probe(repo)
    folders = {}
    for version in ["7.3", "7.4", "7.5", "7.7"]:
        probe = github_dir_probe(repo, version)
        entries = probe["entries"]
        folders[version] = {
            "entry_count": len(entries),
            "png_count": sum(1 for e in entries if str(e["name"]).endswith(".png")),
            "json_count": sum(1 for e in entries if str(e["name"]).endswith(".json")),
            "sample_entries": entries[:8],
            "error": probe["error"],
        }
    readme_url = "https://raw.githubusercontent.com/tibiamaps/tibia-historical-map-data/main/README.md"
    readme, readme_error = fetch_text(readme_url)
    return {
        "repo": repo,
        "web_url": "https://github.com/tibiamaps/tibia-historical-map-data",
        "root_entries": root["entries"],
        "folders": folders,
        "readme_url": readme_url,
        "readme_error": readme_error,
        "readme_key_claims": [
            "Historical Tibia maps, explored or edited using official references only.",
            "Files in the 7.7 folder were generated from official leaked files.",
        ]
        if readme and "official leaked files" in readme
        else [],
    }


def summarize_current_map_repo() -> dict[str, Any]:
    repo = "tibiamaps/tibia-map-data"
    root = github_dir_probe(repo)
    data = github_dir_probe(repo, "data")
    readme_url = "https://raw.githubusercontent.com/tibiamaps/tibia-map-data/main/README.md"
    readme, readme_error = fetch_text(readme_url)
    marker_json_count = sum(1 for e in data["entries"] if str(e["name"]).endswith(".json"))
    return {
        "repo": repo,
        "web_url": "https://github.com/tibiamaps/tibia-map-data",
        "root_entries": root["entries"][:20],
        "data_entry_count": len(data["entries"]),
        "data_json_count": marker_json_count,
        "data_sample_entries": data["entries"][:12],
        "readme_url": readme_url,
        "readme_error": readme_error,
        "readme_key_claims": [
            "custom format has PNG map, PNG pathfinding, and JSON marker info",
            "data can be generated from official Tibia minimap files",
        ]
        if readme and "JSON file containing the marker info" in readme
        else [],
    }


def candidate_matrix(probes: dict[str, Any]) -> list[dict[str, Any]]:
    historical = probes["tibiamaps_historical_map_data"]
    current = probes["tibiamaps_current_map_data"]
    hist_has_only_png = all(
        folder["png_count"] > 0 and folder["json_count"] == 0
        for folder in historical["folders"].values()
        if not folder["error"]
    )
    return [
        {
            "candidate": "tibiamaps_historical_map_data",
            "classification": "WEAK_EXTERNAL_SURFACE_CANDIDATE_MAP_GEOMETRY_ONLY",
            "provenance": "public GitHub repository with 7.3/7.4/7.5/7.7 historical map PNGs; README says official references and 7.7 generated from official leaked files",
            "observed_artifact_shape": "version folders contain PNG floor maps; no JSON/object-layer files observed in API probe",
            "coverage_potential": "historical floor geometry; possible Hellgate room coordinate context",
            "v9_fields_potentially_reduced": ["book_order_topology"],
            "v9_fields_not_reduced_without_object_layer": [
                "event_schedule_and_coarse_control",
                "copy_literal_decision_policy",
                "non_continuation_copy_source_length",
                "innovation_replay_event_starts",
                "row0_table",
            ],
            "sufficiency_test": "needs book object/container/slot/order data, not only floor imagery",
            "control_plan_if_acquired": "map-derived order must beat public-bookcase and permuted coordinate controls on v9 residual fields",
            "blocking_issue": "object layer absent in observed repository shape; leaked-file provenance cannot be treated as official attestation without policy/legal review",
            "probe_evidence": {
                "hist_has_only_png": hist_has_only_png,
                "folders": historical["folders"],
            },
        },
        {
            "candidate": "tibiamaps_current_map_data",
            "classification": "AUDIT_ONLY_MAP_AND_MARKER_SURFACE",
            "provenance": "public GitHub repository backing TibiaMaps.io; README describes PNG maps, pathfinding PNGs, and JSON marker info generated from minimap data",
            "observed_artifact_shape": f"data folder has {current['data_entry_count']} entries and {current['data_json_count']} JSON file(s) in the root-level probe",
            "coverage_potential": "current minimap and marker context",
            "v9_fields_potentially_reduced": ["book_order_topology"],
            "v9_fields_not_reduced_without_object_layer": [
                "copy_literal_decision_policy",
                "non_continuation_copy_source_length",
                "row0_table",
            ],
            "sufficiency_test": "marker/minimap data would need explicit Hellgate book object slots; current probe does not show that",
            "control_plan_if_acquired": "compare marker/order variables against shuffled marker and book-order controls",
            "blocking_issue": "modern/current map surface is not historical authoring order and not an object-content layer",
        },
        {
            "candidate": "tibiawiki_hellgate_library_bookcase_order",
            "classification": "REJECTED_ALREADY_TESTED_PUBLIC_BOOKCASE_SURFACE",
            "provenance": "community Hellgate Library page/bookcase order already compiled into local public topology manifest",
            "observed_artifact_shape": "bookcase/order listing with ambiguous entries and no exact tile/slot/orientation",
            "coverage_potential": "70/70 local books covered by candidate matching; 65 resolved unique entries in audit",
            "v9_fields_potentially_reduced": [],
            "v9_fields_not_reduced_without_object_layer": [
                "event_schedule_and_coarse_control",
                "copy_literal_decision_policy",
                "non_continuation_copy_source_length",
            ],
            "sufficiency_test": "already failed residual-stream topology controls",
            "control_plan_if_acquired": "none; use only as baseline public-order control",
            "blocking_issue": "public overview order is not authorial read order and failed controls",
        },
        {
            "candidate": "otbm_or_old_client_object_layer",
            "classification": "BLOCKED_NEEDS_ALLOWED_PRIMARY_OR_NEAR_PRIMARY_OBJECT_SOURCE",
            "provenance": "would require an allowed old client/map/object extraction, OTBM with book containers, or official/in-game capture",
            "observed_artifact_shape": "not present in repo; web search finds unofficial/leaked/private-server routes but no validated allowed object dataset",
            "coverage_potential": "could supply x/y/z, container ID, slot, insertion/read order for the 70 books",
            "v9_fields_potentially_reduced": [
                "book_order_topology",
                "event_schedule_and_coarse_control",
                "copy_literal_decision_policy",
            ],
            "v9_fields_not_reduced_without_object_layer": [
                "row0_table",
                "literal_innovation_payload_residual",
            ],
            "sufficiency_test": "must cover the 70 books and expose object/container/slot metadata with date/version",
            "control_plan_if_acquired": "prefix/family holdout and coordinate/order permutation controls against v9 residual fields",
            "blocking_issue": "availability, legality/provenance, and exact coverage are unverified",
        },
        {
            "candidate": "historical_corpus_variants_or_authoring_drafts",
            "classification": "BLOCKED_NEEDS_VERSIONED_TEXT_OR_SCRIPT_SOURCE",
            "provenance": "would require timestamped official/client/community captures, authoring scripts, workbook, or old variants",
            "observed_artifact_shape": "not found in current repo or this external probe",
            "coverage_potential": "could explain innovation replay starts and copy/source lineage if variants show incremental construction",
            "v9_fields_potentially_reduced": [
                "innovation_replay_event_starts",
                "non_continuation_copy_source_length",
                "literal_innovation_payload_residual",
            ],
            "v9_fields_not_reduced_without_object_layer": ["book_order_topology", "row0_table"],
            "sufficiency_test": "variant chronology must predict replay/source events above shuffled-variant controls",
            "control_plan_if_acquired": "align variants to v9 events; compare against shuffled chronology and random span controls",
            "blocking_issue": "no versioned source located",
        },
    ]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    probes = {
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "tibiamaps_historical_map_data": summarize_historical_map_repo(),
        "tibiamaps_current_map_data": summarize_current_map_repo(),
    }
    candidates = candidate_matrix(probes)
    promoted = [c for c in candidates if c["classification"].startswith("PROMOTED")]
    blocked = [c for c in candidates if c["classification"].startswith("BLOCKED")]

    result = {
        "schema": "external_authoring_surface_acquisition_gate.v1",
        "scope": "analysis_only_external_authoring_surface_acquisition",
        "classification": "external_authoring_surface_not_acquired_object_layer_required",
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "summary": {
            "candidate_count": len(candidates),
            "promoted_external_sources": len(promoted),
            "blocked_source_classes": len(blocked),
            "new_candidate": "tibiamaps_historical_map_data",
            "new_candidate_status": "weak_map_geometry_only_not_object_layer",
            "required_next_artifact": "object/container/slot/order layer for Hellgate books, or versioned authoring/script/draft source",
            "v9_reduction": 0.0,
        },
        "probes": probes,
        "candidate_matrix": candidates,
        "decision": {
            "external_surface_acquired": False,
            "decoder_integrated": False,
            "reason": "no candidate currently supplies object/container/slot/order or versioned authoring provenance required to reduce v9 residual fields",
            "do_not_do_next": [
                "internal source/length/copy-hint/literal subcodecs",
                "map-image-only promotion",
                "semantic/plaintext reopening",
            ],
            "do_next_only_if_available": [
                "allowed old-client/object-layer extraction",
                "primary CipSoft/in-game object metadata",
                "timestamped historical variants or authoring script/workbook",
            ],
        },
        "source_urls": [
            "https://github.com/tibiamaps/tibia-historical-map-data",
            "https://github.com/tibiamaps/tibia-map-data",
            "https://tibiamaps.io/guides/map-file-format",
            "https://tibiamaps.io/guides/minimap-file-format",
            "https://tibia.fandom.com/wiki/Hellgate_Library",
        ],
    }

    json_path = OUT_DIR / "01_external_authoring_surface_acquisition_gate.json"
    md_path = OUT_DIR / "01_external_authoring_surface_acquisition_gate.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines: list[str] = []
    lines.append("# External Authoring Surface Acquisition Gate")
    lines.append("")
    lines.append("Classification: `external_authoring_surface_not_acquired_object_layer_required`")
    lines.append("Translation delta: `NONE`")
    lines.append("Plaintext claim: `False`")
    lines.append("Case reopened: `False`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        "The next useful external route is not another public bookcase list or map image. "
        "It must expose an object/container/slot/order layer or versioned authoring trace."
    )
    lines.append("")
    lines.append(
        "A new candidate source was identified: `tibiamaps/tibia-historical-map-data`. "
        "It is useful enough to track because it has historical 7.3/7.4/7.5/7.7 map folders, "
        "but the API probe observes PNG floor maps rather than object/book metadata. "
        "It is therefore map-geometry only, not a promoted authoring surface."
    )
    lines.append("")
    lines.append("## Candidate Matrix")
    lines.append("")
    lines.append("| Candidate | Classification | Potential v9 Fields | Blocking Issue |")
    lines.append("| --- | --- | --- | --- |")
    for c in candidates:
        fields = ", ".join(c["v9_fields_potentially_reduced"]) if c["v9_fields_potentially_reduced"] else "none"
        lines.append(f"| `{c['candidate']}` | `{c['classification']}` | {fields} | {c['blocking_issue']} |")
    lines.append("")
    lines.append("## Sufficient Artifact Contract")
    lines.append("")
    lines.append("A promotable source must provide, at minimum:")
    lines.append("")
    lines.append("- version/date and provenance")
    lines.append("- coverage for the 70 books or a declared subset with holdout")
    lines.append("- `book_id` or exact text match")
    lines.append("- `x/y/z` or equivalent physical coordinate")
    lines.append("- container/bookcase object identity")
    lines.append("- slot/read/order or insertion/order metadata")
    lines.append("- enough structure to test against coordinate/order permutation controls")
    lines.append("")
    lines.append("Map PNGs alone fail this contract because they do not identify book objects or slots.")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("No external source is acquired or integrated into v9. Net v9 reduction: `0.0` bits.")
    lines.append("")
    lines.append(
        "`external_authoring_surface_not_acquired_object_layer_required`: the blocker is now concrete. "
        "The next external push should seek an allowed object-layer source or historical variants, not more internal residual coding."
    )
    lines.append("")
    lines.append("`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.")
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    for url in result["source_urls"]:
        lines.append(f"- {url}")
    md_path.write_text("\n".join(lines) + "\n")

    final_lines = list(lines)
    final_lines[0] = "# Final External Authoring Surface Acquisition Audit"
    final_lines.append("")
    final_lines.append("## Reproducible Artifacts")
    final_lines.append("")
    final_lines.append("- [01_external_authoring_surface_acquisition_gate.py](../scripts/01_external_authoring_surface_acquisition_gate.py)")
    final_lines.append("- [01_external_authoring_surface_acquisition_gate.json](test_results/01_external_authoring_surface_acquisition_gate.json)")
    final_lines.append("- [01_external_authoring_surface_acquisition_gate.md](test_results/01_external_authoring_surface_acquisition_gate.md)")
    FINAL_REPORT.write_text("\n".join(final_lines) + "\n")


if __name__ == "__main__":
    main()
