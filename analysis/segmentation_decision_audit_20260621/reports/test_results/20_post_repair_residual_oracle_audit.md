# Post-Repair Residual Oracle Audit

Classification: `post_repair_oracle_localizes_residual_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 20 keeps the gate-18 non-oracle classifier active, then grants
stable-projection oracle corrections only as a diagnostic upper bound.
It asks whether the remaining `10` residual books are still local
first-decision failures or have become deeper path dependencies.

## Correction Budget

- Active classifier: `if_peak_len_le5_then_skip_to_next_peak_ge5`.
- Active exact books: `50/60`.

| Stable-oracle corrections per book | Exact books | Residual repairs vs active |
|---:|---:|---:|
| `0` | `50/60` | `0` |
| `1` | `59/60` | `9` |
| `2` | `60/60` | `10` |
| `3` | `60/60` | `10` |
| `4` | `60/60` | `10` |
| `5` | `60/60` | `10` |

## Residual Topology

- One-correction repaired residual books: `[14, 16, 21, 26, 34, 39, 45, 55, 57]`.
- Full-oracle correction-count histogram: `{1: 9, 2: 1}`.
- First-oracle correction drift classes: `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 2}`.

| Book | First oracle class | Full oracle corrections | One correction exact? |
|---:|---|---:|---|
| `14` | `literal_understop` | `1` | `True` |
| `16` | `copy_started_inside_stable_literal` | `1` | `True` |
| `20` | `internal_copy_missed_as_literal` | `2` | `False` |
| `21` | `book_start_copy_missed_as_literal` | `1` | `True` |
| `26` | `book_start_copy_missed_as_literal` | `1` | `True` |
| `34` | `internal_copy_missed_as_literal` | `1` | `True` |
| `39` | `book_start_copy_missed_as_literal` | `1` | `True` |
| `45` | `internal_copy_missed_as_literal` | `1` | `True` |
| `55` | `copy_length_drift_same_source` | `1` | `True` |
| `57` | `literal_understop` | `1` | `True` |

## Decision

- Promotes parser rule: `False`.
- After the gate18 non-oracle repair, this audit grants stable-projection corrections only to measure whether the remaining drifts are local first-decision failures or deeper path dependencies.
- The result is an oracle dependency map, not a generator.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
