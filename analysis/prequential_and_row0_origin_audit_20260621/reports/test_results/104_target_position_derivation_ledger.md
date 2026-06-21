# Target Position Derivation Ledger

Classification: `target_position_derived_from_length_sequence`
Translation delta: `NONE`

## Purpose

The source-free skeleton was described as operation type, target start,
and length. This ledger checks whether target positions are independent
fields or deterministic consequences of the length sequence.

## Result

- Books: `60`.
- Operation rows checked: `261`.
- Target-start derivable rows: `261`.
- Target-start violations: `0`.
- Remaining derivable rows: `261`.
- Remaining violations: `0`.
- Op-index sequential rows: `261`.
- Op-index violations: `0`.
- Independent skeleton records after target derivation: `261`.
- Record delta vs gate-99 skeleton atlas: `0`.
- Record delta vs gate-99 total materialized records: `0`.

## Decision

- Target start derivable: `True`.
- Remaining derivable: `True`.
- Promotes generator: `False`.
- Target positions are not an independent skeleton dependency: all target_start values equal the cumulative sum of previous operation lengths within each book, and remaining equals book length minus that position. This sharpens the ledger from type/target/length rows to type/length rows with derived target positions, but it does not reduce the one-row-per-operation atlas count or derive op types, lengths, copy sources, or literal payload.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
