# Online Literal Stop Rule Audit

Classification: `online_literal_stop_rule_partial_not_source_free`
Translation delta: `NONE`

## Purpose

Gate 05 showed that literal stops are optimal inside declared windows,
but not over the full suffix. This gate tests online/local stopping
rules that do not use the declared window as the search horizon.

## Best Rule

- Policy: `first_confirmed_max_copy_length_peak`.
- Confirm window: `6`.
- Followed-by-copy hits: `45/49`.
- All literal gap hits with book-end default: `50/54`.

## Policy Scoreboard

| Policy | Window | Followed hits | All hits with book-end default |
|---|---:|---:|---:|
| `first_confirmed_max_copy_length_peak` | `6` | `45/49` | `50/54` |
| `first_confirmed_max_copy_length_peak` | `5` | `44/49` | `49/54` |
| `first_confirmed_max_copy_length_peak` | `7` | `42/49` | `47/54` |
| `first_confirmed_total_advance_peak` | `6` | `40/49` | `45/54` |
| `first_confirmed_max_copy_length_peak` | `4` | `39/49` | `44/54` |
| `first_confirmed_max_copy_length_peak` | `8` | `39/49` | `44/54` |
| `first_confirmed_total_advance_peak` | `5` | `39/49` | `44/54` |
| `first_confirmed_total_advance_peak` | `7` | `38/49` | `43/54` |
| `first_confirmed_max_copy_length_peak` | `3` | `37/49` | `42/54` |
| `first_confirmed_max_copy_length_peak` | `9` | `37/49` | `42/54` |
| `first_confirmed_max_copy_length_peak` | `10` | `37/49` | `42/54` |
| `first_confirmed_total_advance_peak` | `4` | `37/49` | `42/54` |

## Prequential

| Cutoff | Train | Test | Selected | Test hits | Oracle hits |
|---:|---:|---:|---|---:|---:|
| `20` | `24` | `25` | `first_confirmed_max_copy_length_peak:6` | `23/25` | `23/25` |
| `30` | `30` | `19` | `first_confirmed_max_copy_length_peak:6` | `17/19` | `17/19` |
| `40` | `36` | `13` | `first_confirmed_max_copy_length_peak:6` | `12/13` | `13/13` |
| `50` | `43` | `6` | `first_confirmed_max_copy_length_peak:6` | `5/6` | `6/6` |
| `60` | `47` | `2` | `first_confirmed_max_copy_length_peak:6` | `2/2` | `2/2` |

## Decision

- Promotes partial online literal stop rule: `True`.
- Promotes source-free literal stop rule: `False`.
- A small online confirmation rule explains most literal stops: choose the first local peak in available copy length after a six-digit confirmation window. It is stable under prefix selection, but it still misses four followed-by-copy gaps, so literal windows remain partially retained rather than fully generated.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
