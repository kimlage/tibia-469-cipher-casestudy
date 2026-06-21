# Exact Skeleton Dependency Ledger

Classification: `exact_skeleton_dependency_ledger_atlas_only`
Translation delta: `NONE`

## Purpose

Gate 98 proved that the exact source-free operation skeleton is invariant.
This ledger asks what dependency families that actually removes, and what
still remains materialized before a decoder-side generator exists.

## Ledger

- Active external dependency fields: `609`.
- Skeleton atlas records: `261`.
- External fields after skeleton: `261`.
- Total materialized records after skeleton: `522`.
- Copy-source fields after skeleton: `208`.
- Literal payload chunks/digits after skeleton: `53` / `266`.
- Copied digits covered by skeleton copies: `9301`.
- External-field delta vs active: `-348`.
- Total-materialized-record delta vs active: `-87`.

## Decision

- Ledger dependency reduction: `True`.
- Promotes generator: `False`.
- Decoder can emit books from skeleton without payload/source fields: `False`.
- The exact source-free skeleton moves operation type and length into a stable atlas, reducing the residual external field families to literal payload chunks and copy-source choices. Because the atlas itself is still materialized and source/payload fields remain external, this is a dependency ledger improvement rather than a generator promotion.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
