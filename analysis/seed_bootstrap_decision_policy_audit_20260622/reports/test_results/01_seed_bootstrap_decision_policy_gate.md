# Seed Bootstrap Decision-Policy Gate

Classification: `seed_bootstrap_decision_policy_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- Rows: `473`.
- Action counts: `{'literal': 361, 'copy': 112}`.
- Mean test accuracy: `0.446`.
- Shuffled-label p95 mean accuracy: `0.847`.
- Beats shuffled p95: `False`.

## Prefix Holdout

| Cutoff book | Rule | Train acc | Test acc | Test recall | Test precision |
| ---: | --- | ---: | ---: | ---: | ---: |
| `3` | `ctx5_repeat_literal_in_next` | `0.885` | `0.618` | `0.090` | `1.000` |
| `5` | `ctx5_repeat_literal_in_next` | `0.842` | `0.584` | `0.096` | `1.000` |
| `7` | `ctx5_repeat_literal_in_next` | `0.806` | `0.582` | `0.080` | `1.000` |
| `9` | `ctx5_repeat_literal_in_next` | `0.790` | `0.000` | `0.000` | `0.000` |

## Decision

`seed_bootstrap_decision_policy_not_promoted`: simple visible-state rules do not promote as a bootstrap decision policy.

This remains teacher-forced on the true prefix path; it is not an executable seed generator.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
