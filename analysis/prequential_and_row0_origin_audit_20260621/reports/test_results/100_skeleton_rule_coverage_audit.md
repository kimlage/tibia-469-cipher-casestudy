# Skeleton Rule Coverage Audit

Classification: `skeleton_simple_rule_coverage_insufficient`
Translation delta: `NONE`

## Purpose

Gate 98 proved an exact source-free skeleton atlas. This audit checks
whether simple rules over decoder-visible state can generate that skeleton,
or whether it remains materialized.

## Coverage

- Skeleton ops: `261`.
- Copy/literal ops: `208` / `53`.
- Best op-type rule: `always_copy` = `208/261`.
- Best length rule: `length_gte_20` = `116/261`.
- Best literal-length rule: `literal_length_is_remaining_book` = `5/53`.
- Best copy-length rule: `copy_length_is_remaining_book` = `55/208`.
- Best target-dependent type control: `copy_when_minlen_match_available` = `208/261`.

## Decision

- Simple rule covers skeleton: `False`.
- Promotes generator: `False`.
- The exact skeleton is stable, but simple source-free state rules do not generate its operation types and lengths. Target-dependent availability explains part of the type pattern, which reinforces that the skeleton is an atlas rather than a decoder-side generator.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
