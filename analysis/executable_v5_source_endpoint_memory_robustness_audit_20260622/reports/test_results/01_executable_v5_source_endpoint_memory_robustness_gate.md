# Executable v5 Source-Endpoint Memory Robustness Gate

Classification: `PROMOTED_EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_ROBUST`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- Full delta before declaration vs v4: `-11.390`.
- Full delta after declaration vs v4: `-9.805`.
- Note: per-book robustness compares against the v4 residual without recharging the v4 policy declaration.
- Book deltas negative/positive: `13` / `31`.
- Positive suffix splits: `4/5`.
- Total suffix delta vs v4: `-31.764`.
- Control trials per split: `80`.

## Prefix/Suffix Rows

| Cutoff | Train delta | Test delta | Control p05 | Beats p05 |
| ---: | ---: | ---: | ---: | --- |
| `20` | `0.603` | `-11.993` | `-2.123` | `True` |
| `30` | `-5.224` | `-6.167` | `-2.246` | `True` |
| `40` | `-0.349` | `-11.041` | `-6.029` | `True` |
| `50` | `-8.258` | `-3.132` | `-6.741` | `False` |
| `60` | `-11.960` | `0.569` | `-3.258` | `False` |

## Decision

`PROMOTED_EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_ROBUST`.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
