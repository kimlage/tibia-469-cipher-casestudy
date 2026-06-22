#!/usr/bin/env python3
"""Compile the final composition-index structure audit report."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "composition_index_structure_audit_20260622"
RESULT_PATH = FRONT / "reports" / "test_results" / "01_composition_index_structure_gate.json"
FINAL_OUT = FRONT / "reports" / "final_composition_index_structure_audit.md"


def main() -> None:
    result = json.loads(RESULT_PATH.read_text())
    best_key = result["decision"]["best_model"]
    best = result["model_results"][best_key]
    dist = result["distribution_summary"]
    lines = [
        "# Final Composition Index Structure Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "The previous book-level coarse length controller reduced exact fine "
        "length residuals to a book-level composition index once the coarse "
        "`type:length_bucket` sequence and `book_length` are known. This audit "
        "tests whether the exact index position has reusable structure, or "
        "whether it remains an external field.",
        "",
        "This does not reopen row0, plaintext, translation, semantics, or fan "
        "glosses, and it does not alter the compression bound.",
        "",
        "## Evidence",
        "",
        f"- Nontrivial composition books: `{dist['nontrivial_books']}`.",
        f"- Edge ranks among nontrivial books: `{dist['edge_books']}`.",
        f"- Low-half ranks among nontrivial books: `{dist['low_half_books']}`.",
        f"- Best model: `{best_key}`.",
        f"- Best model classification: `{best['classification']}`.",
        f"- Repeated-holdout uniform composition-index bits: `{best['totals']['uniform_bits']:.3f}`.",
        f"- Repeated-holdout model bits: `{best['totals']['model_bits']:.3f}`.",
        f"- Saving: `{best['totals']['saving_bits']:.3f}` bits.",
        f"- Nontrivial saving: `{best['totals']['nontrivial_saving_bits']:.3f}` bits.",
        f"- Random-rank saving mean: `{best['random_saving_mean']:.3f}` bits.",
        f"- Random-rank saving p95: `{best['random_saving_p95']:.3f}` bits.",
        "",
        "## Decision",
        "",
    ]
    if result["classification"] == "PROMOTED_COMPOSITION_INDEX_STRUCTURE":
        lines.append(
            "A composition-index structure model is promoted: the exact rank can "
            "be coded below uniform composition indexing in prefix/holdout and "
            "clears random-rank controls. This reduces one remaining declared "
            "field, but does not create a complete generator."
        )
    elif result["classification"] == "WEAK_COMPOSITION_INDEX_CLUE":
        lines.append(
            "The rank stream shows a weak clue, but it does not clear the "
            "promotion gate against random-rank controls. The composition index "
            "therefore remains external payload, with only a weak bias noted."
        )
    else:
        lines.append(
            "The composition-index route is not promoted. Book-length constrained "
            "composition remains a valid structural codec, but the exact index "
            "inside that composition still has to be declared under current "
            "evidence."
        )
    lines.extend(
        [
            "",
            "## Impact On The Generative Search",
            "",
            "- `row0` remains exogenous and unchanged.",
            "- Translation/plaintext/semantic status remains unchanged.",
            "- `compression_bound` remains separate and unchanged.",
            "- The book-level controller remains the strongest current coarse "
            "generation candidate, but exact residual composition index payload "
            "is not removed unless the promotion gate above passes.",
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
            "- [01_composition_index_structure_gate.py](../scripts/01_composition_index_structure_gate.py)",
            "- [01_composition_index_structure_gate.json](test_results/01_composition_index_structure_gate.json)",
            "- [01_composition_index_structure_gate.md](test_results/01_composition_index_structure_gate.md)",
            "- [02_compile_final_composition_index_structure_audit.py](../scripts/02_compile_final_composition_index_structure_audit.py)",
        ]
    )
    FINAL_OUT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
