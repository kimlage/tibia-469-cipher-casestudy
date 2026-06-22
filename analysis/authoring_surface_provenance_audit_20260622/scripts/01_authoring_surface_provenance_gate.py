#!/usr/bin/env python3
"""Audit whether v9 residual tapes map to an external authoring surface.

This is intentionally not a new internal codec. It reads the current executable
ledger artifacts and asks whether any known external/provenance surface can
replace post-hoc residual declarations.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "analysis/authoring_surface_provenance_audit_20260622/reports/test_results"
FINAL_REPORT = ROOT / "analysis/authoring_surface_provenance_audit_20260622/reports/final_authoring_surface_provenance_audit.md"


def load_json(path: str) -> dict[str, Any]:
    with (ROOT / path).open() as f:
        return json.load(f)


def safe_read(path: str) -> str:
    p = ROOT / path
    return p.read_text() if p.exists() else ""


def bits_for_choice_count(n: int) -> float:
    return math.log2(n) if n > 1 else 0.0


def build_dependency_ledger(
    minimal: dict[str, Any],
    v7: dict[str, Any],
    v8: dict[str, Any],
    v9: dict[str, Any],
    topology: dict[str, Any],
) -> list[dict[str, Any]]:
    min_summary = minimal["summary"]
    v7_summary = v7["summary"]
    v8_summary = v8["summary"]
    v9_summary = v9["summary"]
    topo_summary = topology["summary"]

    # These are fields the decoder still needs to be told or pay for after v9.
    return [
        {
            "dependency": "event_schedule_and_coarse_control",
            "current_status": "partially_programmed_paid",
            "v9_or_recent_bits": v7_summary["online_x64_coarse_bits"],
            "coverage": "books_10_69; 261 ops; x64 exact sequence before correction 37/60 books",
            "what_it_controls": "op_count plus coarse type:length_bucket sequence; target_start derives from resulting lengths",
            "still_external": "beam ranks/corrections for misses; event policy not authorially sourced",
            "target_text_dependency": False,
            "candidate_external_surface": [
                "physical book order/topology",
                "internal insertion IDs",
                "historical map coordinates",
            ],
            "evidence_status": "x64 internal program promoted, but public topology control signal not promoted",
            "provenance_gate": "no external control source promoted",
        },
        {
            "dependency": "copy_literal_decision_policy",
            "current_status": "external_event_policy",
            "v9_or_recent_bits": None,
            "coverage": "all copy/literal event choices in derived books",
            "what_it_controls": "whether the next emitted event is copy or literal",
            "still_external": "v9 can execute the schedule but does not derive why event type occurs there",
            "target_text_dependency": True,
            "candidate_external_surface": [
                "authoring worksheet operation marks",
                "bookcase/order annotations",
                "source workbook/script",
            ],
            "evidence_status": "no primary source or topology variable currently predicts this policy",
            "provenance_gate": "blocked without source worksheet/script or primary map/object order",
        },
        {
            "dependency": "non_continuation_copy_source_length",
            "current_status": "mostly_external_paid",
            "v9_or_recent_bits": v7_summary["copy_bits"] - v9_summary["source_bits_saved"] + v9_summary["continuation_pattern_bits"],
            "coverage": "208 copy ops; v9 derives only 5/17 copy-after-copy continuation opportunities",
            "what_it_controls": "copy source and source/length choice when not explained by endpoint/continuation rules",
            "still_external": "non-continuation source-length choices and fallback hints remain paid",
            "target_text_dependency": True,
            "candidate_external_surface": [
                "content-addressed authoring chunks",
                "book insertion/order IDs",
                "historical corpus variants",
            ],
            "evidence_status": "v9 reduces source bits narrowly; no external source identifies source chunks",
            "provenance_gate": "blocked without authoring surface tying chunk choice to observable IDs/topology",
        },
        {
            "dependency": "residual_composition_index",
            "current_status": "external_paid",
            "v9_or_recent_bits": v7_summary["residual_composition_bits"],
            "coverage": "fine exact lengths within coarse buckets after book-length constraints",
            "what_it_controls": "exact residual lengths once coarse buckets and book length are known",
            "still_external": "composition rank/index per book remains declared",
            "target_text_dependency": False,
            "candidate_external_surface": [
                "physical line breaks or book layout",
                "authoring spreadsheet columns",
                "map/object ordering",
            ],
            "evidence_status": "remaining-tape/topology coupling gates did not promote a predictor",
            "provenance_gate": "blocked without primary layout/worksheet evidence",
        },
        {
            "dependency": "innovation_replay_event_starts",
            "current_status": "target_conditioned_paid_replay",
            "v9_or_recent_bits": v7_summary["payload_replay_bits"],
            "coverage": "1962-digit innovation stream; replay copies 1000 digits and leaves 962 literal digits",
            "what_it_controls": "where seed/literal innovation chunks are introduced and replayed",
            "still_external": "replay starts and copy/literal starts are known from the target stream",
            "target_text_dependency": True,
            "candidate_external_surface": [
                "seed draft text/workbook",
                "source script",
                "historical incremental versions",
            ],
            "evidence_status": "unified innovation payload is promoted only as replay ledger, not source-free generator",
            "provenance_gate": "blocked without historical drafts or script provenance",
        },
        {
            "dependency": "literal_innovation_payload_residual",
            "current_status": "partially_modeled_paid",
            "v9_or_recent_bits": v8_summary["selected_markov_bits_after_declaration"],
            "coverage": "962 literal innovation digits after replay",
            "what_it_controls": "literal digits not copied inside the innovation replay",
            "still_external": "Markov model reduces declaration but does not derive authorial source",
            "target_text_dependency": True,
            "candidate_external_surface": [
                "authoring random-number source",
                "spreadsheet formula/script",
                "versioned draft stream",
            ],
            "evidence_status": "literal Markov ledger promoted as paid reduction only",
            "provenance_gate": "blocked without source artifact",
        },
        {
            "dependency": "row0_table",
            "current_status": "exogenous",
            "v9_or_recent_bits": 160.521,
            "coverage": "99/100 ordered codes; missing 39; 19/91 conflict clue",
            "what_it_controls": "2-digit code to 14-symbol substrate",
            "still_external": "manual/semimanual 10x10 worksheet remains the best current explanation",
            "target_text_dependency": False,
            "candidate_external_surface": [
                "CipSoft/in-game symbol table",
                "authorial worksheet",
                "primary historical script",
            ],
            "evidence_status": "row0_origin_exogenous_under_current_evidence",
            "provenance_gate": "blocked until primary source or paid holdout formula appears",
        },
        {
            "dependency": "book_order_topology",
            "current_status": "granted_or_weak_public_manifest",
            "v9_or_recent_bits": bits_for_choice_count(70),
            "coverage": f"{topo_summary['resolved_unique_topology_books']} resolved unique topology books; {topo_summary['covered_books']} covered books in residual target tests",
            "what_it_controls": "canonical traversal/order, possible bookcase grouping, possible physical context",
            "still_external": "public topology is partial and failed residual stream controls",
            "target_text_dependency": False,
            "candidate_external_surface": [
                "real historical map coordinates",
                "tile/slot/orientation",
                "internal book object IDs",
            ],
            "evidence_status": "PARTIAL_TOPOLOGY_CONTROL_SIGNAL_NOT_PROMOTED",
            "provenance_gate": "weak surface only; not enough to replace v9 residual declarations",
        },
    ]


def build_source_candidates(topology: dict[str, Any]) -> list[dict[str, Any]]:
    target_summaries = topology["summary"]["target_summaries"]
    return [
        {
            "candidate": "partial_public_hellgate_topology_manifest",
            "source_type": "local public/topology manifest",
            "provenance": "analysis/physical_topology_20260620/tables/hellgate_public_bookcase_manifest.csv plus committed audit",
            "date_or_version": "compiled in repo; original public surface not complete enough for primary authoring order",
            "coverage": "64 resolved unique topology books; 54 books/237 operations usable in residual tests",
            "decoder_field_reduced": [],
            "control_test": "prefix and leave-bookcase residual stream tests with 150 permutation trials",
            "cost_or_effect": {
                "coarse_control_saving_bits": target_summaries["coarse_control"]["total_saving_bits"],
                "copy_hint_rank_bucket_saving_bits": target_summaries["copy_hint_rank_bucket"]["total_saving_bits"],
                "op_type_saving_bits": target_summaries["op_type"]["total_saving_bits"],
            },
            "contradictions": "all tested targets have negative savings and fail permutation p95",
            "classification": "REJECTED_PROVENANCE_CONTROL",
            "notes": "This is the only already-tested external-ish surface; it cannot be integrated into v9 as a promoted source.",
        },
        {
            "candidate": "community_book_pages_fandom_tibiawiki",
            "source_type": "secondary/community book catalog",
            "provenance": "TibiaWiki/Fandom book pages list location, version, author unknown, and book text; 469 overview says many claimed translations lack proof",
            "date_or_version": "community pages; example book page lists Version 6.2 / June 10, 2001",
            "coverage": "book texts and locations exist for at least individual Hellgate Library books; not a primary authoring surface",
            "decoder_field_reduced": [],
            "control_test": "not usable as a source-control variable without primary order/slot/ID metadata",
            "cost_or_effect": {},
            "contradictions": "documents text/location but not authorial event schedule, source chunks, row0, or operation policy",
            "classification": "WEAK_PROVENANCE_CLUE",
            "notes": "Useful for corpus provenance only; not enough to reduce v9 residual fields.",
        },
        {
            "candidate": "s2ward_469_repository",
            "source_type": "community extract/analysis repository",
            "provenance": "public GitHub repository with collected books/alignment attempts and historical/community clues",
            "date_or_version": "public repository; not a CipSoft primary source",
            "coverage": "corpus-level book text collection and community analysis materials",
            "decoder_field_reduced": [],
            "control_test": "already treated as corpus provenance; no primary insertion IDs or authoring worksheet",
            "cost_or_effect": {},
            "contradictions": "contains/reflects community extraction and rearrangement work, not authorial control variables",
            "classification": "AUDIT_ONLY",
            "notes": "Preserves data lineage but cannot substitute for v9 event/source policies.",
        },
        {
            "candidate": "tibiawiki_br_469_article",
            "source_type": "secondary/community theory article",
            "provenance": "Portuguese TibiaWiki page collecting lore/speculation such as 486/cryptography/computer references",
            "date_or_version": "current public wiki page; not a primary artifact",
            "coverage": "lore/theory surface, not the 70-book authoring order",
            "decoder_field_reduced": [],
            "control_test": "not an executable control source; no tested variable predicts v9 residual streams",
            "cost_or_effect": {},
            "contradictions": "speculative allusion layer does not supply row0 labels, event schedule, or source/length policy",
            "classification": "REJECTED_PROVENANCE_CONTROL",
            "notes": "Kept out of semantic/plaintext path by design.",
        },
        {
            "candidate": "official_cipsoft_or_ingame_authoring_surface",
            "source_type": "primary source required but absent",
            "provenance": "would need official CipSoft source, in-game object metadata, map/object IDs, script/workbook, or exact book-to-control crib",
            "date_or_version": "none identified in repo or current public sweep",
            "coverage": "unknown",
            "decoder_field_reduced": [
                "book_order_topology",
                "event_schedule_and_coarse_control",
                "copy_literal_decision_policy",
                "non_continuation_copy_source_length",
                "row0_table",
            ],
            "control_test": "would require prediction against v9 residual fields and permutation/order controls",
            "cost_or_effect": {},
            "contradictions": "not currently available",
            "classification": "BLOCKED_NEEDS_PRIMARY_SOURCE",
            "notes": "This is the only class that could materially reopen authoring-surface provenance.",
        },
        {
            "candidate": "historical_client_map_or_object_id_data",
            "source_type": "primary/near-primary data required but absent",
            "provenance": "old client/map data with tile/slot/orientation/object insertion order would be needed",
            "date_or_version": "none committed or verified for this audit",
            "coverage": "unknown; must cover enough of the 70 books to beat controls",
            "decoder_field_reduced": [
                "book_order_topology",
                "event_schedule_and_coarse_control",
                "copy_literal_decision_policy",
            ],
            "control_test": "prefix/family holdout plus permuted map/order controls",
            "cost_or_effect": {},
            "contradictions": "public partial topology already failed as a residual predictor",
            "classification": "BLOCKED_NEEDS_PRIMARY_SOURCE",
            "notes": "Potentially valuable only if it gives more than the partial public topology already rejected.",
        },
        {
            "candidate": "historical_corpus_variants_or_incremental_drafts",
            "source_type": "primary/near-primary history required but absent",
            "provenance": "would need timestamped versions, screenshots, old exports with variants, or authoring drafts",
            "date_or_version": "none identified",
            "coverage": "unknown",
            "decoder_field_reduced": [
                "innovation_replay_event_starts",
                "literal_innovation_payload_residual",
                "non_continuation_copy_source_length",
            ],
            "control_test": "variant order must predict replay/source events better than shuffled variant controls",
            "cost_or_effect": {},
            "contradictions": "current community corpus is a static extract, not a versioned authoring trace",
            "classification": "BLOCKED_NEEDS_PRIMARY_SOURCE",
            "notes": "This is the most direct route for innovation/source provenance, but no artifact is available.",
        },
    ]


def main() -> None:
    minimal = load_json("analysis/minimal_external_tape_program_audit_20260622/reports/test_results/02_unified_external_tape_ledger.json")
    v7 = load_json("analysis/executable_v7_unified_innovation_payload_audit_20260622/reports/test_results/01_executable_v7_unified_innovation_payload_gate.json")
    v8 = load_json("analysis/executable_v8_innovation_literal_markov_audit_20260622/reports/test_results/01_executable_v8_innovation_literal_markov_gate.json")
    v9 = load_json("analysis/executable_v9_innovation_copy_continuation_audit_20260622/reports/test_results/01_executable_v9_innovation_copy_continuation_gate.json")
    topology = load_json("analysis/physical_topology_control_signal_audit_20260622/reports/test_results/01_physical_topology_control_signal_gate.json")

    final_report = safe_read("docs/469_final_report.md")
    row0_report = safe_read("analysis/row0_origin_parallel_20260621/reports/final_row0_origin_parallel_report.md")

    dependency_ledger = build_dependency_ledger(minimal, v7, v8, v9, topology)
    source_candidates = build_source_candidates(topology)

    promoted_sources = [c for c in source_candidates if c["classification"] == "PROMOTED_EXTERNAL_CONTROL_SOURCE"]
    weak_sources = [c for c in source_candidates if c["classification"] == "WEAK_PROVENANCE_CLUE"]
    blocked_sources = [c for c in source_candidates if c["classification"] == "BLOCKED_NEEDS_PRIMARY_SOURCE"]

    result = {
        "schema": "authoring_surface_provenance_gate.v1",
        "scope": "analysis_only_authoring_surface_provenance",
        "classification": "internal_generative_route_saturated_without_external_authoring_surface",
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "inputs": {
            "final_report": "docs/469_final_report.md",
            "authorial_mechanism_wiki": "docs/wiki/18-authorial-mechanism-model.md",
            "v9": "analysis/executable_v9_innovation_copy_continuation_audit_20260622/reports/test_results/01_executable_v9_innovation_copy_continuation_gate.json",
            "unified_innovation_payload": "analysis/unified_innovation_payload_audit_20260622/reports/final_unified_innovation_payload_audit.md",
            "physical_topology": "analysis/physical_topology_control_signal_audit_20260622/reports/test_results/01_physical_topology_control_signal_gate.json",
            "row0_parallel": "analysis/row0_origin_parallel_20260621/reports/final_row0_origin_parallel_report.md",
        },
        "web_spotcheck_sources": [
            {
                "url": "https://tibia.fandom.com/wiki/469",
                "finding": "secondary 469 overview; states Hellgate Library books exist and translation claims lack solid proof",
                "source_role": "community context, not primary authoring surface",
            },
            {
                "url": "https://tibia.fandom.com/wiki/9457655996_(Book)",
                "finding": "example community book page lists Hellgate Library location, unknown author, Version 6.2, and raw book text",
                "source_role": "text/location provenance clue, not event/source policy",
            },
            {
                "url": "https://github.com/s2ward/469",
                "finding": "community repository preserves books and alignment/history materials",
                "source_role": "corpus provenance/audit-only",
            },
            {
                "url": "https://www.tibiawiki.com.br/wiki/469",
                "finding": "community theory/lore article with speculative 486/computer/cryptography allusions",
                "source_role": "not promoted; no executable control variable",
            },
        ],
        "summary": {
            "v9_external_bits_total_content_included": v9["summary"]["v9_external_bits_total_content_included"],
            "v9_roundtrip_70_70": v9["validation"]["roundtrip_70_70"],
            "dependency_count": len(dependency_ledger),
            "source_candidate_count": len(source_candidates),
            "promoted_external_control_sources": len(promoted_sources),
            "weak_provenance_clues": len(weak_sources),
            "blocked_primary_source_candidates": len(blocked_sources),
            "partial_topology_promoted_targets": topology["decision"]["promoted_targets"],
            "row0_report_exogenous": "row0_origin_exogenous_under_current_evidence" in row0_report,
            "final_report_external_reopen_only": "external CipSoft-attested ground truth" in final_report,
        },
        "dependency_ledger": dependency_ledger,
        "source_candidates": source_candidates,
        "decision": {
            "external_authoring_surface_exists": False,
            "v9_dependencies_reduced_by_external_source": [],
            "v9_status": "promoted_executable_ledger_not_authorial_formula",
            "generator_route_status": "internal_generative_route_saturated_without_external_authoring_surface",
            "next_action": "freeze internal subcodec route unless primary CipSoft/in-game/map/script provenance appears",
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "01_authoring_surface_provenance_gate.json"
    md_path = OUT_DIR / "01_authoring_surface_provenance_gate.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines: list[str] = []
    lines.append("# Authoring Surface Provenance Gate")
    lines.append("")
    lines.append("Classification: `internal_generative_route_saturated_without_external_authoring_surface`")
    lines.append("Translation delta: `NONE`")
    lines.append("Plaintext claim: `False`")
    lines.append("Case reopened: `False`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"v9 remains an executable ledger with roundtrip `70/70` and "
        f"`{result['summary']['v9_external_bits_total_content_included']:.3f}` content-included bits. "
        "No external authoring surface is promoted."
    )
    lines.append("")
    lines.append(
        "The current public/provenance surfaces either describe the corpus after the fact "
        "or are partial community manifests. They do not reduce the v9 residual fields under controls."
    )
    lines.append("")
    lines.append("## Still-External v9 Dependencies")
    lines.append("")
    lines.append("| Dependency | Status | Bits/Cost Reference | Provenance Gate |")
    lines.append("| --- | --- | ---: | --- |")
    for row in dependency_ledger:
        bits = row["v9_or_recent_bits"]
        bits_s = "" if bits is None else f"{bits:.3f}"
        lines.append(
            f"| `{row['dependency']}` | `{row['current_status']}` | {bits_s} | {row['provenance_gate']} |"
        )
    lines.append("")
    lines.append("## Source Candidate Decisions")
    lines.append("")
    lines.append("| Candidate | Classification | Decoder Field Reduced | Reason |")
    lines.append("| --- | --- | --- | --- |")
    for c in source_candidates:
        reduced = ", ".join(c["decoder_field_reduced"]) if c["decoder_field_reduced"] else "none"
        lines.append(
            f"| `{c['candidate']}` | `{c['classification']}` | {reduced} | {c['contradictions']} |"
        )
    lines.append("")
    lines.append("## Public Source Spotcheck")
    lines.append("")
    lines.append("| URL | Role | Finding |")
    lines.append("| --- | --- | --- |")
    for source in result["web_spotcheck_sources"]:
        lines.append(f"| {source['url']} | {source['source_role']} | {source['finding']} |")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("`internal_generative_route_saturated_without_external_authoring_surface`.")
    lines.append("")
    lines.append(
        "No source qualifies as `PROMOTED_EXTERNAL_CONTROL_SOURCE`. The only live routes are primary "
        "CipSoft/in-game/map/object/script evidence or timestamped historical variants that predict v9 "
        "residual fields above controls."
    )
    lines.append("")
    lines.append("`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.")
    md_path.write_text("\n".join(lines) + "\n")

    final_lines = list(lines)
    final_lines[0] = "# Final Authoring Surface Provenance Audit"
    final_lines.append("")
    final_lines.append("## Reproducible Artifacts")
    final_lines.append("")
    final_lines.append("- [01_authoring_surface_provenance_gate.py](../scripts/01_authoring_surface_provenance_gate.py)")
    final_lines.append("- [01_authoring_surface_provenance_gate.json](test_results/01_authoring_surface_provenance_gate.json)")
    final_lines.append("- [01_authoring_surface_provenance_gate.md](test_results/01_authoring_surface_provenance_gate.md)")
    FINAL_REPORT.write_text("\n".join(final_lines) + "\n")


if __name__ == "__main__":
    main()
