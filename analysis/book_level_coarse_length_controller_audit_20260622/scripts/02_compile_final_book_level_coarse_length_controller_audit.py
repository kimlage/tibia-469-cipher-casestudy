#!/usr/bin/env python3
"""Compile final report for the book-level coarse length controller audit."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "book_level_coarse_length_controller_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"
RESULT_PATH = TEST_RESULTS / "01_book_level_coarse_length_controller_gate.json"
OUT = FRONT / "reports" / "final_book_level_coarse_length_controller_audit.md"


def bits(value: float) -> str:
    return f"{value:.3f}"


def main() -> None:
    result = json.loads(RESULT_PATH.read_text())
    if result.get("translation_delta") != "NONE":
        raise SystemExit("translation delta must remain NONE")
    if result.get("case_reopened") or result.get("plaintext_claim"):
        raise SystemExit("audit must not reopen case or make plaintext claims")

    residual = result["residual_composition"]["summary"]
    best_key = result["decision"]["best_pair"]
    best = result["pair_results"][best_key]
    integrated = result["integrated_cost"]["summary"]

    lines = [
        "# Final Book-Level Coarse Length Controller Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "This audit integrates the recent length/control factorization at book level: "
        "known `book_length`, latent `op_count`, coarse `type:length_bucket` sequence, "
        "and within-bucket residual lengths represented as a composition constrained "
        "by the book length.",
        "",
        "No target text, plaintext, semantics, fan glosses, row0 origin, or exact "
        "residuals are used to choose the coarse sequence.",
        "",
        "## Residual Composition",
        "",
        f"- Books: `{residual['books']}` (`{residual['trivial_books']}` trivial, `{residual['nontrivial_books']}` nontrivial).",
        f"- Independent residual bits: `{bits(residual['total_uniform_bits'])}`.",
        f"- Composition-index bits: `{bits(residual['total_composition_bits'])}`.",
        f"- Saving: `{bits(residual['saving_bits'])}` bits.",
        f"- Classification: `{result['residual_composition']['classification']}`.",
        "",
        "Given the true coarse sequence and `book_length`, exact residual lengths can "
        "be represented by a book-level composition index. This promotes a residual "
        "composition codec: the fine residual field is reduced structurally, though "
        "not freely generated.",
        "",
        "## Latent Op-Count Coarse Beam",
        "",
        f"- Best model pair: `{best_key}`.",
        f"- Pair classification: `{best['classification']}`.",
        f"- Exact op_count in beam: `{best['totals']['exact_opcount_in_beam']}/{best['totals']['test_books']}`.",
        f"- Exact coarse sequence in beam: `{best['totals']['exact_sequence_in_beam']}/{best['totals']['test_books']}`.",
        f"- Nontrivial exact coarse sequences: `{best['totals']['nontrivial_exact_sequence_in_beam']}`.",
        f"- Same-multiset shuffled exact-sequence p95: `{best['random_exact_sequence_p95']}`.",
        f"- Promoted pairs: `{result['decision']['promoted_pairs']}`.",
        "",
        "The true coarse sequence survives in beam above same-multiset controls after "
        "`op_count` is made latent. This does not make top-1 generation exact, but it "
        "does reduce the status of op_count/coarse sequence from pure atlas to a "
        "book-level controller candidate with corrections.",
        "",
        "## Integrated Cost",
        "",
        "| Model | Bits |",
        "| --- | ---: |",
        f"| op_count + coarse sequence separated, uniform residual | `{bits(integrated['opcount_coarse_separated_uniform_residual'])}` |",
        f"| op_count granted coarse model + residual composition index | `{bits(integrated['opcount_granted_coarse_model_plus_composition'])}` |",
        f"| latent op_count beam + residual composition/corrections | `{bits(integrated['latent_beam_plus_composition'])}` |",
        "",
        "The latent book-level controller improves substantially over separated "
        "op_count/coarse/residual declaration, but remains worse than the version that "
        "still grants true op_count to the coarse controller. The gap is the current "
        "book-level correction ledger.",
        "",
        "## Decision",
        "",
        "- `PROMOTED_BOOK_LEVEL_CONTROLLER_CANDIDATE`.",
        "- `op_count` is no longer treated as simply conceded: the latent beam recovers "
        "true op_count in most held-out books and keeps exact coarse sequences above "
        "same-multiset controls.",
        "- The fine length residual is reduced to a book-level composition index when "
        "the coarse sequence is known or corrected.",
        "- This is closer to a gerative mechanism, but not a complete generator: top-1 "
        "books are not exact, and correction payload remains.",
        "- `row0`, translation, plaintext, and the compression bound remain unchanged.",
        "",
        "## Remaining External Fields",
        "",
        "- coarse sequence corrections when the true sequence misses beam",
        "- book-level composition index for exact residual lengths",
        "- literal innovation tape payload and schedule",
        "- copy-hint rank stream",
        "- seed books `0..9`",
        "- `row0`",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_book_level_coarse_length_controller_gate.py](../scripts/01_book_level_coarse_length_controller_gate.py)",
        "- [01_book_level_coarse_length_controller_gate.json](test_results/01_book_level_coarse_length_controller_gate.json)",
        "- [01_book_level_coarse_length_controller_gate.md](test_results/01_book_level_coarse_length_controller_gate.md)",
        "- [02_compile_final_book_level_coarse_length_controller_audit.py](../scripts/02_compile_final_book_level_coarse_length_controller_audit.py)",
    ]
    OUT.write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "best_pair": best_key,
                "classification": result["classification"],
                "exact_sequence_in_beam": best["totals"]["exact_sequence_in_beam"],
                "residual_saving_bits": residual["saving_bits"],
                "report": str(OUT.relative_to(ROOT)),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
