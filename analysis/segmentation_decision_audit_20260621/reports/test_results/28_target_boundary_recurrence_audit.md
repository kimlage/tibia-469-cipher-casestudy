# Target Boundary Recurrence Audit

Classification: `target_boundary_recurrence_policy_rejected`
Translation delta: `NONE`

## Purpose

Gate 28 tests one of the original structural segmentation hypotheses: branch
choices might preserve recurrent target-side chunk boundaries. Each candidate
branch defines a next boundary at `target_start + length`; policies choose the
branch whose boundary has the most recurrent raw digit context.

Full-fit rows are optimistic diagnostics. Prefix/holdout rows rebuild recurrence
counts from prefix books only before scoring future books.

## Summary

- Decisions: `234`.
- Residual first-drift decisions: `10`.
- Clean controls: `224`.
- Recurrence policies tested: `11`.
- Radii: `[2, 3, 4, 6, 8]`.
- Active baseline: `224/234`,
  residual `0/10`,
  clean false changes `0`.
- Best recurrence policy: `max_left_right_r8`.
- Best recurrence result: `31/234`,
  residual `1/10`,
  clean false changes `194`.

## Full-Fit Policies

| policy | total hits | residual hits | clean false changes | residual misses |
| --- | --- | --- | --- | --- |
| prefer_active_control | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| max_left_right_r8 | 31/234 | 1/10 | 194 | [14, 20, 21, 26, 34, 39, 45, 55, 57] |
| max_left_right_r6 | 22/234 | 0/10 | 202 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| max_around_r8 | 15/234 | 1/10 | 210 | [14, 20, 21, 26, 34, 39, 45, 55, 57] |
| max_left_right_r2 | 13/234 | 1/10 | 212 | [14, 16, 20, 21, 26, 34, 39, 45, 55] |
| max_left_right_r4 | 12/234 | 0/10 | 212 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| max_left_right_r3 | 9/234 | 0/10 | 215 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| max_around_r6 | 8/234 | 0/10 | 216 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |

## Prefix/Holdout

| cutoff | selected policy | train hits | test hits | test residual hits | test clean false changes | matches oracle |
| --- | --- | --- | --- | --- | --- | --- |
| 20 | max_left_right_r6 | 13/71 | 13/163 | 0/8 | 142 | False |
| 30 | max_left_right_r6 | 16/104 | 9/130 | 0/5 | 116 | False |
| 40 | max_left_right_r8 | 22/146 | 12/88 | 0/3 | 73 | True |
| 50 | max_left_right_r8 | 29/184 | 2/50 | 0/2 | 46 | False |
| 60 | max_left_right_r8 | 32/214 | 0/20 | 0/0 | 20 | False |

## Random Boundary Control

- Controls: `200`.
- Total-hit range under random branch boundaries:
  `33..52`.
- Median total hits under controls: `41`.
- Max residual hits under controls: `3`.
- Minimum clean false changes under controls: `173`.
- `p(total_hits >= real_best)`: `1.000000`.
- `p(residual_hits >= real_best)`: `0.442786`.

## Decision

- Promotes target-boundary recurrence parser policy:
  `False`.
- Prequential zero-clean-false-change cells:
  `0/5`.
- Prequential cover-all-test-residual cells:
  `1/5`.
- This gate tests a structural boundary-reuse idea, not a bit sweep.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
