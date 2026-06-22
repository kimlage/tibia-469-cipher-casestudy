# Innovation Tape Replay Gate

Classification: `innovation_tape_replay_not_promoted`
Translation delta: `NONE`

## Purpose

Test whether the canonical literal payload can be treated as one external
innovation tape consumed by an online copy transducer, instead of as
operation-local literal payload attached to a fixed skeleton.

## Summary

- Literal tape digits: `266`.
- Literal tape chunks: `53`.
- Thresholds tested: `[5, 8, 12, 20]`.
- Best threshold: `5`.
- Best exact books: `22/60`.
- Best exact nontrivial books: `12`.
- Best tape digits consumed: `44/266`.
- Best cutpoint hits: `40/201`.
- Best source+length hits: `47/208`.
- Best shuffled-tape exact-book p95: `23.0`.
- Best blind replay exact books: `0`.
- Promotes innovation tape replay: `False`.

The canonical literal payload can be treated as a single innovation tape and replayed with online copy policies. The target-conditioned layer is an upper bound because it asks whether candidate copies match the known target; blind replay is the closed-loop control.

## Target-Conditioned Rows

| Threshold | Exact books | Nontrivial exact | Tape used | Cutpoints | Source+length | Shuffle p95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `5` | `22/60` | `12` | `44/266` | `40/201` | `47/208` | `23.0` |
| `8` | `17/60` | `8` | `56/266` | `30/201` | `41/208` | `17.0` |
| `12` | `16/60` | `7` | `51/266` | `17/201` | `30/208` | `16.0` |
| `20` | `14/60` | `5` | `51/266` | `11/201` | `23/208` | `14.0` |

## Blind Rows

| Threshold | Exact books | Mean prefix fraction | Tape used |
| ---: | ---: | ---: | ---: |
| `5` | `0/60` | `0.000950` | `0/266` |
| `8` | `0/60` | `0.000950` | `0/266` |
| `12` | `0/60` | `0.000950` | `36/266` |
| `20` | `0/60` | `0.000950` | `83/266` |

## Decision

- The target-conditioned layer is an upper bound, not a closed-loop generator.
- Blind replay is the closed-loop control.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
