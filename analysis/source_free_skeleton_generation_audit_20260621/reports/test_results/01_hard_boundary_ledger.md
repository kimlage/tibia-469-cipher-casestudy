# Hard Boundary Ledger

Classification: `hard_boundary_ledger_audit_only`
Translation delta: `NONE`

## Purpose

Freeze the exact remaining dependencies after the source-free skeleton
invariance result. This is the boundary for future generator work.

## Ledger

- Skeleton atlas records: `261`.
- Copy-source fields: `208`.
- Literal payload chunks/digits: `53` / `266`.
- External dependency fields after skeleton: `261`.
- Total materialized records after skeleton: `522`.
- Copied digits covered by skeleton copies: `9301`.
- Seed books external: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`.

## Decision

- The next main test is skeleton generation, not source-choice selection.
- Copy source and literal payload remain external after the skeleton.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
