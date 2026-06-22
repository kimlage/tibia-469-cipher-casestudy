# Executable v3 Source-Boundary Robustness Gate

Classification: `PROMOTED_EXECUTABLE_V3_SOURCE_BOUNDARY_ROBUST`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Does the executable v3 source-boundary reduction survive explicit system/policy declaration cost and prefix-only system selection?

## Summary

- Systems tested: `7`.
- Policies tested: `3`.
- Declaration bits for system+policy: `4.392`.
- Full-fit v3 delta before declaration: `-142.991` bits.
- Full-fit v3 delta after declaration: `-138.598` bits.
- Prefix-selected positive test splits: `5/5`.
- Prefix-selected total test delta: `-226.100` bits.
- Prefix-selected systems: `{'event_plus_surprisal_top20': 4, 'surprisal_top20': 1}`.

## Prefix Selection

| Cutoff | Selected system | Policy | Train delta | Test hits | Test delta |
| ---: | --- | --- | ---: | ---: | ---: |
| `20` | `surprisal_top20` | `long_recent` | `-48.818` | `9` | `-63.144` |
| `30` | `event_plus_surprisal_top20` | `long_recent` | `-71.528` | `9` | `-71.463` |
| `40` | `event_plus_surprisal_top20` | `long_recent` | `-88.794` | `6` | `-54.197` |
| `50` | `event_plus_surprisal_top20` | `long_recent` | `-116.614` | `3` | `-26.377` |
| `60` | `event_plus_surprisal_top20` | `long_recent` | `-132.072` | `1` | `-10.918` |

## Decision

`PROMOTED_EXECUTABLE_V3_SOURCE_BOUNDARY_ROBUST`: the v3 ledger reduction survives declaration cost and prefix-selected systems.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
