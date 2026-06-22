#!/usr/bin/env python3
"""Compile the final unified control program audit report."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "unified_control_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"
OUT = FRONT / "reports" / "final_unified_control_program_audit.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def fmt_bits(value: float) -> str:
    return f"{value:.3f}"


def main() -> None:
    ledger = load_json(TEST_RESULTS / "01_unified_residual_control_ledger.json")
    tests = load_json(TEST_RESULTS / "02_unified_control_program_tests.json")

    if ledger.get("translation_delta") != "NONE" or tests.get("translation_delta") != "NONE":
        raise SystemExit("Translation delta must remain NONE")
    if ledger.get("case_reopened") or tests.get("case_reopened"):
        raise SystemExit("Audit must not reopen the case")
    if ledger.get("plaintext_claim") or tests.get("plaintext_claim"):
        raise SystemExit("Audit must not make plaintext claims")

    summary = ledger["summary"]
    residual = tests["residual_cost_ledger"]
    coupling = tests["control_tape_coupling_gate"]
    holdout = tests["unified_program_holdout"]["summary"]
    relation_rows = coupling["relations"]

    promoted = coupling["promoted_relations"]
    generator_promoted = holdout["exact_books_without_atlas"] > 0 or holdout["exact_ops_without_atlas"] > 0
    final_classification = (
        "unified_control_program_promoted"
        if generator_promoted
        else "unified_control_program_partial_coupling_not_generator"
        if promoted
        else "unified_control_program_not_promoted"
    )

    lines: list[str] = []
    lines.extend(
        [
            "# Final Unified Control Program Audit",
            "",
            "Status: `analysis_only`",
            f"Classification: `{final_classification}`",
            "Translation delta: `NONE`",
            "Plaintext claim: `False`",
            "Case reopened: `False`",
            "",
            "## Question",
            "",
            "This audit asks whether the residual controls needed to reproduce the 70-book "
            "469 corpus form a small, synchronized, prefix-generalizable control program, "
            "or whether the current explanation is still an operational atlas with better "
            "accounting.",
            "",
            "It does not test plaintext, translation, fan glosses, semantics, or row0 origin. "
            "Row0 remains exogenous, and the compression bound remains separate from "
            "generation explanation.",
            "",
            "## Inputs",
            "",
            "- Recent latent-transducer gates: copy-state rescue, copy-candidate ranking, "
            "copy-hint lower bound, and copy-hint stream structure.",
            "- Canonical derived-book operation skeleton used by the recent generation "
            "fronts.",
            "- Best known copy-hint lower-bound policy from the copy-hint stream audit.",
            "",
            "## Unified Residual Ledger",
            "",
            f"- Books covered: `{summary['books']}` derived books.",
            f"- Operations: `{summary['ops']}` total, `{summary['copy_ops']}` copies, "
            f"`{summary['literal_ops']}` literal runs.",
            f"- Copied digits: `{summary['copy_digits']}`.",
            f"- Literal innovation tape: `{summary['literal_digits']}` digits, "
            f"`{fmt_bits(summary['literal_payload_bits'])}` raw uniform bits.",
            f"- Target starts derived from prior lengths: `{summary['target_start_derived_ops']}/{summary['ops']}`.",
            f"- Source-address cost: `{fmt_bits(summary['source_address_bits'])}` bits.",
            f"- Same-length chunk hint cost: `{fmt_bits(summary['same_length_chunk_hint_bits'])}` bits.",
            f"- Best known copy-hint rank cost: `{fmt_bits(summary['copy_hint_rank_bits'])}` bits.",
            f"- Unique `type:length` control symbols: `{summary['unique_type_length_symbols']}`.",
            "",
            "The ledger makes the residual explicit: starts are downstream of the length "
            "sequence, but op type, length, literal innovation, copy hint rank, seed payload, "
            "and row0 are still declared or paid streams.",
            "",
            "## Residual Cost Ledger",
            "",
            "| Model | Bits | Interpretation |",
            "| --- | ---: | --- |",
            f"| start/type/length/literal/source separated | `{fmt_bits(residual['cost_models']['start_type_length_literal_source_separated'])}` | operational source-address declaration |",
            f"| start/type/length/literal/copy-hint | `{fmt_bits(residual['cost_models']['start_type_length_literal_copy_hint'])}` | source replaced by same-length copy hint |",
            f"| innovation tape + copy-hint + joint `type:length` stream | `{fmt_bits(residual['cost_models']['innovation_tape_copy_hint_type_length_stream'])}` | best organized residual stream model |",
            f"| innovation tape + copy-hint + separate control streams | `{fmt_bits(residual['cost_models']['innovation_tape_copy_hint_separate_control_streams'])}` | organized residual without joint type:length |",
            "",
            f"The best organized residual model is `{fmt_bits(residual['reductions']['best_unified_vs_separated_source_bits'])}` "
            "bits below independent source-address declaration on the full ledger. This is "
            "a lower-bound/accounting improvement, not a generator, because it still pays "
            "the residual streams.",
            "",
            "## Control-Tape Coupling Gate",
            "",
            f"Promoted relations: `{promoted}`.",
            "",
            "| Relation | Rows | Saving | Random p95 | Status |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )

    for name in sorted(relation_rows):
        row = relation_rows[name]
        lines.append(
            f"| `{name}` | `{row['rows']}` | `{fmt_bits(row['observed_total_saving_bits'])}` | "
            f"`{fmt_bits(row['random_saving_p95'])}` | `{row['status']}` |"
        )

    lines.extend(
        [
            "",
            "Only `previous_op_to_next_control_symbol` is promoted as a non-tautological "
            "coupling clue. The literal-consumption and joint type:length relations are "
            "kept audit-only because their features leak the field being explained. "
            "Length-bucket and book-phase effects beat weak controls but remain below the "
            "effect-size gate.",
            "",
            "## Unified Program Holdout",
            "",
            f"- Total independent-source test bits across cutoffs: `{fmt_bits(holdout['total_independent_source_bits'])}`.",
            f"- Total best unified test bits across cutoffs: `{fmt_bits(holdout['total_best_unified_bits'])}`.",
            f"- Reduction vs independent source: `{fmt_bits(holdout['total_reduction_vs_independent_source_bits'])}` bits.",
            f"- Exact books without atlas: `{holdout['exact_books_without_atlas']}`.",
            f"- Exact ops without atlas: `{holdout['exact_ops_without_atlas']}`.",
            f"- Fields still external: `{holdout['fields_still_external']}`.",
            "",
            "The holdout result shows that organized residual streams compress the remaining "
            "controls better than independent source-address declaration, but no book or "
            "operation is generated exactly without the atlas/control streams.",
            "",
            "## Decision",
            "",
            f"- Final classification: `{final_classification}`.",
            "- `row0` unchanged: still exogenous under current evidence.",
            "- `compression_bound` unchanged: this audit organizes residual generation fields "
            "and does not claim a new compression bound.",
            "- Generative status: partial synchronization clue, not a promoted unified control "
            "program.",
            "- Current explanation: strong mechanical parser/compressor with explicit residual "
            "streams; not a complete authorial generator.",
            "",
            "## Remaining External Fields",
            "",
            "- `type_length_control_stream`",
            "- `literal_innovation_tape`",
            "- `copy_hint_rank_stream`",
            "- `seed_books_0_9`",
            "- `row0`",
            "",
            "## Next Blocker",
            "",
            "The next real blocker is not another local source/rank selector. It is a "
            "target-free rule that generates the `type:length` control stream, the literal "
            "innovation tape schedule/payload, and copy-hint ranks jointly enough to reduce "
            "declared fields under prefix/holdout. Without that, the route remains an "
            "organized residual ledger rather than a compact generation formula.",
            "",
            "## Reproducible Artifacts",
            "",
            "- [01_unified_residual_control_ledger.py](../scripts/01_unified_residual_control_ledger.py)",
            "- [01_unified_residual_control_ledger.json](test_results/01_unified_residual_control_ledger.json)",
            "- [01_unified_residual_control_ledger.md](test_results/01_unified_residual_control_ledger.md)",
            "- [02_unified_control_program_tests.py](../scripts/02_unified_control_program_tests.py)",
            "- [02_unified_control_program_tests.json](test_results/02_unified_control_program_tests.json)",
            "- [02_unified_control_program_tests.md](test_results/02_unified_control_program_tests.md)",
            "- [03_compile_final_unified_control_program_audit.py](../scripts/03_compile_final_unified_control_program_audit.py)",
        ]
    )

    OUT.write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "classification": final_classification,
                "promoted_relations": promoted,
                "exact_books_without_atlas": holdout["exact_books_without_atlas"],
                "exact_ops_without_atlas": holdout["exact_ops_without_atlas"],
                "fields_still_external": holdout["fields_still_external"],
                "report": str(OUT.relative_to(ROOT)),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
