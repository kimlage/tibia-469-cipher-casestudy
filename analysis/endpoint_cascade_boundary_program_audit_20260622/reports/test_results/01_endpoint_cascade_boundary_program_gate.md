# Endpoint-Cascade Boundary Program Gate

Classification: `WEAK_ENDPOINT_CASCADE_BOUNDARY_CANDIDATE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can a fixed endpoint cascade use both end-only and start-only anchors without paying a per-copy mode bit?

## Policy Costs

| Policy | Residual bits | Delta vs v3 | Delta vs v4 no-decl | Copy bits | Composition bits | Classes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `none` | `3280.192` | `0.000` | `49.465` | `1884.598` | `511.961` | `{'fallback': 179, 'both': 29}` |
| `start_first` | `3263.470` | `-16.722` | `32.744` | `1867.876` | `511.961` | `{'one_sided_start': 40, 'fallback': 139, 'both': 29}` |
| `end_first` | `3230.726` | `-49.465` | `0.000` | `1835.132` | `511.961` | `{'fallback': 123, 'one_sided_end': 56, 'both': 29}` |
| `best_with_mode_bit` | `3310.004` | `29.813` | `79.278` | `1914.410` | `511.961` | `{'one_sided_start': 40, 'one_sided_end': 56, 'fallback': 83, 'both': 29}` |
| `end_then_start` | `3214.004` | `-66.187` | `-16.722` | `1818.410` | `511.961` | `{'one_sided_start': 40, 'one_sided_end': 56, 'fallback': 83, 'both': 29}` |
| `start_then_end` | `3214.004` | `-66.187` | `-16.722` | `1818.410` | `511.961` | `{'one_sided_start': 40, 'one_sided_end': 56, 'fallback': 83, 'both': 29}` |

## Prefix Selection

| Cutoff | Selected policy | Train delta vs v4 no-decl | Test delta vs v4 no-decl | Test classes |
| ---: | --- | ---: | ---: | --- |
| `20` | `end_then_start` | `-10.031` | `-6.691` | `{'one_sided_end': 44, 'one_sided_start': 30, 'fallback': 63, 'both': 18}` |
| `30` | `end_then_start` | `-17.189` | `0.467` | `{'fallback': 51, 'one_sided_end': 35, 'one_sided_start': 24, 'both': 9}` |
| `40` | `end_then_start` | `-9.337` | `-7.385` | `{'fallback': 32, 'one_sided_end': 27, 'one_sided_start': 15, 'both': 6}` |
| `50` | `end_then_start` | `-9.938` | `-6.784` | `{'one_sided_start': 11, 'one_sided_end': 16, 'fallback': 19, 'both': 3}` |
| `60` | `end_then_start` | `-18.281` | `1.559` | `{'one_sided_start': 5, 'one_sided_end': 7, 'fallback': 5, 'both': 1}` |

## Decision

- Best policy: `end_then_start`.
- Declaration bits for `6` tested policies: `2.585`.
- Delta after declaration vs v4 residual: `-16.137` bits.
- Prefix-selected positive splits vs v4: `3/5`.
- Prefix-selected aggregate delta vs v4: `-18.836` bits.

`WEAK_ENDPOINT_CASCADE_BOUNDARY_CANDIDATE`: full-fit cost falls, but prefix holdout is not stable enough to promote.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
