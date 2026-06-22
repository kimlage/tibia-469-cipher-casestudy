# Boundary-Mark Propagation Program Gate

Classification: `boundary_mark_propagation_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Do source-side boundary marks propagate through copy events and explain additional future copy intervals beyond executable v3?

## Summary

- Propagated copy hits/misses: `34/174` out of `208`.
- Delta hits vs event-only propagation: `5`.
- Delta hits vs shuffled propagation: `-14`.
- V3 residual baseline: `3280.192` bits.
- Propagated residual bits: `3280.551`.
- Delta vs v3 residual: `0.359` bits.
- Rank/fallback/composition/literal bits: `344.768` / `1558.196` / `493.954` / `883.633`.

## Modes

| Mode | Hits | Residual bits | Delta vs v3 | Rank bits | Fallback bits |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_no_propagation` | `29` | `3280.192` | `0.000` | `275.077` | `1609.521` |
| `event_only_propagation` | `29` | `3280.192` | `0.000` | `275.077` | `1609.521` |
| `shuffled_propagation` | `48` | `3295.604` | `15.412` | `526.849` | `1433.803` |
| `propagated_marks` | `34` | `3280.551` | `0.359` | `344.768` | `1558.196` |

## Decision

`boundary_mark_propagation_not_promoted`: propagated marks do not improve the executable v3 residual ledger beyond controls.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
