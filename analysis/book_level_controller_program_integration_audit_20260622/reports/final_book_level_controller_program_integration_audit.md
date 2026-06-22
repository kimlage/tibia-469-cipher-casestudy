# Final Book-Level Controller Program Integration Audit

Status: `analysis_only`
Classification: `book_level_controller_program_integration_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can the already-promoted book-level coarse controller reduce an actual external tape in the executable decoder contract?

## Evidence

- Frozen pair: `book_length__op_count`.
- Baseline coarse+composition bits over prefix/family splits: `3824.176`.
- Controller+correction bits: `4069.056`.
- Saving: `-244.881` bits.
- True sequence in beam: `66/186`.
- Nontrivial beam hits: `16`.
- Top-1 exact books: `38`.
- Top-1 nontrivial exact books: `0`.
- Top-1 exact ops: `38`.
- Model/grammar descriptor cost charged here: `0.000` bits, so the negative result is a generous lower bound.
- Same-multiset shuffled p95: `7.170` bits.
- Random trainset p95: `-13.320` bits.

## Decision

The integration is not promoted. The previous controller remains a candidate clue, but it does not reduce the executable ledger under this charged integration.

## Reproducible Artifacts

- [01_book_level_controller_program_integration_gate.py](../scripts/01_book_level_controller_program_integration_gate.py)
- [01_book_level_controller_program_integration_gate.json](test_results/01_book_level_controller_program_integration_gate.json)
- [01_book_level_controller_program_integration_gate.md](test_results/01_book_level_controller_program_integration_gate.md)
