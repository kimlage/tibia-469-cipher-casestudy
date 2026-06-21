# 132. Canonical Online Recipe Formula Compile

Classification: `canonical_online_recipe_representation`
Translation delta: `NONE`

## Purpose

Audit 131 proved that per-book `length` and copy `target_start` are
derivable representation fields in the online reparse formula. This
compile materializes the canonical formula projection without those
fields.

## Result

- Active bits: `8343.062`
- Canonical bits: `8343.062`
- Score delta: `+0.000000000000`
- Roundtrip: `70/70`
- Removed book `length` fields: `70`
- Removed copy `target_start` fields: `261`
- Recipe JSON byte reduction: `5612`

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_canonical_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_canonical_formula_469.json)

## Interpretation

This is a lossless mechanical representation improvement. The current
`8343.062` bit bound is unchanged, but the committed formula no longer
needs to carry fields that can be derived during decoding. Literal payload,
copy source, and copy length remain declared recipe dependencies.

## Boundary

- No plaintext or translation is introduced.
- Row0/table origin is unchanged.
- The compression bound is not lowered by this compile.
