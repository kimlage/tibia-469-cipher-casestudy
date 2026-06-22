# One-Sided Source-Boundary Program Gate

Classification: `PROMOTED_ONE_SIDED_SOURCE_BOUNDARY_PROGRAM`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can fallback copy intervals be reduced when only one source-side endpoint is in the promoted boundary set?

## Endpoint Coverage

- Both endpoints hit: `29`.
- Start-only hits: `40`.
- End-only hits: `56`.
- Both endpoints missing: `83`.
- Best-policy delta after declaration: `-47.465` bits.
- Prefix-selected positive splits: `5/5`.
- Prefix-selected aggregate delta: `-62.507` bits.

## Policy Costs

| Policy | Residual bits | Delta vs v3 | Copy bits | Composition bits | Classes |
| --- | ---: | ---: | ---: | ---: | --- |
| `none` | `3280.192` | `0.000` | `1884.598` | `511.961` | `{'fallback': 179, 'both': 29}` |
| `start_first` | `3263.470` | `-16.722` | `1867.876` | `511.961` | `{'one_sided_start': 40, 'fallback': 139, 'both': 29}` |
| `end_first` | `3230.726` | `-49.465` | `1835.132` | `511.961` | `{'fallback': 123, 'one_sided_end': 56, 'both': 29}` |
| `best_with_mode_bit` | `3310.004` | `29.813` | `1914.410` | `511.961` | `{'one_sided_start': 40, 'one_sided_end': 56, 'fallback': 83, 'both': 29}` |

## Prefix Selection

| Cutoff | Selected policy | Train delta | Test delta | Test classes |
| ---: | --- | ---: | ---: | --- |
| `20` | `end_first` | `-24.923` | `-24.543` | `{'one_sided_end': 44, 'fallback': 93, 'both': 18}` |
| `30` | `end_first` | `-35.323` | `-14.143` | `{'fallback': 75, 'one_sided_end': 35, 'both': 9}` |
| `40` | `end_first` | `-38.342` | `-11.124` | `{'fallback': 47, 'one_sided_end': 27, 'both': 6}` |
| `50` | `end_first` | `-40.120` | `-9.345` | `{'fallback': 30, 'one_sided_end': 16, 'both': 3}` |
| `60` | `end_first` | `-46.112` | `-3.353` | `{'fallback': 10, 'one_sided_end': 7, 'both': 1}` |

## Decision

`PROMOTED_ONE_SIDED_SOURCE_BOUNDARY_PROGRAM`: one-sided anchors reduce the v3 ledger.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
