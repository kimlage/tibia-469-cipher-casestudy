# Final Book-Opcount Start-Anchor Program Audit

Status: `analysis_only`
Classification: `WEAK_BOOK_OPCOUNT_START_ANCHOR_CLUE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tested whether the decoded book-level `op_count` can activate start-only source-boundary anchors on top of executable v4. The best small rule is `op_count_le_3`: enable the start-anchor extension only for books with at most three operations.

Full-fit cost improves by `-25.957` bits before declaration and `-21.957` bits after charging `4.000` bits for the `16`-rule family. Fixed `op_count_le_3` improves `4/5` suffix splits with aggregate delta `-60.727` bits.

However, the random op-count control is not cleared: observed best saving is `25.957` bits versus random p95 `29.826`.

## Decision

`WEAK_BOOK_OPCOUNT_START_ANCHOR_CLUE`. The signal is useful for the residual ledger, but it is not strong enough to replace v4 as the promoted executable program.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_book_opcount_start_anchor_program_gate.py](../scripts/01_book_opcount_start_anchor_program_gate.py)
- [01_book_opcount_start_anchor_program_gate.json](test_results/01_book_opcount_start_anchor_program_gate.json)
- [01_book_opcount_start_anchor_program_gate.md](test_results/01_book_opcount_start_anchor_program_gate.md)
