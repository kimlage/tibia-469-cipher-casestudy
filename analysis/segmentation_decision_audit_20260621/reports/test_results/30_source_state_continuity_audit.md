# Source State Continuity Audit

Classification: `source_state_continuity_policy_rejected`
Translation delta: `NONE`

## Purpose

Gate 30 tests whether the remaining branch choices are explained by continuity
with the previous copy in the already accepted book-local prefix path. The
candidate features are previous source, previous source end, previous copy
length, and proximity to those values.

This is a structural parser test, not a bit sweep and not a row0-origin test.
It does not use the stable branch as a feature.

## Summary

- Decisions: `234`.
- Residual first-drift decisions: `10`.
- Clean controls: `224`.
- Decisions with previous-copy state: `162`.
- Residual decisions with previous-copy state:
  `6/10`.
- Source-state policies tested: `7`.
- Active baseline: `224/234`,
  residual `0/10`,
  clean false changes `0`.
- Best source-state policy: `min_source_delta`.
- Best source-state result: `217/234`,
  eligible `152/162`,
  residual `6/10`,
  eligible residual
  `3/6`,
  clean false changes `13`.

## Full-Fit Policies

| policy | total hits | eligible hits | residual hits | eligible residual hits | clean false changes | residual misses |
| --- | --- | --- | --- | --- | --- | --- |
| prefer_active_control | 224/234 | 156/162 | 0/10 | 0/6 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| min_source_delta | 217/234 | 152/162 | 6/10 | 3/6 | 13 | [14, 16, 55, 57] |
| min_source_to_prev_end_delta | 217/234 | 152/162 | 6/10 | 3/6 | 13 | [14, 16, 55, 57] |
| prefer_same_source | 217/234 | 152/162 | 6/10 | 3/6 | 13 | [14, 16, 55, 57] |
| prefer_same_source_end | 217/234 | 152/162 | 6/10 | 3/6 | 13 | [14, 16, 55, 57] |
| prefer_source_at_prev_end | 217/234 | 152/162 | 6/10 | 3/6 | 13 | [14, 16, 55, 57] |
| min_source_end_delta | 156/234 | 91/162 | 6/10 | 3/6 | 74 | [14, 16, 55, 57] |
| min_length_delta_after_copy | 155/234 | 90/162 | 5/10 | 2/6 | 74 | [14, 16, 20, 55, 57] |

## Prefix/Holdout

| cutoff | selected policy | train hits | test hits | test residual hits | test eligible residual hits | test clean false changes | matches oracle |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | min_source_delta | 64/71 | 153/163 | 6/8 | 3/5 | 8 | True |
| 30 | min_source_delta | 96/104 | 121/130 | 3/5 | 2/4 | 7 | True |
| 40 | min_source_delta | 136/146 | 81/88 | 1/3 | 1/3 | 5 | True |
| 50 | min_source_delta | 172/184 | 45/50 | 0/2 | 0/2 | 3 | True |
| 60 | min_source_delta | 198/214 | 19/20 | 0/0 | 0/0 | 1 | True |

## Randomized Feature Control

- Controls: `50`.
- Total-hit range under per-decision shuffled source-state features:
  `62..88`.
- Median total hits under controls: `74`.
- Max residual hits under controls: `2`.
- Minimum clean false changes under controls: `136`.
- `p(total_hits >= real_best)`: `0.019608`.
- `p(residual_hits >= real_best)`: `0.019608`.

## Decision

- Promotes source-state continuity parser policy:
  `False`.
- Prequential zero-clean-false-change cells:
  `0/5`.
- Prequential cover-all-test-residual cells:
  `1/5`.
- The test is book-local: it does not claim a cross-book hidden source state.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
