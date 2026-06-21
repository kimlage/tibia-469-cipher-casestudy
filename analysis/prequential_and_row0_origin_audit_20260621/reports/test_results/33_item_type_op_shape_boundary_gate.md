# Item Type Op Shape Boundary Gate

Classification: `item_type_split_only_retained_op_type_shape_derived`
Translation delta: `NONE`

## Purpose

Item type appears in two places: as a learned literal/copy operation
sequence in the generation ledger, and as an explicit `type` field in
some recipe JSON projections. This gate separates those two meanings.

## Summary

- Split-only formula bits: `8561.792` -> `8558.667`.
- Split-only gain: `3.125` bits.
- Conservative split-only gain: `2.125` bits.
- Item-type stream bits: `223.412` -> `220.287`.
- Coded item-type items: `287`.
- Forced item-type items: `81` (`literal->copy 73`, `short suffix 8`).
- Current/best alpha: `2` / `2`.
- Nearest alpha-1 delta: `0.309` bits.
- Removed explicit op `type` fields: `348`.
- Literal/copy-shaped ops: `87` / `261`.
- Ambiguous shape ops: `0`.
- Op-type derivation score delta: `0.000000000000` bits.

## Interpretation

The split-only item-type model is retained as a real mechanical component:
it improved the old bound and alpha `2` remains best. That does not mean
the compact recipe must carry explicit op `type` fields. Once operation
shape is normalized, `text` means literal and `source_digit_pos` plus
`length` means copy; the explicit `type` field is derivable with zero
score delta and `70/70` roundtrip.

## Boundary

- No new compression bound is promoted by this gate.
- Item-type sequence modeling and recipe `type` fields are separate layers.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
