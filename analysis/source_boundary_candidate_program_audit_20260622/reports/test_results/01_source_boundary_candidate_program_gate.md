# Source-Boundary Candidate Program Gate

Classification: `PROMOTED_SOURCE_BOUNDARY_PROGRAM`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can copy source and length be derived by choosing an interval between decoder-visible boundaries in the already emitted material?

## Summary

- Best boundary system: `event_plus_surprisal_top20`.
- Selected interval policy: `long_recent`.
- Copy hits/misses: `29/179` out of `208`.
- V2 residual baseline: `3423.183` bits.
- Source-boundary program bits: `3280.192` bits.
- Delta vs v2 residual: `-142.991` bits.
- Composition bits after derived copy lengths: `511.961`.
- Boundary count mean: `1188.817`.
- Candidate interval count median/mean/max on hits: `2253` / `6318.621` / `47395`.
- Top-80 hits: `1/208`.

## Systems

| System | Hits | Bits | Delta vs v2 | Policy |
| --- | ---: | ---: | ---: | --- |
| `event_boundaries` | `5` | `3326.336` | `-96.847` | `long_recent` |
| `surprisal_top05` | `1` | `3357.845` | `-65.338` | `recent_long` |
| `surprisal_top10` | `5` | `3341.794` | `-81.388` | `recent_long` |
| `surprisal_top20` | `20` | `3311.221` | `-111.962` | `long_recent` |
| `event_plus_surprisal_top05` | `10` | `3309.479` | `-113.703` | `recent_long` |
| `event_plus_surprisal_top10` | `14` | `3308.679` | `-114.503` | `recent_long` |
| `event_plus_surprisal_top20` | `29` | `3280.192` | `-142.991` | `long_recent` |

## Prefix Holdout

| Cutoff | Policy | Hits | Program bits | V2 bits | Delta |
| ---: | --- | ---: | ---: | ---: | ---: |
| `20` | `long_recent` | `18` | `2207.586` | `2303.166` | `-95.580` |
| `30` | `long_recent` | `9` | `1715.300` | `1786.763` | `-71.463` |
| `40` | `long_recent` | `6` | `1220.157` | `1274.354` | `-54.197` |
| `50` | `long_recent` | `3` | `747.630` | `774.007` | `-26.377` |
| `60` | `long_recent` | `1` | `224.033` | `234.951` | `-10.918` |

## Controls

- Shuffled event-boundary program bits: `3305.138`.
- Shuffled event-boundary hits: `22/208`.
- Random boundary hits p95: `15.000`.
- Random boundary copy bits p05/p50/p95: `1932.531` / `1976.612` / `2027.732`.

## Decision

`PROMOTED_SOURCE_BOUNDARY_PROGRAM`: source intervals reduce the residual ledger and beat controls.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
