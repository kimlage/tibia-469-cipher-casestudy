# 133. Literal-Length-Derived Recipe Compile

Classification: `literal_length_derived_canonical_online_recipe`
Translation delta: `NONE`

## Purpose

The canonical online formula still carried `length` on literal operations,
even though that value is derivable from the literal text payload. This
compile materializes a stricter recipe representation where literal
length is restored only during validation as `len(text)`.

## Result

- Canonical bits: `8343.062`
- Literal-length-derived bits: `8343.062`
- Score delta: `+0.000000000000`
- Roundtrip: `70/70`
- Removed literal `length` fields: `87`
- Copy `length` fields retained: `261`
- Additional recipe JSON byte reduction: `977`

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_literal_length_derived_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_literal_length_derived_formula_469.json)

## Interpretation

Literal run length is not an independent recipe dependency when the
literal payload text is already declared. Copy length remains a real
declared dependency because copied text is not stored in the operation.

## Boundary

- No plaintext or translation is introduced.
- Row0/table origin is unchanged.
- The compression bound is unchanged.
