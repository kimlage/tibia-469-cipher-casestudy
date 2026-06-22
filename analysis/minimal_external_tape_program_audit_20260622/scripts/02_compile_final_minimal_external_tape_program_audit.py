#!/usr/bin/env python3
"""Compile final report for the minimal external tape program audit."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "minimal_external_tape_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"
CONTRACT = TEST_RESULTS / "01_executable_decoder_contract.json"
LEDGER = TEST_RESULTS / "02_unified_external_tape_ledger.json"
GATE = TEST_RESULTS / "03_macro_program_gate.json"
FINAL_OUT = FRONT / "reports" / "final_minimal_external_tape_program_audit.md"


def main() -> None:
    contract = json.loads(CONTRACT.read_text())
    ledger = json.loads(LEDGER.read_text())
    gate = json.loads(GATE.read_text())
    validation = contract["validation"]
    ledger_summary = ledger["summary"]
    gate_summary = gate["summary"]
    controls = gate["controls"]
    lines = [
        "# Final Minimal External Tape Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{gate['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can the current 469 book-generation residual be represented as a small "
        "executable control program plus unified external tapes, and can a macro "
        "grammar over that IR reduce the external ledger after paying grammar and "
        "corrections?",
        "",
        "This audit does not reopen row0, plaintext, translation, semantics, or fan "
        "glosses. `compression_bound` remains separate from `generation_explanation`.",
        "",
        "## Executable Decoder Contract",
        "",
        f"- Roundtrip: `{validation['exact_books']}/70` books.",
        f"- Derived operation count: `{validation['operation_count']}`.",
        f"- Seed books paid externally: `{validation['seed_books']}`.",
        f"- Emitted digit stream: `{validation['stream_digits']}` digits.",
        "- Derived fields include target starts and emitted book text from literal/copy execution.",
        "- Target-conditioned fields remain explicit: literal payload, copy hints, and composition index.",
        "",
        "## Unified External Tape Ledger",
        "",
        f"- Derived books: `{ledger_summary['books']}`.",
        f"- Operations: `{ledger_summary['ops']}` (`{ledger_summary['literal_ops']}` literal, `{ledger_summary['copy_ops']}` copy).",
        f"- Seed payload: `{ledger_summary['seed_payload_bits']:.3f}` bits.",
        f"- Uniform coarse control: `{ledger_summary['coarse_control_bits_uniform']:.3f}` bits.",
        f"- Composition index: `{ledger_summary['composition_index_bits']:.3f}` bits.",
        f"- Literal payload: `{ledger_summary['literal_payload_bits']:.3f}` bits.",
        f"- Copy-hint rank: `{ledger_summary['copy_hint_rank_bits']:.3f}` bits.",
        f"- Total external tapes including seed: `{ledger_summary['total_external_tape_bits_including_seed']:.3f}` bits.",
        "",
        "## Macro Program Gate",
        "",
        f"- Classification: `{gate['classification']}`.",
        f"- Program reduction vs separated coarse+composition ledger: `{gate_summary['program_reduction_vs_separated_control_plus_composition_bits']:.3f}` bits.",
        f"- Macro saving before composition carry-through: `{gate_summary['macro_saving_bits']:.3f}` bits.",
        f"- Template saving before composition carry-through: `{gate_summary['template_saving_bits']:.3f}` bits.",
        f"- Coupling bucket-stream saving: `{gate_summary['coupling_saving_bits']:.3f}` bits.",
        f"- Exact books without sequence atlas/terminals: `{gate_summary['total_exact_books_without_atlas_or_terminals']}`.",
        f"- Nontrivial exact books without sequence atlas/terminals: `{gate_summary['total_nontrivial_exact_books_without_atlas_or_terminals']}`.",
        f"- Exact ops without sequence atlas/terminals: `{gate_summary['total_exact_ops_without_atlas_or_terminals']}`.",
        f"- Same-multiset shuffled p95: `{controls['same_multiset_shuffled_reduction_p95']:.3f}` bits.",
        f"- Permuted-order p95: `{controls['permuted_order_reduction_p95']:.3f}` bits.",
        "",
        "## Decision",
        "",
    ]
    if gate["classification"] == "PROMOTED_MINIMAL_EXTERNAL_TAPE_PROGRAM":
        lines.append(
            "The unified program is promoted: it reduces the paid external ledger or "
            "generates nontrivial held-out structure above controls. It is still not "
            "a translation or row0-origin result."
        )
    else:
        lines.append(
            "`minimal_external_tape_program_not_promoted`. The decoder contract is "
            "now executable and the external ledger is unified, but the tested "
            "macro/template grammar increases cost after grammar/correction charges. "
            "This organizes the blocker; it does not yet reduce the external tapes."
        )
    lines.extend(
        [
            "",
            "## Remaining External Fields",
            "",
            "- seed books `0..9`",
            "- coarse control stream when macro/template program misses",
            "- book-level composition index",
            "- literal innovation payload tape",
            "- copy hint rank/source tape",
            "- correction tape for macro/template misses",
            "- `row0`",
            "",
            "## Reproducible Artifacts",
            "",
            "- [01_minimal_external_tape_program_gate.py](../scripts/01_minimal_external_tape_program_gate.py)",
            "- [01_executable_decoder_contract.json](test_results/01_executable_decoder_contract.json)",
            "- [01_executable_decoder_contract.md](test_results/01_executable_decoder_contract.md)",
            "- [02_unified_external_tape_ledger.json](test_results/02_unified_external_tape_ledger.json)",
            "- [02_unified_external_tape_ledger.md](test_results/02_unified_external_tape_ledger.md)",
            "- [03_macro_program_gate.json](test_results/03_macro_program_gate.json)",
            "- [03_macro_program_gate.md](test_results/03_macro_program_gate.md)",
            "- [02_compile_final_minimal_external_tape_program_audit.py](../scripts/02_compile_final_minimal_external_tape_program_audit.py)",
        ]
    )
    FINAL_OUT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
