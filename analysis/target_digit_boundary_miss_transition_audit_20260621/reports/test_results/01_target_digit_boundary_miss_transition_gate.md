# Target Digit Boundary Miss Transition Gate

Classification: `target_digit_boundary_miss_transition_classes_rejected_control`
Translation delta: `NONE`

## Purpose

Test whether the cutpoints missed by `right_ge:4` are explained by
skeleton transition classes, length buckets, ordinal position, or chunk
recurrence diagnostics.

## Summary

- Cutpoints/hits/misses: `201` / `94` / `107`.
- Features tested: `15`.
- Baseline miss-label atlas: `196.243` bits.
- Best feature: `shape` with `20` categories.
- Best saving before/after feature charge: `39.806` / `35.900` bits.
- Random relabel p95 before feature charge: `44.763` bits.
- Beats random p95: `False`.
- Prefix-selected positive test cells: `5/5`.

The best feature looks useful before controls, but the same category sizes
produce comparable savings under random miss-label permutations. Chunk
recurrence features are sparse and do not explain the miss set.

## Top Features

| Feature | Categories | Saving after charge | Saving before charge |
| --- | ---: | ---: | ---: |
| `shape` | `20` | `35.900` | `39.806` |
| `book_mod10` | `10` | `24.887` | `28.794` |
| `op_mod5` | `5` | `11.840` | `15.747` |
| `pos_quint` | `5` | `10.313` | `14.220` |
| `prev_len_bucket` | `3` | `6.620` | `10.527` |
| `transition` | `3` | `2.867` | `6.774` |
| `next_len_bucket` | `3` | `2.847` | `6.754` |
| `op_mod3` | `3` | `2.503` | `6.410` |

## Decision

- Miss transition/chunk feature promoted: `False`.
- Endpoint generator promoted: `False`.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
