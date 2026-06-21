# 134. Op-Type-Derived Recipe Compile

Classification: `op_type_derived_canonical_online_recipe`
Translation delta: `NONE`

## Purpose

The literal-length-derived formula still carried explicit operation
`type` fields. This compile tests whether operation type is derivable
from each op's field shape: `text` means literal, while
`source_digit_pos` plus `length` means copy.

## Result

- Source bits: `8343.062`
- Type-derived bits: `8343.062`
- Score delta: `+0.000000000000`
- Roundtrip: `70/70`
- Removed `type` fields: `348`
- Literal-shaped ops: `87`
- Copy-shaped ops: `261`
- Additional recipe JSON byte reduction: `5133`

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_type_derived_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_type_derived_formula_469.json)

## Interpretation

Operation type is not an independent recipe dependency in the compact
formula. After this compile, the remaining operation-level declared
dependencies are literal payload text, copy source, and copy length.

## Boundary

- No plaintext or translation is introduced.
- Row0/table origin is unchanged.
- The compression bound is unchanged.
