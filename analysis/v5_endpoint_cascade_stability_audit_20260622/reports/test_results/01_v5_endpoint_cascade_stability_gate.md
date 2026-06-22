# V5 Endpoint-Cascade Stability Gate

Classification: `WEAK_V5_ENDPOINT_CASCADE_FULLFIT_ONLY`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- Best policy: `end_then_start`.
- V5 residual bits: `3220.921`.
- Best residual bits before declaration: `3205.395`.
- Declaration bits: `2.000`.
- Delta after declaration vs v5: `-13.526`.
- Prefix-positive splits: `2/5`.
- Prefix aggregate delta vs v5: `12.679`.
- Shuffled residual p05/p50: `3221.714` / `3234.393`.

## Policy Costs

| Policy | Residual bits | Copy bits | Composition bits | Classes |
| --- | ---: | ---: | ---: | --- |
| `end_first` | `3219.336` | `1895.745` | `439.959` | `{'fallback': 101, 'end': 55, 'both': 52}` |
| `start_first` | `3234.001` | `1910.410` | `439.959` | `{'start': 41, 'fallback': 115, 'both': 52}` |
| `end_then_start` | `3205.395` | `1881.803` | `439.959` | `{'start': 41, 'end': 55, 'fallback': 60, 'both': 52}` |
| `start_then_end` | `3205.395` | `1881.803` | `439.959` | `{'start': 41, 'end': 55, 'fallback': 60, 'both': 52}` |

## Prefix Selection

| Cutoff | Selected policy | Train delta | Test delta |
| ---: | --- | ---: | ---: |
| `20` | `end_then_start` | `-9.464` | `-4.477` |
| `30` | `end_then_start` | `-18.675` | `4.734` |
| `40` | `end_then_start` | `-22.755` | `8.814` |
| `50` | `end_then_start` | `-13.920` | `-0.021` |
| `60` | `end_then_start` | `-17.571` | `3.630` |

## Decision

`WEAK_V5_ENDPOINT_CASCADE_FULLFIT_ONLY`: full-fit cost falls, but prefix holdout is not stable enough to promote v6.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
