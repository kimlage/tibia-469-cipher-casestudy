# Recipe Representation Dependency Gate

Classification: `recipe_representation_artifacts_removed_dependencies_retained`
Translation delta: `NONE`

## Purpose

The online formula compiles remove several fields from the operation
recipe without changing the score. This gate separates derivable
representation artifacts from recipe dependencies that remain declared.

## Summary

- Active/type-derived bits: `8343.062` / `8343.062`.
- Score delta: `0.000000000000` bits.
- Roundtrip: `70/70`.
- Removed book `length` fields: `70`.
- Removed copy `target_start` fields: `261`.
- Removed literal `length` fields: `87`.
- Removed op `type` fields: `348`.
- Total removed independent fields: `766`.
- Recipe JSON bytes: `24355` -> `12633`.
- Total JSON byte saving: `11722`.

## Remaining Declared Dependencies

- Literal text fields: `87` covering `857` digits.
- Copy source fields: `261` covering `10406` copied digits.
- Copy length fields: `261` covering `10406` copied digits.
- Literal/copied digit fractions: `0.076090` / `0.923910`.

## Interpretation

This is a mechanical-description simplification, not a compression-bound
promotion. Book length is derived from operation lengths, copy target
start from cumulative emitted position, literal length from `len(text)`,
and operation type from field shape. The compact recipe still has to
declare literal payload, copy source, and copy length.

## Boundary

- No compression bound is promoted.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
