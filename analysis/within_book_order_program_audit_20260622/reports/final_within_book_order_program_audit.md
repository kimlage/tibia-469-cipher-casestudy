# Final Within-Book Order Program Audit

Status: `analysis_only`
Classification: `WITHIN_BOOK_ORDER_PROGRAM_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Given the true per-book joint-token multiset, can a prefix-trained sequential policy generate or reduce the exact within-book order index?

## Result

The no-replacement order policy costs `606.765` bits versus `587.378` uniform order bits (`19.387` bits worse than uniform). It beats shuffled-train p95 in `1/5` cells and shuffled-test p95 in `0/5` cells. Beam20 keeps the true sequence in `118` held-out books, `37` nontrivial.

## Decision

The gate grants the exact book multiset, so even a positive order result would be only a component. Row0, plaintext, translation, and compression_bound remain unchanged.

## Reproducible Artifacts

- [01_within_book_order_program_gate.py](../scripts/01_within_book_order_program_gate.py)
- [01_within_book_order_program_gate.json](test_results/01_within_book_order_program_gate.json)
- [01_within_book_order_program_gate.md](test_results/01_within_book_order_program_gate.md)
