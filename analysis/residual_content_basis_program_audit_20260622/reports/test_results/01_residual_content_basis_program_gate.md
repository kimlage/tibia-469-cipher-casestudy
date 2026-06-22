# Residual Content-Basis Program Gate

Classification: `residual_content_basis_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- V6 fallback rows tested: `90`.
- Best mode: `exact`.
- Best hits: `1/90`.
- Best delta vs copy-hint: `3.419` bits.
- Prefix positive splits: `0/5`.
- Family positive splits: `0`.

## Full Fit

| Mode | Hits | Misses | Basis | Coded bits | Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `exact` | `1` | `89` | `89` | `782.990` | `3.419` |
| `substring` | `38` | `52` | `52` | `937.541` | `157.970` |

## Prefix Holdout: `exact`

| Cutoff | Train basis | Test rows | Frozen hits | Frozen delta | Online hits | Online delta |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `27` | `63` | `0` | `1.585` | `1` | `3.419` |
| `30` | `38` | `52` | `0` | `1.585` | `1` | `3.419` |
| `40` | `52` | `38` | `0` | `1.585` | `1` | `3.419` |
| `50` | `67` | `23` | `1` | `3.127` | `1` | `3.419` |
| `60` | `82` | `7` | `0` | `1.585` | `0` | `1.585` |

## Controls

- Order-shuffle observed delta: `3.419`; p05/p50/p95: `-4.119` / `-2.716` / `3.436`.
- Content-shuffle observed delta: `3.419`; p05/p50/p95: `-5.026` / `-1.751` / `1.459`.

## Decision

`residual_content_basis_program_not_promoted`: online content-basis reuse does not replace the remaining v6 fallback copy-hint tape under paid controls.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
