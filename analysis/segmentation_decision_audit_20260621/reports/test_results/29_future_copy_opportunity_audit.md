# Future Copy Opportunity Audit

Classification: `future_copy_opportunity_policy_rejected`
Translation delta: `NONE`

## Purpose

Gate 29 tests whether residual branch choices are explained by preserving or
creating near-future copy opportunities. Each branch boundary is scored by copy
availability at the boundary and within the next `12` target
positions.

This is a structural parser test, not a bit sweep. It asks whether choosing the
stable branch can be inferred from the copy-opportunity landscape without using
the stable projection as a feature.

## Summary

- Decisions: `234`.
- Residual first-drift decisions: `10`.
- Clean controls: `224`.
- Opportunity policies tested: `5`.
- Active baseline: `224/234`,
  residual `0/10`,
  clean false changes `0`.
- Best opportunity policy: `max_copy_positions`.
- Best opportunity result: `96/234`,
  residual `2/10`,
  clean false changes `130`.

## Full-Fit Policies

| policy | total hits | residual hits | clean false changes | residual misses |
| --- | --- | --- | --- | --- |
| prefer_active_control | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| max_copy_positions | 96/234 | 2/10 | 130 | [14, 20, 21, 26, 34, 39, 45, 55] |
| max_window_sum_len | 78/234 | 2/10 | 148 | [14, 20, 21, 26, 34, 39, 45, 55] |
| max_window_best_len | 76/234 | 2/10 | 150 | [14, 20, 21, 26, 34, 39, 45, 55] |
| max_immediate_len | 66/234 | 1/10 | 159 | [14, 20, 21, 26, 34, 39, 45, 55, 57] |
| min_first_available_offset | 52/234 | 0/10 | 172 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |

## Prefix/Holdout

| cutoff | selected policy | train hits | test hits | test residual hits | test clean false changes | matches oracle |
| --- | --- | --- | --- | --- | --- | --- |
| 20 | max_copy_positions | 25/71 | 63/163 | 0/8 | 92 | True |
| 30 | max_copy_positions | 36/104 | 57/130 | 0/5 | 68 | True |
| 40 | max_copy_positions | 56/146 | 40/88 | 1/3 | 46 | True |
| 50 | max_copy_positions | 74/184 | 22/50 | 1/2 | 27 | True |
| 60 | max_copy_positions | 88/214 | 8/20 | 0/0 | 12 | False |

## Randomized Feature Control

- Controls: `30`.
- Total-hit range under per-decision shuffled opportunity features:
  `121..150`.
- Median total hits under controls: `132`.
- Max residual hits under controls: `1`.
- Minimum clean false changes under controls: `75`.
- `p(total_hits >= real_best)`: `1.000000`.
- `p(residual_hits >= real_best)`: `0.032258`.

## Decision

- Promotes future-copy-opportunity parser policy:
  `False`.
- Prequential zero-clean-false-change cells:
  `0/5`.
- Prequential cover-all-test-residual cells:
  `1/5`.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
