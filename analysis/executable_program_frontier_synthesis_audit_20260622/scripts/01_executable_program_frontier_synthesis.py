#!/usr/bin/env python3
"""Executable program frontier synthesis audit.

This is a consolidation gate, not another local residual-field search. It reads
the current executable decoder contract and the recent integration/removal
gates, then records which external tapes have actually been reduced inside the
decoder and which remain external.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "executable_program_frontier_synthesis_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

CONTRACT = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_decoder_contract.json"
)
LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
MACRO_GATE = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "03_macro_program_gate.json"
)
SOURCE_GATE = (
    ROOT
    / "analysis"
    / "source_tape_removal_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_source_tape_removal_program_gate.json"
)
BOOK_CONTROLLER_GATE = (
    ROOT
    / "analysis"
    / "book_level_controller_program_integration_audit_20260622"
    / "reports"
    / "test_results"
    / "01_book_level_controller_program_integration_gate.json"
)
COMPOSITION_GATE = (
    ROOT
    / "analysis"
    / "composition_index_structure_audit_20260622"
    / "reports"
    / "test_results"
    / "01_composition_index_structure_gate.json"
)
SHARED_TAPE_GATE = (
    ROOT
    / "analysis"
    / "shared_innovation_tape_audit_20260622"
    / "reports"
    / "test_results"
    / "01_shared_literal_length_tape_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_executable_program_frontier_synthesis.json"
MD_OUT = TEST_RESULTS / "01_executable_program_frontier_synthesis.md"
FINAL_OUT = FRONT / "reports" / "final_executable_program_frontier_synthesis_audit.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def maybe_json(path: Path) -> Any | None:
    return load_json(path) if path.exists() else None


def frontier_rows() -> dict:
    contract = load_json(CONTRACT)
    ledger = load_json(LEDGER)
    macro = load_json(MACRO_GATE)
    source = load_json(SOURCE_GATE)
    controller = load_json(BOOK_CONTROLLER_GATE)
    composition = load_json(COMPOSITION_GATE)
    shared = maybe_json(SHARED_TAPE_GATE)

    ledger_summary = ledger["summary"]
    macro_summary = macro["summary"]
    source_best = source["policy_results"][source["decision"]["best_policy"]]
    source_totals = source_best["totals"]
    controller_summary = controller["summary"]
    composition_best = composition["model_results"][composition["decision"]["best_model"]]

    rows = [
        {
            "external_tape": "seed_books_0_9",
            "baseline_bits": ledger_summary["seed_payload_bits"],
            "best_executable_attempt": "seed_primacy_audit_prior",
            "best_attempt_delta_bits": None,
            "classification": "EXTERNAL_RETAINED",
            "evidence": "seed payload is required by current executable contract; prior seed-primacy controls did not promote books 0..9 as special authorial seeds",
            "next_blocker": "needs external authorial/source evidence or a new generator that reduces seed payload without posthoc seed selection",
        },
        {
            "external_tape": "coarse_control_plus_composition_index",
            "baseline_bits": ledger_summary["coarse_control_bits_uniform"] + ledger_summary["composition_index_bits"],
            "best_executable_attempt": "book_level_controller_program_integration",
            "best_attempt_delta_bits": controller_summary["saving_bits"],
            "classification": "EXECUTABLE_REDUCTION_REJECTED",
            "evidence": (
                f"controller+corrections {controller_summary['controller_bits']:.3f} vs baseline "
                f"{controller_summary['baseline_bits']:.3f}; true sequence in beam "
                f"{controller_summary['sequence_in_beam']}/{controller_summary['test_books']}; "
                f"top1 nontrivial exact books {controller_summary.get('top1_nontrivial_exact_books', 0)}"
            ),
            "next_blocker": "requires a different coarse/length representation, not another local beam-rank codec",
        },
        {
            "external_tape": "copy_source_hint",
            "baseline_bits": ledger_summary["copy_hint_rank_bits"],
            "best_executable_attempt": "decoder_visible_source_tape_removal",
            "best_attempt_delta_bits": source_totals["saving_vs_copy_hint_bits"],
            "classification": "EXECUTABLE_REDUCTION_REJECTED",
            "evidence": (
                f"default hits {source_totals.get('default_copy_hits', 0)}/{source_totals.get('test_copy_ops', 0)}, "
                f"policy+exception {source_totals['policy_bits']:.3f} vs copy-hint baseline "
                f"{source_totals['baseline_copy_hint_bits']:.3f}"
            ),
            "next_blocker": "source remains target-chunk dependent unless a joint chunk-origin generator is found",
        },
        {
            "external_tape": "literal_payload",
            "baseline_bits": ledger_summary["literal_payload_bits"],
            "best_executable_attempt": "innovation_stream_transducer_prior",
            "best_attempt_delta_bits": None,
            "classification": "WEAK_CLUE_NOT_EXECUTABLE_REDUCTION",
            "evidence": (
                "literal tape has prior structure clues, but paid tape subcodecs and closed-loop generation were not promoted"
            ),
            "next_blocker": "needs integration with operation/chunk generation, not a standalone literal-payload codec",
        },
        {
            "external_tape": "macro_template_program",
            "baseline_bits": ledger_summary["coarse_control_bits_uniform"] + ledger_summary["composition_index_bits"],
            "best_executable_attempt": "minimal_external_tape_macro_program",
            "best_attempt_delta_bits": macro_summary["program_reduction_vs_separated_control_plus_composition_bits"],
            "classification": "EXECUTABLE_MACRO_PROGRAM_REJECTED",
            "evidence": (
                f"macro/template program reduction {macro_summary['program_reduction_vs_separated_control_plus_composition_bits']:.3f}; "
                f"nontrivial exact books {macro_summary['total_nontrivial_exact_books_without_atlas_or_terminals']}"
            ),
            "next_blocker": "macro grammar over current IR is too expensive; representation needs to change",
        },
        {
            "external_tape": "composition_index_rank_structure",
            "baseline_bits": ledger_summary["composition_index_bits"],
            "best_executable_attempt": "composition_index_structure_audit",
            "best_attempt_delta_bits": composition_best["totals"]["saving_bits"],
            "classification": "FIELD_STRUCTURE_REJECTED",
            "evidence": (
                f"best rank model saving {composition_best['totals']['saving_bits']:.3f} vs random p95 "
                f"{composition_best['random_saving_p95']:.3f}"
            ),
            "next_blocker": "composition index remains payload until tied to a different book-level generator",
        },
    ]

    if shared:
        rows.append(
            {
                "external_tape": "shared_literal_length_tape",
                "baseline_bits": None,
                "best_executable_attempt": "shared_innovation_tape_audit",
                "best_attempt_delta_bits": shared.get("summary", {}).get("saving_bits"),
                "classification": "WEAK_CLUE_NOT_EXECUTABLE_REDUCTION",
                "evidence": "shared literal/length tape clue did not beat direct residual declaration",
                "next_blocker": "only useful if a joint program consumes one innovation stream across operation and literal choices",
            }
        )

    executable_reductions = [
        row for row in rows
        if row["classification"].startswith("PROMOTED") or row["classification"] == "EXECUTABLE_REDUCTION_PROMOTED"
    ]
    rejected_executable = [
        row for row in rows
        if row["classification"].startswith("EXECUTABLE") and "REJECTED" in row["classification"]
    ]

    return {
        "case_reopened": False,
        "classification": "executable_program_frontier_requires_representation_change",
        "compression_bound_status": "unchanged",
        "decision": {
            "current_executable_contract_roundtrip": contract["validation"]["roundtrip_70_70"],
            "promoted_executable_tape_reductions": len(executable_reductions),
            "rejected_executable_program_routes": len(rejected_executable),
            "row0_status": "unchanged_exogenous",
            "next_route": "joint_chunk_origin_or_new_representation_required",
        },
        "inputs": {
            "book_controller_gate": rel(BOOK_CONTROLLER_GATE),
            "composition_gate": rel(COMPOSITION_GATE),
            "contract": rel(CONTRACT),
            "ledger": rel(LEDGER),
            "macro_gate": rel(MACRO_GATE),
            "source_gate": rel(SOURCE_GATE),
        },
        "plaintext_claim": False,
        "rows": rows,
        "scope": "analysis_only_executable_program_frontier_synthesis",
        "summary": {
            "external_bits_excluding_seed": ledger_summary["total_external_tape_bits_excluding_seed"],
            "external_bits_including_seed": ledger_summary["total_external_tape_bits_including_seed"],
            "promoted_executable_tape_reductions": len(executable_reductions),
            "rejected_executable_program_routes": len(rejected_executable),
            "roundtrip_70_70": contract["validation"]["roundtrip_70_70"],
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict) -> None:
    s = result["summary"]
    lines = [
        "# Executable Program Frontier Synthesis",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Consolidate the executable decoder contract and recent integration/removal "
        "gates. This is a frontier decision: whether the current external tapes have "
        "a promoted reduction path, or whether the representation itself needs to change.",
        "",
        "## Summary",
        "",
        f"- Executable contract roundtrip: `{s['roundtrip_70_70']}`.",
        f"- External bits excluding seed: `{s['external_bits_excluding_seed']:.3f}`.",
        f"- External bits including seed: `{s['external_bits_including_seed']:.3f}`.",
        f"- Promoted executable tape reductions: `{s['promoted_executable_tape_reductions']}`.",
        f"- Rejected executable program routes: `{s['rejected_executable_program_routes']}`.",
        "",
        "| External Tape / Route | Baseline Bits | Best Attempt | Delta Bits | Classification |",
        "| --- | ---: | --- | ---: | --- |",
    ]
    for row in result["rows"]:
        baseline = "" if row["baseline_bits"] is None else f"`{row['baseline_bits']:.3f}`"
        delta = "" if row["best_attempt_delta_bits"] is None else f"`{row['best_attempt_delta_bits']:.3f}`"
        lines.append(
            f"| `{row['external_tape']}` | {baseline} | `{row['best_executable_attempt']}` | "
            f"{delta} | `{row['classification']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "No current tape reducer has promoted inside the executable decoder. The "
            "current program is a valid roundtrip contract, but not a generative "
            "formula: source, coarse/length, literal, composition, and seed payloads "
            "remain external. The next aligned route is not another local tape codec; "
            "it must change representation, most likely toward a joint chunk-origin "
            "program that explains operation chunks, source choice, and innovation "
            "together.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict) -> None:
    s = result["summary"]
    lines = [
        "# Final Executable Program Frontier Synthesis Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "After testing the executable decoder contract, source-tape removal, and "
        "book-level controller integration, is there still a promoted path that "
        "reduces the current external tapes, or has this representation hit a frontier?",
        "",
        "## Evidence",
        "",
        f"- Executable roundtrip remains valid: `{s['roundtrip_70_70']}`.",
        f"- External tape cost: `{s['external_bits_excluding_seed']:.3f}` bits excluding seed, `{s['external_bits_including_seed']:.3f}` including seed.",
        f"- Promoted executable tape reductions: `{s['promoted_executable_tape_reductions']}`.",
        f"- Rejected executable program routes: `{s['rejected_executable_program_routes']}`.",
        "- Source tape removal: not promoted.",
        "- Book-level controller integration: not promoted.",
        "- Macro/template program over the current IR: not promoted.",
        "",
        "## Decision",
        "",
        "The current executable tape representation has reached a practical frontier. "
        "The decoder contract is useful because it makes every dependency explicit "
        "and roundtrips `70/70`, but none of the current positive clues reduces the "
        "external ledger when integrated into that decoder. The next real route "
        "needs a representation change, not another isolated field audit.",
        "",
        "## Remaining External Fields",
        "",
        "- seed books `0..9`",
        "- coarse control / exact length representation",
        "- composition index",
        "- literal innovation payload",
        "- copy source/hint",
        "- `row0`",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_executable_program_frontier_synthesis.py](../scripts/01_executable_program_frontier_synthesis.py)",
        "- [01_executable_program_frontier_synthesis.json](test_results/01_executable_program_frontier_synthesis.json)",
        "- [01_executable_program_frontier_synthesis.md](test_results/01_executable_program_frontier_synthesis.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = frontier_rows()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
