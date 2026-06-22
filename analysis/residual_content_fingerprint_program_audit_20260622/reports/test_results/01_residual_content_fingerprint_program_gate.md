# Residual Content-Fingerprint Program Gate

Classification: `residual_content_fingerprint_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- V6 fallback rows tested: `90`.
- Best policy: `prefix_1`.
- Best unique-match events: `0`.
- Best delta vs copy-hint: `245.804` bits.
- Prefix positive splits: `0/5`.
- Family positive splits: `0`.

## Policy Scoreboard

| Policy | Unique | Avg matches | Coded bits | Delta |
| --- | ---: | ---: | ---: | ---: |
| `prefix_1` | `0` | `340.033` | `1025.375` | `245.804` |
| `suffix_1` | `0` | `353.722` | `1032.094` | `252.523` |
| `edge_2` | `1` | `38.856` | `1034.555` | `254.984` |
| `suffix_2` | `0` | `41.600` | `1037.890` | `258.319` |
| `prefix_2` | `0` | `50.800` | `1054.793` | `275.222` |
| `edge_3` | `10` | `6.456` | `1093.976` | `314.405` |
| `suffix_3` | `6` | `13.633` | `1180.170` | `400.599` |
| `prefix_3` | `2` | `18.389` | `1193.972` | `414.401` |
| `edge_4` | `56` | `1.656` | `1245.879` | `466.308` |
| `prefix_4` | `12` | `9.400` | `1396.898` | `617.327` |
| `suffix_4` | `13` | `7.533` | `1397.675` | `618.104` |
| `edge_5` | `74` | `1.233` | `1517.266` | `737.695` |
| `edge_6` | `84` | `1.078` | `1791.045` | `1011.474` |
| `edge_8` | `90` | `1.000` | `2329.257` | `1549.686` |

## Prefix Holdout

| Cutoff | Selected | Test rows | Unique | Test delta |
| ---: | --- | ---: | ---: | ---: |
| `20` | `edge_2` | `63` | `0` | `189.231` |
| `30` | `prefix_1` | `52` | `0` | `144.356` |
| `40` | `prefix_1` | `38` | `0` | `104.978` |
| `50` | `prefix_1` | `23` | `0` | `61.629` |
| `60` | `prefix_1` | `7` | `0` | `18.711` |

## Random-Content Control

- Observed delta: `245.804`.
- Random p05/p50/p95 delta: `241.635` / `248.687` / `255.289`.
- Observed unique matches: `0`.
- Random p05/p50/p95 unique: `0` / `0` / `0`.
- Beats p05 delta: `False`.

## Decision

`residual_content_fingerprint_program_not_promoted`: paid content fingerprints do not replace the remaining v6 fallback copy-hint tape under controls.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
