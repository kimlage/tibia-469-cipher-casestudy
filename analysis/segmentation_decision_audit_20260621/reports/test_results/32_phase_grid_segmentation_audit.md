# Phase Grid Segmentation Audit

Classification: `phase_grid_segmentation_policy_rejected`
Translation delta: `NONE`

## Purpose

Gate 32 tests whether residual branch choices are explained by a simple
phase/grid constraint over target boundaries, operation lengths, copy sources,
copy source ends, or source-target phase alignment. Cycles tested:
`[2, 3, 4, 5, 8, 10, 16, 20]`.

This is a structural parser test, not a bit sweep, row0-origin test, plaintext
claim, or semantic read.

## Summary

- Decisions: `234`.
- Residual first-drift decisions: `10`.
- Clean controls: `224`.
- Phase/grid policies tested: `64`.
- Active baseline: `224/234`,
  residual `0/10`,
  clean false changes `0`.
- Best phase/grid policy: `source_mod0_10`.
- Best phase/grid result: `225/234`,
  residual `1/10`,
  clean false changes `0`.

## Full-Fit Policies

| policy | total hits | residual hits | clean false changes | residual misses |
| --- | --- | --- | --- | --- |
| prefer_active_control | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| source_mod0_10 | 225/234 | 1/10 | 0 | [14, 16, 20, 21, 26, 34, 45, 55, 57] |
| source_mod0_20 | 225/234 | 1/10 | 0 | [14, 16, 20, 21, 26, 34, 45, 55, 57] |
| source_end_matches_boundary_phase_10 | 224/234 | 1/10 | 1 | [14, 16, 20, 21, 26, 34, 45, 55, 57] |
| source_end_matches_boundary_phase_20 | 224/234 | 1/10 | 1 | [14, 16, 20, 21, 26, 34, 45, 55, 57] |
| source_end_matches_boundary_phase_8 | 224/234 | 1/10 | 1 | [14, 16, 20, 21, 26, 34, 45, 55, 57] |
| source_matches_target_start_phase_10 | 224/234 | 1/10 | 1 | [14, 16, 20, 21, 26, 34, 45, 55, 57] |
| source_matches_target_start_phase_20 | 224/234 | 1/10 | 1 | [14, 16, 20, 21, 26, 34, 45, 55, 57] |
| source_matches_target_start_phase_8 | 224/234 | 1/10 | 1 | [14, 16, 20, 21, 26, 34, 45, 55, 57] |
| target_start_mod0_10 | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| target_start_mod0_16 | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| target_start_mod0_2 | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |

## Prefix/Holdout

| cutoff | selected policy | train hits | test hits | test residual hits | test clean false changes | matches oracle |
| --- | --- | --- | --- | --- | --- | --- |
| 20 | source_end_matches_boundary_phase_16 | 69/71 | 154/163 | 0/8 | 1 | False |
| 30 | source_end_matches_boundary_phase_16 | 99/104 | 124/130 | 0/5 | 1 | False |
| 40 | source_end_matches_boundary_phase_8 | 140/146 | 84/88 | 0/3 | 1 | False |
| 50 | source_end_matches_boundary_phase_8 | 177/184 | 47/50 | 0/2 | 1 | False |
| 60 | source_mod0_10 | 205/214 | 20/20 | 0/0 | 0 | True |

## Randomized Feature Control

- Controls: `50`.
- Total-hit range under per-decision shuffled phase features:
  `224..224`.
- Median total hits under controls: `224`.
- Max residual hits under controls: `0`.
- Minimum clean false changes under controls: `0`.
- `p(total_hits >= real_best)`: `0.019608`.
- `p(residual_hits >= real_best)`: `0.019608`.

## Decision

- Promotes phase/grid parser policy: `False`.
- Prequential zero-clean-false-change cells:
  `1/5`.
- Prequential cover-all-test-residual cells:
  `1/5`.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
