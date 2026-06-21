# Trajectory Neighbor Parser Audit

Classification: `trajectory_neighbor_parser_rejected`
Translation delta: `NONE`

## Purpose

Gate 38 tests whether the residual first-drift choices can be explained by
nearest cumulative parser-state trajectories from books already parsed exactly.
This is a richer path/state shortcut than local branch predicates or exact
template reuse.

It does not search row0, plaintext, or semantics.

## Summary

- Active classifier: `if_peak_len_le5_then_skip_to_next_peak_ge5`.
- Exact parser books: `50`.
- Residual parser books: `10`.
- Families tested: `['trajectory', 'context', 'combined']`.
- k values tested: `[1, 3, 5]`.
- Best policy: `trajectory`, k=`1`.
- Best residual hits: `0/10`.
- Prequential residual cells fully hit:
  `0/4`.
- Shuffle control `p_ge_observed`: `1.0000`.
- Promotes parser rule: `False`.

## Scoreboard

| family | k | hits | residual queries |
| --- | --- | --- | --- |
| combined | 1 | 0 | 10 |
| combined | 3 | 0 | 10 |
| combined | 5 | 0 | 10 |
| context | 1 | 0 | 10 |
| context | 3 | 0 | 10 |
| context | 5 | 0 | 10 |
| trajectory | 1 | 0 | 10 |
| trajectory | 3 | 0 | 10 |
| trajectory | 5 | 0 | 10 |

## Prequential Rows For Best Policy

| cutoff | test residuals | hits |
| --- | --- | --- |
| 20 | 8 | 0 |
| 30 | 5 | 0 |
| 40 | 3 | 0 |
| 50 | 2 | 0 |
| 60 | 0 | 0 |

## Shuffle Control For Best Policy

- Observed hits: `0`.
- Trials: `400`.
- Shuffle mean: `0.190`.
- Shuffle max: `2`.
- `p_ge_observed`: `1.0000`.

## Best Policy Residual Rows

| book | op | drift class | active label | stable label | predicted label | nearest distance | hit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | 0 | literal_understop | ('literal', 27) | ('literal', 39) | ('literal', 5) | 0.0 | False |
| 16 | 9 | copy_started_inside_stable_literal | ('copy', 8) | ('literal', 1) | ('copy', 72) | 11.0 | False |
| 20 | 2 | internal_copy_missed_as_literal | ('literal', 3) | ('copy', 10) | ('copy', 37) | 4.0 | False |
| 21 | 0 | book_start_copy_missed_as_literal | ('literal', 7) | ('copy', 9) | ('literal', 5) | 0.0 | False |
| 26 | 0 | book_start_copy_missed_as_literal | ('literal', 1) | ('copy', 11) | ('literal', 5) | 0.0 | False |
| 34 | 7 | internal_copy_missed_as_literal | ('literal', 5) | ('copy', 5) | ('copy', 13) | 15.0 | False |
| 39 | 0 | book_start_copy_missed_as_literal | ('literal', 7) | ('copy', 5) | ('literal', 5) | 0.0 | False |
| 45 | 1 | internal_copy_missed_as_literal | ('literal', 1) | ('copy', 8) | ('copy', 42) | 14.0 | False |
| 55 | 2 | copy_length_drift_same_source | ('copy', 45) | ('copy', 44) | ('copy', 12) | 11.0 | False |
| 57 | 2 | literal_understop | ('literal', 17) | ('literal', 28) | ('copy', 45) | 17.0 | False |

## Decision

Trajectory-neighbor parsing is not promoted. The best nearest-trajectory policy
does not cover the residual first-drift choices under prefix/holdout and
therefore does not replace the retained segmentation decisions.

The remaining blocker is still a richer latent path/state mechanism or a
source-free target digit account.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
