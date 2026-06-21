# Operation Type Dependency Ledger

Classification: `operation_type_dependency_reduced_not_promoted`
Translation delta: `NONE`

## Purpose

Gates 103-106 show that operation type is strongly constrained by
copy availability and optional-literal rules. This ledger separates
conceptual op-type dependency reduction from actual generator promotion.

## Ledger

- Operations: `261`.
- Copies/literals: `208` / `53`.
- Forced literals from no copy availability: `36`.
- Optional literal exceptions before rule: `17`.
- Optional literal rule: `(length_le_5 and remaining_ge_10)`.
- Rule TP/FP/FN: `[17, 3, 0]`.
- Residual type errors after rule: `3`.
- Explicit op-type fields before/after rule: `261` / `3`.
- Conceptual op-type field delta: `-258`.
- Length atlas records retained: `261`.
- Type+length records after rule: `264`.
- Record delta vs exact skeleton atlas: `3`.
- Total materialized record delta vs gate 99: `3`.

## Prequential Support

- Evaluated splits: `4`.
- Train-selected beats baseline splits: `4`.
- Max train-selected oracle gap: `1`.
- Promotes prequential rule: `False`.

## Decision

- Promotes type generator: `False`.
- Operation type is mostly derivable once target copy availability and the length atlas are allowed: no-availability forces 36 literals, availability covers all 208 copies, and a short rule reduces the 17 optional literal exceptions to 3 residual errors. This reduces explicit op-type dependency conceptually from 261 fields to 3 residual fields, with prequential support, but it does not reduce the materialized atlas because the 261 length rows, target copy availability, copy sources, and literal payload remain external.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
