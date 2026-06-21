# Context Nearest Branch Audit

Classification: `context_nearest_branch_policy_rejected`
Translation delta: `NONE`

## Purpose

Gate 33 tests whether stable branch choices recur with raw digit context. For
each decision, the policy finds the nearest prior/other-book decision by
target-context Hamming distance and applies that training decision's stable
branch action class to the current candidate branches.

This is a predictive parser test, not a bit sweep. It uses stable branch labels
only in training rows, never as a current-decision feature.

## Summary

- Decisions: `234`.
- Residual first-drift decisions: `10`.
- Clean controls: `224`.
- Context windows: `[(4, 8), (8, 8), (8, 12), (12, 12), (16, 16)]`.
- Signature modes: `['action_class', 'action_type_length', 'action_label_length']`.
- Nearest-context policies tested: `15`.
- Active baseline: `224/234`,
  residual `0/10`,
  clean false changes `0`.
- Best leave-one-book policy: `nearest_context_l8_r8_action_class`.
- Best leave-one-book result:
  `216/234`,
  residual `0/10`,
  clean false changes `8`.

## Leave-One-Book Scoreboard

| policy | total hits | residual hits | clean false changes | residual misses |
| --- | --- | --- | --- | --- |
| prefer_active_control | 224/234 | 0/10 | 0 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| nearest_context_l8_r8_action_class | 216/234 | 0/10 | 8 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| nearest_context_l8_r8_action_label_length | 216/234 | 0/10 | 8 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| nearest_context_l8_r8_action_type_length | 216/234 | 0/10 | 8 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| nearest_context_l16_r16_action_class | 215/234 | 0/10 | 9 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| nearest_context_l16_r16_action_label_length | 215/234 | 0/10 | 9 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| nearest_context_l16_r16_action_type_length | 215/234 | 0/10 | 9 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| nearest_context_l8_r12_action_class | 215/234 | 0/10 | 9 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| nearest_context_l8_r12_action_label_length | 215/234 | 0/10 | 9 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |
| nearest_context_l8_r12_action_type_length | 215/234 | 0/10 | 9 | [14, 16, 20, 21, 26, 34, 39, 45, 55, 57] |

## Prefix/Holdout

| cutoff | selected policy | train hits | test hits | test residual hits | test clean false changes | matches oracle |
| --- | --- | --- | --- | --- | --- | --- |
| 20 | nearest_context_l4_r8_action_class | 65/71 | 149/163 | 0/8 | 6 | False |
| 30 | nearest_context_l4_r8_action_class | 92/104 | 119/130 | 0/5 | 6 | False |
| 40 | nearest_context_l4_r8_action_class | 131/146 | 80/88 | 0/3 | 5 | False |
| 50 | nearest_context_l16_r16_action_class | 168/184 | 47/50 | 0/2 | 1 | False |
| 60 | nearest_context_l16_r16_action_class | 196/214 | 19/20 | 0/0 | 1 | False |

## Shuffled Label Control

- Controls: `30`.
- Total-hit range under shuffled training action labels:
  `216..223`.
- Median total hits under controls: `220`.
- Max residual hits under controls: `1`.
- Minimum clean false changes under controls: `1`.
- `p(total_hits >= real_best)`: `1.000000`.
- `p(residual_hits >= real_best)`: `1.000000`.

## Decision

- Promotes context-nearest parser policy:
  `False`.
- Prequential zero-clean-false-change cells:
  `0/5`.
- Prequential cover-all-test-residual cells:
  `1/5`.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
