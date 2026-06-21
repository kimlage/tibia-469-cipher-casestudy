# Source Interval Precision Gate

Classification: `source_interval_precision_weak_clue_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 51 tests whether the gate-50 source-interval weak clue can
be made precise. A source-interval policy may repair a decision
only when an observable predicate fires; otherwise the active
parser branch is retained.

## Summary

- Policy-decision rows: `2808`.
- Policies: `12`.
- Predicates: `1780`.
- Scored rules: `30720`.
- Best rule: `max_payload_occurrences` / `changes_type_eq_True__and__source_target_interval_distance_ge_3`.
- Best residual hits: `5/10`.
- Best clean false changes: `4`.
- Best residual false repairs: `0`.
- Best zero-FP rule: `max_context_recurrence_r8` / `drift_class_eq_book_start_copy_missed_as_literal`.
- Best zero-FP residual hits: `3/10`.

## Scoreboard

| Policy | Predicate | Residual hits | Clean false changes | Residual false | Selected |
|---|---|---:|---:|---:|---:|
| `max_payload_occurrences` | `changes_type_eq_True__and__source_target_interval_distance_ge_3` | `5/10` | `4` | `0` | `9` |
| `min_source_target_start_distance` | `changes_type_eq_True__and__source_target_interval_distance_ge_3` | `5/10` | `4` | `0` | `9` |
| `max_payload_occurrences` | `changes_type_eq_True__and__r2_interval_distance_ge_3` | `5/10` | `4` | `0` | `9` |
| `min_source_target_start_distance` | `changes_type_eq_True__and__r2_interval_distance_ge_3` | `5/10` | `4` | `0` | `9` |
| `max_payload_occurrences` | `changes_type_eq_True__and__source_target_end_distance_ge_1` | `5/10` | `5` | `0` | `10` |
| `min_source_target_start_distance` | `changes_type_eq_True__and__source_target_end_distance_ge_1` | `5/10` | `5` | `0` | `10` |
| `max_payload_occurrences` | `changes_type_eq_True__and__r4_interval_distance_ge_6` | `5/10` | `5` | `0` | `10` |
| `min_source_target_start_distance` | `changes_type_eq_True__and__r4_interval_distance_ge_6` | `5/10` | `5` | `0` | `10` |
| `max_payload_occurrences` | `changes_type_eq_True__and__r4_interval_distance_ge_5` | `5/10` | `5` | `0` | `10` |
| `min_source_target_start_distance` | `changes_type_eq_True__and__r4_interval_distance_ge_5` | `5/10` | `5` | `0` | `10` |
| `max_payload_occurrences` | `changes_type_eq_True__and__r4_end_distance_ge_3` | `5/10` | `5` | `0` | `10` |
| `min_source_target_start_distance` | `changes_type_eq_True__and__r4_end_distance_ge_3` | `5/10` | `5` | `0` | `10` |
| `max_payload_occurrences` | `changes_type_eq_True__and__r2_end_distance_ge_1` | `5/10` | `5` | `0` | `10` |
| `min_source_target_start_distance` | `changes_type_eq_True__and__r2_end_distance_ge_1` | `5/10` | `5` | `0` | `10` |
| `max_payload_occurrences` | `changes_type_eq_True__and__r8_interval_distance_ge_14` | `5/10` | `5` | `1` | `11` |

## Prefix/Holdout

| Cutoff | Policy | Predicate | Test residual hits | Test clean false changes | Test residual false |
|---:|---|---|---:|---:|---:|
| `20` | `max_context_recurrence_r2` | `r8_start_distance_le_4` | `0/8` | `7` | `0` |
| `30` | `max_payload_occurrences` | `changes_type_eq_True` | `2/5` | `7` | `1` |
| `40` | `max_payload_occurrences` | `changes_type_eq_True` | `0/3` | `5` | `1` |
| `50` | `max_payload_occurrences` | `changes_type_eq_True` | `0/2` | `3` | `0` |
| `60` | `max_payload_occurrences` | `changes_type_eq_True` | `0/0` | `1` | `0` |

## Decision

- Promotes source-interval precision rule: `False`.
- Prequential cover-all-residual cells: `0/4`.
- Prequential zero-clean-false-change cells: `0/5`.
- Gate 51 asks whether the gate-50 source-interval weak clue can be converted into a precise repair rule by observable predicates. Full-fit pair predicates are diagnostic; prequential selection uses single predicates to avoid smuggling residual-site lookup.
- The source-interval signal does not convert into a clean parser rule.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
