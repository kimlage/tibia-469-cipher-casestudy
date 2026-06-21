# Sequential Signature Support Gate

Classification: `sequential_signature_support_rejected`
Translation delta: `NONE`

## Purpose

Gate 56 tests whether the static candidate-signature failure in gate 55 is
only missing a small sequential state. It augments observable candidate
signatures with prior within-book path memory: previous one or two stable/active
operation shapes and prior copy/literal counts.

For residual first-drift decisions, this prior path is observable before the
drift because previous operations match the active parser. The gate does not use
`drift_class`, plaintext, semantics, row0 origin, or future stable labels.

## Summary

- Decisions: `234`.
- Residual decisions: `10`.
- Sequential signature families: `10`.
- Label modes: `3`.
- Best signature: `prev2_stable_x_decision_coarse`.
- Best label mode: `stable_shape_label`.
- Best deterministic residual matches:
  `0/10`.
- Best supported residuals: `0/10`.
- Best status counts: `{'out_of_support': 10}`.
- Static gate-55 best deterministic matches:
  `0/10`.
- Prefix/holdout cells with any deterministic match:
  `0/4`.
- Prefix/holdout cover-all residual cells:
  `0/4`.
- Promotes parser rule: `False`.

## Scoreboard

| signature | label mode | deterministic matches | supported | contradictions | ambiguous with stable | status counts |
| --- | --- | --- | --- | --- | --- | --- |
| prev2_stable_x_decision_coarse | stable_shape_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev2_stable_x_decision_coarse | stable_rank_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev2_stable_x_decision_coarse | stable_action_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev2_stable_x_candidate_length_buckets | stable_shape_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev2_stable_x_candidate_length_buckets | stable_rank_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev2_stable_x_candidate_length_buckets | stable_action_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev2_stable_x_candidate_extrema | stable_shape_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev2_stable_x_candidate_extrema | stable_rank_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev2_stable_x_candidate_extrema | stable_action_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev2_active_x_decision_coarse | stable_shape_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev2_active_x_decision_coarse | stable_rank_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev2_active_x_decision_coarse | stable_action_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev1_stable_x_decision_coarse | stable_shape_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev1_stable_x_decision_coarse | stable_rank_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev1_stable_x_decision_coarse | stable_action_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev1_stable_x_candidate_length_buckets | stable_shape_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev1_stable_x_candidate_length_buckets | stable_rank_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| prev1_stable_x_candidate_length_buckets | stable_action_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |

## Prefix/Holdout For Best Signature

| cutoff | deterministic matches | supported | contradictions | status counts |
| --- | --- | --- | --- | --- |
| 20 | 0/8 | 0 | 0 | {'out_of_support': 8} |
| 30 | 0/5 | 0 | 0 | {'out_of_support': 5} |
| 40 | 0/3 | 0 | 0 | {'out_of_support': 3} |
| 50 | 0/2 | 0 | 0 | {'out_of_support': 2} |
| 60 | 0/0 | 0 | 0 | {} |

## Residual Rows For Best Signature

| book | op | class | active | stable | support | labels | majority | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | 0 | literal_understop | {'type': 'literal', 'target_start': 0, 'length': 27, 'source': None} | {'type': 'literal', 'target_start': 0, 'length': 39, 'source': None} | 0 | 0 | None | out_of_support |
| 16 | 9 | copy_started_inside_stable_literal | {'type': 'copy', 'target_start': 164, 'length': 8, 'source': 473} | {'type': 'literal', 'target_start': 164, 'length': 1, 'source': None} | 0 | 0 | None | out_of_support |
| 20 | 2 | internal_copy_missed_as_literal | {'type': 'literal', 'target_start': 21, 'length': 3, 'source': None} | {'type': 'copy', 'target_start': 21, 'length': 10, 'source': 180} | 0 | 0 | None | out_of_support |
| 21 | 0 | book_start_copy_missed_as_literal | {'type': 'literal', 'target_start': 0, 'length': 7, 'source': None} | {'type': 'copy', 'target_start': 0, 'length': 9, 'source': 197} | 0 | 0 | None | out_of_support |
| 26 | 0 | book_start_copy_missed_as_literal | {'type': 'literal', 'target_start': 0, 'length': 1, 'source': None} | {'type': 'copy', 'target_start': 0, 'length': 11, 'source': 3054} | 0 | 0 | None | out_of_support |
| 34 | 7 | internal_copy_missed_as_literal | {'type': 'literal', 'target_start': 105, 'length': 5, 'source': None} | {'type': 'copy', 'target_start': 105, 'length': 5, 'source': 183} | 0 | 0 | None | out_of_support |
| 39 | 0 | book_start_copy_missed_as_literal | {'type': 'literal', 'target_start': 0, 'length': 7, 'source': None} | {'type': 'copy', 'target_start': 0, 'length': 5, 'source': 2520} | 0 | 0 | None | out_of_support |
| 45 | 1 | internal_copy_missed_as_literal | {'type': 'literal', 'target_start': 62, 'length': 1, 'source': None} | {'type': 'copy', 'target_start': 62, 'length': 8, 'source': 2850} | 0 | 0 | None | out_of_support |
| 55 | 2 | copy_length_drift_same_source | {'type': 'copy', 'target_start': 67, 'length': 45, 'source': 2757} | {'type': 'copy', 'target_start': 67, 'length': 44, 'source': 2757} | 0 | 0 | None | out_of_support |
| 57 | 2 | literal_understop | {'type': 'literal', 'target_start': 69, 'length': 17, 'source': None} | {'type': 'literal', 'target_start': 69, 'length': 28, 'source': None} | 0 | 0 | None | out_of_support |

## Decision

Sequential observable signatures do not promote a parser. Adding prior path
memory does not produce deterministic support for the residual first-drift
choices, and prefix/holdout does not cover held-out residuals. The remaining
blocker is not a small observable sequential context over the current candidate
state.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
