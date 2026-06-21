# Book Length Ledger

Classification: `book_length_ledger_audit_only`
Translation delta: `NONE`

## Purpose

Map the 70 declared book lengths and separate residual compression
from a source-free generator.

## Summary

- Book count: `70`.
- Length range: `35..294`.
- Unique lengths: `51`.
- Repeated length rows: `29`.
- Raw gamma length bits: `1030`.
- Active signed-Rice ledger: `anchor=151`, `k=5`, `566` bits.
- Active gain vs raw gamma: `464` bits.

## Decision

- Book lengths are clustered enough for a compact residual ledger, but the active Rice model still declares per-book residuals. It is not a generator for the length sequence.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
