# Global Source State Continuity Audit

Classification: `global_source_state_continuity_policy_rejected`
Translation delta: `NONE`

## Purpose

Gate 31 tests the carryover version of the source-state hypothesis. Unlike gate
30, the previous-copy state is not reset at each book. It is built by replaying
the full stable projection before the current decision, then candidate branches
are scored by source/source-end/length continuity.

This is an intentionally favorable upper-bound test for the hypothesis: the
history state is granted from the stable projection. It is not a source-free
generator and not a row0-origin test.

## Summary

- Decisions: `234`.
- Residual first-drift decisions: `10`.
- Clean controls: `224`.
- Decisions with previous-copy state: `232`.
- Residual decisions with previous-copy state:
  `10/10`.
- Source-state policies tested: `7`.
- Active baseline: `224/234`,
  residual `0/10`,
  clean false changes `0`.
- Best global source-state policy: `min_source_delta`.
- Best result: `217/234`,
  eligible `216/232`,
  residual `6/10`,
  eligible residual
  `6/10`,
  clean false changes `13`.

## Full-Fit Policies

| policy | total hits | eligible hits | residual hits | eligible residual hits | clean false changes | residual misses |
| --- | --- | --- | --- | --- | --- | --- |
| prefer_active_control | 224/234 | 222/232 | 0/10 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| min_source_delta | 217/234 | 216/232 | 6/10 | 6/10 | 13 | [14, 16, 55, 57] |
| min_source_to_prev_end_delta | 217/234 | 216/232 | 6/10 | 6/10 | 13 | [14, 16, 55, 57] |
| prefer_same_source | 217/234 | 216/232 | 6/10 | 6/10 | 13 | [14, 16, 55, 57] |
| prefer_same_source_end | 217/234 | 216/232 | 6/10 | 6/10 | 13 | [14, 16, 55, 57] |
| prefer_source_at_prev_end | 217/234 | 216/232 | 6/10 | 6/10 | 13 | [14, 16, 55, 57] |
| min_source_end_delta | 126/234 | 125/232 | 5/10 | 5/10 | 103 | [14, 16, 26, 55, 57] |
| min_length_delta_after_copy | 126/234 | 125/232 | 4/10 | 4/10 | 102 | [14, 16, 20, 21, 55, 57] |

## Prefix/Holdout

| cutoff | selected policy | train hits | test hits | test residual hits | test eligible residual hits | test clean false changes | matches oracle |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | min_source_delta | 64/71 | 153/163 | 6/8 | 6/8 | 8 | True |
| 30 | min_source_delta | 96/104 | 121/130 | 3/5 | 3/5 | 7 | True |
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

- Promotes global source-state continuity parser policy:
  `False`.
- Prequential zero-clean-false-change cells:
  `0/5`.
- Prequential cover-all-test-residual cells:
  `1/5`.
- The test grants stable-projection history, so any positive result would still
  need a source-free way to obtain that state.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
