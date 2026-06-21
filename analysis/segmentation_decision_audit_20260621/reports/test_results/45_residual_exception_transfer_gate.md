# Residual Exception Transfer Gate

Classification: `residual_exception_transfer_rejected`
Translation delta: `NONE`

## Purpose

Gate 45 asks whether the residual corrections form a reusable exception
family. It trains only on other residual corrections and predicts each held-out
residual from observable active-parser features, using stable labels only as
leave-one-residual-out training/evaluation labels.

## Summary

- Residual decisions tested: `10`.
- Families tested: `6`.
- k values tested: `[1, 3, 5]`.
- Best family: `context_prev2`.
- Best k: `1`.
- Best hits: `0/10`.
- Best unsupported residuals: `0`.
- Prequential cells with held-out hit: `0/4`.
- Shuffle p_ge_observed: `1.0000`.
- Promotes residual exception transfer: `False`.

## Scoreboard

| family | k | hits | query count | unsupported |
| --- | --- | --- | --- | --- |
| active_shape | 1 | 0 | 10 | 0 |
| active_shape_prev1 | 1 | 0 | 10 | 0 |
| coarse | 1 | 0 | 10 | 0 |
| context | 1 | 0 | 10 | 0 |
| context_prev1 | 1 | 0 | 10 | 0 |
| context_prev2 | 1 | 0 | 10 | 0 |
| active_shape | 3 | 0 | 10 | 0 |
| active_shape_prev1 | 3 | 0 | 10 | 0 |
| coarse | 3 | 0 | 10 | 0 |
| context | 3 | 0 | 10 | 0 |
| context_prev1 | 3 | 0 | 10 | 0 |
| context_prev2 | 3 | 0 | 10 | 0 |
| active_shape | 5 | 0 | 10 | 0 |
| active_shape_prev1 | 5 | 0 | 10 | 0 |
| coarse | 5 | 0 | 10 | 0 |
| context | 5 | 0 | 10 | 0 |
| context_prev1 | 5 | 0 | 10 | 0 |
| context_prev2 | 5 | 0 | 10 | 0 |

## Best-Family Rows

| book | op | active label | stable label | predicted label | hit | nearest neighbors |
| --- | --- | --- | --- | --- | --- | --- |
| 14 | 0 | ('literal', 27) | ('literal', 39) | ('copy', 5) | False | [{'book': 39, 'stable_label': ('copy', 5), 'distance': 18.0}] |
| 16 | 9 | ('copy', 8) | ('literal', 1) | ('copy', 5) | False | [{'book': 34, 'stable_label': ('copy', 5), 'distance': 36.0}] |
| 20 | 2 | ('literal', 3) | ('copy', 10) | ('copy', 5) | False | [{'book': 34, 'stable_label': ('copy', 5), 'distance': 27.0}] |
| 21 | 0 | ('literal', 7) | ('copy', 9) | ('copy', 5) | False | [{'book': 39, 'stable_label': ('copy', 5), 'distance': 4.0}] |
| 26 | 0 | ('literal', 1) | ('copy', 11) | ('copy', 9) | False | [{'book': 21, 'stable_label': ('copy', 9), 'distance': 16.0}] |
| 34 | 7 | ('literal', 5) | ('copy', 5) | ('copy', 10) | False | [{'book': 20, 'stable_label': ('copy', 10), 'distance': 27.0}] |
| 39 | 0 | ('literal', 7) | ('copy', 5) | ('copy', 9) | False | [{'book': 21, 'stable_label': ('copy', 9), 'distance': 4.0}] |
| 45 | 1 | ('literal', 1) | ('copy', 8) | ('copy', 44) | False | [{'book': 55, 'stable_label': ('copy', 44), 'distance': 42.0}] |
| 55 | 2 | ('copy', 45) | ('copy', 44) | ('copy', 8) | False | [{'book': 45, 'stable_label': ('copy', 8), 'distance': 42.0}] |
| 57 | 2 | ('literal', 17) | ('literal', 28) | ('copy', 5) | False | [{'book': 34, 'stable_label': ('copy', 5), 'distance': 53.0}] |

## Prequential Rows

| cutoff | test residuals | hits | unsupported |
| --- | --- | --- | --- |
| 20 | 8 | 0 | 0 |
| 30 | 5 | 0 | 0 |
| 40 | 3 | 0 | 0 |
| 50 | 2 | 0 | 0 |
| 60 | 0 | 0 | 0 |

## Shuffle Control

- Trials: `400`.
- Shuffle min/mean/max hits: `0` / `0.225` / `2`.
- Shuffle >= observed: `400`.
- p_ge_observed: `1.0000`.

## Decision

No residual exception-transfer rule is promoted. The residual corrections do
not predict each other under the tested observable feature families. This
makes a compact reusable residual-exception class unlikely under current
evidence; the remaining explanation is still a richer latent state or an
external/source-free target stream account.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
