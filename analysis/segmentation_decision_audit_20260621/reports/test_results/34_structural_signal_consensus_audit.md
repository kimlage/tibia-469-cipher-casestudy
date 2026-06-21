# Structural Signal Consensus Audit

Classification: `structural_signal_consensus_policy_rejected`
Translation delta: `NONE`

## Purpose

Gate 34 tests whether weak structural signals become useful only when they
agree. Four families vote on the current candidate branches:

- source-state continuity;
- phase/grid alignment;
- near-future copy opportunity;
- recurrent target boundary.

The consensus rule keeps the active branch unless at least `k` families choose
the same non-active branch. This is a parser decision test, not a bit sweep.

## Summary

- Decisions: `234`.
- Residual first-drift decisions: `10`.
- Clean controls: `224`.
- Signal families: `4`.
- Consensus configs tested: `48`.
- Active baseline: `224/234`,
  residual `0/10`,
  clean false changes `0`.
- Best consensus policy: `k3:source=global_min_source_delta:phase=source_mod0_10:future=max_copy_positions:boundary=max_left_right_r8`.
- Best consensus result: `224/234`,
  residual `0/10`,
  clean false changes `0`.

## Full-Fit Policies

| policy | total hits | residual hits | clean false changes | residual misses |
| --- | --- | --- | --- | --- |
| prefer_active_control | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| k3:source=global_min_source_delta:phase=source_mod0_10:future=max_copy_positions:boundary=max_left_right_r8 | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| k3:source=global_min_source_delta:phase=source_mod0_10:future=max_copy_positions:boundary=multi_radius_sum | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| k3:source=global_min_source_delta:phase=source_mod0_10:future=max_window_best_len:boundary=max_left_right_r8 | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| k3:source=global_min_source_delta:phase=source_mod0_10:future=max_window_best_len:boundary=multi_radius_sum | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| k3:source=global_min_source_delta:phase=source_mod0_20:future=max_copy_positions:boundary=max_left_right_r8 | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| k3:source=global_min_source_delta:phase=source_mod0_20:future=max_copy_positions:boundary=multi_radius_sum | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| k3:source=global_min_source_delta:phase=source_mod0_20:future=max_window_best_len:boundary=max_left_right_r8 | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| k3:source=global_min_source_delta:phase=source_mod0_20:future=max_window_best_len:boundary=multi_radius_sum | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| k3:source=local_min_source_delta:phase=source_mod0_10:future=max_copy_positions:boundary=max_left_right_r8 | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |

## Prefix/Holdout

| cutoff | selected policy | train hits | test hits | test residual hits | test clean false changes | matches oracle |
| --- | --- | --- | --- | --- | --- | --- |
| 20 | k2:source=global_min_source_delta:phase=source_mod0_10:future=max_copy_positions:boundary=multi_radius_sum | 69/71 | 150/163 | 1/8 | 6 | False |
| 30 | k3:source=global_min_source_delta:phase=source_mod0_10:future=max_copy_positions:boundary=max_left_right_r8 | 99/104 | 125/130 | 0/5 | 0 | True |
| 40 | k3:source=global_min_source_delta:phase=source_mod0_10:future=max_copy_positions:boundary=max_left_right_r8 | 139/146 | 85/88 | 0/3 | 0 | True |
| 50 | k3:source=global_min_source_delta:phase=source_mod0_10:future=max_copy_positions:boundary=max_left_right_r8 | 176/184 | 48/50 | 0/2 | 0 | True |
| 60 | k3:source=global_min_source_delta:phase=source_mod0_10:future=max_copy_positions:boundary=max_left_right_r8 | 204/214 | 20/20 | 0/0 | 0 | True |

## Shuffled Family Control

- Controls: `100`.
- Total-hit range under shuffled family votes:
  `224..224`.
- Median total hits under controls: `224`.
- Max residual hits under controls: `0`.
- Minimum clean false changes under controls: `0`.
- `p(total_hits >= real_best)`: `1.000000`.
- `p(residual_hits >= real_best)`: `1.000000`.

## Decision

- Promotes structural-signal consensus parser policy:
  `False`.
- Prequential zero-clean-false-change cells:
  `4/5`.
- Prequential cover-all-test-residual cells:
  `1/5`.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
