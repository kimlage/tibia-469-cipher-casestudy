# Final Composition Index Structure Audit

Status: `analysis_only`
Classification: `COMPOSITION_INDEX_REMAINS_EXTERNAL`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

The previous book-level coarse length controller reduced exact fine length residuals to a book-level composition index once the coarse `type:length_bucket` sequence and `book_length` are known. This audit tests whether the exact index position has reusable structure, or whether it remains an external field.

This does not reopen row0, plaintext, translation, semantics, or fan glosses, and it does not alter the compression bound.

## Evidence

- Nontrivial composition books: `48`.
- Edge ranks among nontrivial books: `2`.
- Low-half ranks among nontrivial books: `24`.
- Best model: `count_x_length__quantile10`.
- Best model classification: `COMPOSITION_INDEX_REMAINS_EXTERNAL`.
- Repeated-holdout uniform composition-index bits: `1198.420`.
- Repeated-holdout model bits: `1211.748`.
- Saving: `-13.327` bits.
- Nontrivial saving: `-13.327` bits.
- Random-rank saving mean: `-24.843` bits.
- Random-rank saving p95: `-13.273` bits.

## Decision

The composition-index route is not promoted. Book-length constrained composition remains a valid structural codec, but the exact index inside that composition still has to be declared under current evidence.

## Impact On The Generative Search

- `row0` remains exogenous and unchanged.
- Translation/plaintext/semantic status remains unchanged.
- `compression_bound` remains separate and unchanged.
- The book-level controller remains the strongest current coarse generation candidate, but exact residual composition index payload is not removed unless the promotion gate above passes.

## Remaining External Fields

- coarse sequence corrections when the true sequence misses beam
- book-level composition index for exact residual lengths
- literal innovation tape payload and schedule
- copy-hint rank stream
- seed books `0..9`
- `row0`

## Reproducible Artifacts

- [01_composition_index_structure_gate.py](../scripts/01_composition_index_structure_gate.py)
- [01_composition_index_structure_gate.json](test_results/01_composition_index_structure_gate.json)
- [01_composition_index_structure_gate.md](test_results/01_composition_index_structure_gate.md)
- [02_compile_final_composition_index_structure_audit.py](../scripts/02_compile_final_composition_index_structure_audit.py)
