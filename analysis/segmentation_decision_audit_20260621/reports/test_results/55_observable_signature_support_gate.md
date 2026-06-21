# Observable Signature Support Gate

Classification: `observable_signature_support_rejected`
Translation delta: `NONE`

## Purpose

Gate 55 asks whether the remaining residual `(source,length)` choices are
supported by repeated observable decision/candidate signatures. It does not
score a new branch policy. Instead, each residual first-drift decision is
queried against other decisions with the same observable signature. A signature
can promote only if it deterministically supports the needed stable label and
generalizes under prefix/holdout.

The signature families use book/start position, active operation shape, branch
counts, candidate length profiles, and copy feature buckets. They do not use
`drift_class`, plaintext, semantics, or row0 origin information.

## Summary

- Decisions: `234`.
- Residual decisions: `10`.
- Signature families: `6`.
- Label modes: `3`.
- Best signature: `decision_coarse`.
- Best label mode: `stable_shape_label`.
- Best deterministic residual matches:
  `0/10`.
- Best supported residuals: `3/10`.
- Best status counts: `{'ambiguous_includes_stable': 1, 'deterministic_contradiction': 2, 'out_of_support': 7}`.
- Prefix/holdout cells with any deterministic match:
  `0/4`.
- Prefix/holdout cover-all residual cells:
  `0/4`.
- Promotes parser rule: `False`.

## Scoreboard

| signature | label mode | deterministic matches | supported | contradictions | ambiguous with stable | status counts |
| --- | --- | --- | --- | --- | --- | --- |
| decision_coarse | stable_shape_label | 0/10 | 3 | 2 | 1 | {'ambiguous_includes_stable': 1, 'deterministic_contradiction': 2, 'out_of_support': 7} |
| decision_coarse | stable_rank_label | 0/10 | 3 | 3 | 0 | {'deterministic_contradiction': 3, 'out_of_support': 7} |
| decision_coarse | stable_action_label | 0/10 | 3 | 3 | 0 | {'deterministic_contradiction': 3, 'out_of_support': 7} |
| candidate_length_buckets | stable_shape_label | 0/10 | 1 | 1 | 0 | {'ambiguous_excludes_stable': 1, 'out_of_support': 9} |
| candidate_length_buckets | stable_rank_label | 0/10 | 1 | 1 | 0 | {'deterministic_contradiction': 1, 'out_of_support': 9} |
| candidate_length_buckets | stable_action_label | 0/10 | 1 | 1 | 0 | {'deterministic_contradiction': 1, 'out_of_support': 9} |
| candidate_count_extrema | stable_shape_label | 0/10 | 1 | 1 | 0 | {'ambiguous_excludes_stable': 1, 'out_of_support': 9} |
| candidate_count_extrema | stable_rank_label | 0/10 | 1 | 1 | 0 | {'deterministic_contradiction': 1, 'out_of_support': 9} |
| candidate_count_extrema | stable_action_label | 0/10 | 1 | 1 | 0 | {'deterministic_contradiction': 1, 'out_of_support': 9} |
| candidate_feature_profile | stable_shape_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| candidate_feature_profile | stable_rank_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| candidate_feature_profile | stable_action_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| candidate_exact_length_profile | stable_shape_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| candidate_exact_length_profile | stable_rank_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| candidate_exact_length_profile | stable_action_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| candidate_exact_feature_profile | stable_shape_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| candidate_exact_feature_profile | stable_rank_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |
| candidate_exact_feature_profile | stable_action_label | 0/10 | 0 | 0 | 0 | {'out_of_support': 10} |

## Prefix/Holdout For Best Signature

| cutoff | deterministic matches | supported | contradictions | status counts |
| --- | --- | --- | --- | --- |
| 20 | 0/8 | 2 | 2 | {'ambiguous_excludes_stable': 1, 'deterministic_contradiction': 1, 'out_of_support': 6} |
| 30 | 0/5 | 1 | 1 | {'ambiguous_excludes_stable': 1, 'out_of_support': 4} |
| 40 | 0/3 | 1 | 0 | {'ambiguous_includes_stable': 1, 'out_of_support': 2} |
| 50 | 0/2 | 1 | 0 | {'ambiguous_includes_stable': 1, 'out_of_support': 1} |
| 60 | 0/0 | 0 | 0 | {} |

## Residual Rows For Best Signature

| book | op | class | active | stable | support | labels | majority | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | 0 | literal_understop | {'type': 'literal', 'target_start': 0, 'length': 27, 'source': None} | {'type': 'literal', 'target_start': 0, 'length': 39, 'source': None} | 0 | 0 | None | out_of_support |
| 16 | 9 | copy_started_inside_stable_literal | {'type': 'copy', 'target_start': 164, 'length': 8, 'source': 473} | {'type': 'literal', 'target_start': 164, 'length': 1, 'source': None} | 1 | 1 | ('copy', 7) | deterministic_contradiction |
| 20 | 2 | internal_copy_missed_as_literal | {'type': 'literal', 'target_start': 21, 'length': 3, 'source': None} | {'type': 'copy', 'target_start': 21, 'length': 10, 'source': 180} | 1 | 1 | ('literal', 3) | deterministic_contradiction |
| 21 | 0 | book_start_copy_missed_as_literal | {'type': 'literal', 'target_start': 0, 'length': 7, 'source': None} | {'type': 'copy', 'target_start': 0, 'length': 9, 'source': 197} | 0 | 0 | None | out_of_support |
| 26 | 0 | book_start_copy_missed_as_literal | {'type': 'literal', 'target_start': 0, 'length': 1, 'source': None} | {'type': 'copy', 'target_start': 0, 'length': 11, 'source': 3054} | 0 | 0 | None | out_of_support |
| 34 | 7 | internal_copy_missed_as_literal | {'type': 'literal', 'target_start': 105, 'length': 5, 'source': None} | {'type': 'copy', 'target_start': 105, 'length': 5, 'source': 183} | 0 | 0 | None | out_of_support |
| 39 | 0 | book_start_copy_missed_as_literal | {'type': 'literal', 'target_start': 0, 'length': 7, 'source': None} | {'type': 'copy', 'target_start': 0, 'length': 5, 'source': 2520} | 0 | 0 | None | out_of_support |
| 45 | 1 | internal_copy_missed_as_literal | {'type': 'literal', 'target_start': 62, 'length': 1, 'source': None} | {'type': 'copy', 'target_start': 62, 'length': 8, 'source': 2850} | 0 | 0 | None | out_of_support |
| 55 | 2 | copy_length_drift_same_source | {'type': 'copy', 'target_start': 67, 'length': 45, 'source': 2757} | {'type': 'copy', 'target_start': 67, 'length': 44, 'source': 2757} | 24 | 15 | ('copy', 52) | ambiguous_includes_stable |
| 57 | 2 | literal_understop | {'type': 'literal', 'target_start': 69, 'length': 17, 'source': None} | {'type': 'literal', 'target_start': 69, 'length': 28, 'source': None} | 0 | 0 | None | out_of_support |

## Decision

Observable candidate signatures do not promote a segmentation parser. The best
full-fit signature explains only the listed deterministic residual subset, and
prefix/holdout does not cover all held-out residuals. The remaining residual
choices therefore still require either richer latent path/state information or
a source-free account of the target digit stream.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
