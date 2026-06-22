# Seed Bootstrap Transducer Program Gate

Classification: `seed_bootstrap_transducer_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- Seed digits: `1696`.
- Literal tape digits from surface parse: `361`.
- Best policy: context `4`, copy_len `4`, source `latest`.
- Exact prefix without correction: `55`.
- Exact seed books without correction: `0/10`.
- Correction digits: `1641`.
- Corrected bits: `6656.992`.
- Delta vs raw seed: `1023.002`.

## Policy Scoreboard

| ctx | copy_len | source | prefix | exact books | correction | delta |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| `4` | `4` | `latest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `4` | `earliest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `5` | `latest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `5` | `earliest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `6` | `latest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `6` | `earliest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `8` | `latest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `8` | `earliest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `10` | `latest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `10` | `earliest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `12` | `latest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `12` | `earliest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `16` | `latest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `16` | `earliest` | `55` | `0` | `1641` | `1023.002` |
| `4` | `24` | `latest` | `55` | `0` | `1641` | `1023.002` |

## Shuffled Literal-Tape Control

- Observed exact prefix: `55`.
- Shuffled p05/p50/p95 exact prefix: `0` / `0` / `1`.
- Observed delta: `1023.002`.
- Shuffled p05/p50/p95 delta: `1202.386` / `1205.708` / `1205.708`.

## Decision

`seed_bootstrap_transducer_not_promoted`: the target-free policies do not generate enough of the seed stream to reduce the raw seed payload after corrections.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
