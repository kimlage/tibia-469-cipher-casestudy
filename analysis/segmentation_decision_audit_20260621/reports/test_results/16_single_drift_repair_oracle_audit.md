# Single Drift Repair Oracle Audit

Classification: `single_drift_oracle_partial_path_dependency`
Translation delta: `NONE`

## Purpose

Gate 16 asks whether the `12` residual books from the integrated
`window5` parser are local first-decision failures or deeper path
dependencies. It grants an explicit stable-projection oracle only
for diagnostics: when the parser first diverges, the audit can replace
that one operation with the stable operation and then resume the same
parser.

This is not a promoted parser rule because the repair operation is
chosen from the stable projection.

## Correction Budget

| Stable-oracle corrections per book | Exact books | Residual repairs vs baseline |
|---:|---:|---:|
| `0` | `48/60` | `0` |
| `1` | `59/60` | `11` |
| `2` | `60/60` | `12` |
| `3` | `60/60` | `12` |
| `4` | `60/60` | `12` |
| `5` | `60/60` | `12` |

## Residual Topology

- Baseline exact books: `48/60`.
- One-correction exact books: `59/60`.
- Residual books repaired by one correction: `[14, 16, 21, 23, 26, 34, 39, 45, 49, 55, 57]`.
- Full-oracle correction-count histogram on residual books: `{1: 11, 2: 1}`.
- First-correction drift classes: `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}`.

| Book | First correction class | Full oracle corrections | One correction exact? |
|---:|---|---:|---|
| `14` | `literal_understop` | `1` | `True` |
| `16` | `copy_started_inside_stable_literal` | `1` | `True` |
| `20` | `internal_copy_missed_as_literal` | `2` | `False` |
| `21` | `book_start_copy_missed_as_literal` | `1` | `True` |
| `23` | `literal_understop` | `1` | `True` |
| `26` | `book_start_copy_missed_as_literal` | `1` | `True` |
| `34` | `internal_copy_missed_as_literal` | `1` | `True` |
| `39` | `book_start_copy_missed_as_literal` | `1` | `True` |
| `45` | `internal_copy_missed_as_literal` | `1` | `True` |
| `49` | `literal_understop` | `1` | `True` |
| `55` | `copy_length_drift_same_source` | `1` | `True` |
| `57` | `literal_understop` | `1` | `True` |

## Decision

- Promotes local repair rule: `False`.
- A stable-projection oracle correction at the first drift is a diagnostic upper bound, not a rule. It tests whether the remaining parser failures are isolated first-decision errors or deeper path dependencies.
- The result is an oracle dependency map, not a new generator.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
