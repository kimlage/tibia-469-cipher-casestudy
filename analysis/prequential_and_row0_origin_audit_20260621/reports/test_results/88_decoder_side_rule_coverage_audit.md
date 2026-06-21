# Decoder-Side Rule Coverage Audit

Classification: `decoder_side_rule_coverage_insufficient`
Translation delta: `NONE`

## Purpose

Gate 87 showed that the stable path projection still uses target text.
This audit tests simple decoder-side rules for the projection copy
sources and lengths, with negative controls for random legal sources and
permuted lengths.

## Coverage

- Projection copy events: `208`.
- Projection copied digits: `9302`.
- Literal payload digits still materialized: `265`.
- Best decoder-side source rule: `source_is_previous_copy_end` = `6/208`.
- Best decoder-side length rule: `length_is_decoder_max` = `58/208`.
- Best decoder-side joint rule: `joint_previous_end_decoder_max` = `2/208`.
- Decoder joint rule covers all: `False`.
- Promotes generator: `False`.

## Rule Counts

| Rule | Hits |
|---|---:|
| `joint_earliest_target_match_decoder_max` | `58` |
| `joint_latest_legal_decoder_max` | `0` |
| `joint_previous_end_decoder_max` | `2` |
| `joint_unique_target_match_decoder_max` | `24` |
| `joint_zero_decoder_max` | `1` |
| `length_is_decoder_max` | `58` |
| `length_is_min_len` | `7` |
| `length_is_previous_copy_length` | `2` |
| `length_is_remaining_book` | `55` |
| `source_is_earliest_target_match` | `208` |
| `source_is_latest_legal` | `0` |
| `source_is_latest_target_match` | `78` |
| `source_is_previous_copy_end` | `6` |
| `source_is_unique_target_match` | `78` |
| `source_is_zero` | `1` |

## Controls

- Previous-end source p-value: `0.0000`.
- Zero source p-value: `0.0520`.
- Latest-legal source p-value: `1.0000`.
- Decoder-max length p-value: `0.0000`.

## Decision

- Simple decoder-side source and length rules explain only part of the stable projection. The projection remains target-text dependent unless copy source, copy length, and literal payload can be generated without oracle access.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
