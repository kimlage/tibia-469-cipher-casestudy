# Branch Rank Position Audit

Classification: `branch_rank_rule_rejected`
Translation delta: `NONE`

## Purpose

Gate 46 ranks every observable candidate branch at the remaining residual
sites. It asks whether the stable branch is simply top-ranked by a small
observable ordering: type priority, length priority, active/default priority,
literal-stop/immediate-copy priority, or suffix continuation metrics.

## Summary

- Rankers tested: `14`.
- Residual decisions: `10`.
- Clean controls: `224`.
- Best top-1 ranker: `balanced_ops_literals`.
- Best top-1 residual hits: `6/10`.
- Best top-1 clean false changes: `20`.
- Best top-3 ranker: `balanced_ops_literals`.
- Best top-3 residual coverage: `8/10`.
- Best top-3 clean false changes: `20`.
- Promotes branch-rank rule: `False`.

## Oracle Rank Lower Bound

- Residual branch count min/median/max: `9` / `21.0` / `26`.
- Per-residual rank selector lower bound: `42.736` bits.

## Ranker Scoreboard

| ranker | top1 | top2 | top3 | clean false changes | median rank | max rank |
| --- | --- | --- | --- | --- | --- | --- |
| balanced_ops_literals | 6 | 8 | 8 | 20 | 1.0 | 8 |
| copy_first_longest | 6 | 7 | 7 | 43 | 1.0 | 14 |
| immediate_copy_first | 6 | 7 | 7 | 43 | 1.0 | 14 |
| max_suffix_copy_digits | 5 | 6 | 8 | 20 | 1.5 | 5 |
| min_suffix_literals | 5 | 6 | 8 | 20 | 1.5 | 5 |
| max_suffix_copy_count | 4 | 6 | 7 | 155 | 2.0 | 7 |
| copy_first_shortest | 2 | 2 | 7 | 215 | 3.0 | 7 |
| shortest_op | 1 | 1 | 2 | 217 | 8.5 | 18 |
| literal_first_shortest | 1 | 1 | 1 | 217 | 20.5 | 26 |
| literal_stop_first | 1 | 1 | 1 | 217 | 20.5 | 26 |
| active_first | 0 | 2 | 2 | 0 | 4.0 | 20 |
| min_suffix_ops | 0 | 4 | 5 | 174 | 5.0 | 18 |
| longest_op | 0 | 0 | 1 | 174 | 13.0 | 19 |
| literal_first_longest | 0 | 0 | 0 | 222 | 19.0 | 24 |

## Best Top-1 Residual Rows

| book | class | branches | stable rank | top label | top stable? | top active? |
| --- | --- | --- | --- | --- | --- | --- |
| 14 | literal_understop | 19 | 6 | observable_literal_stop | False | False |
| 16 | copy_started_inside_stable_literal | 9 | 8 | observable_immediate_copy | False | False |
| 20 | internal_copy_missed_as_literal | 24 | 2 | observable_immediate_copy | False | False |
| 21 | book_start_copy_missed_as_literal | 26 | 2 | observable_immediate_copy | False | False |
| 26 | book_start_copy_missed_as_literal | 22 | 1 | observable_immediate_copy+stable_projection_oracle | True | False |
| 34 | internal_copy_missed_as_literal | 13 | 1 | observable_immediate_copy+stable_projection_oracle | True | False |
| 39 | book_start_copy_missed_as_literal | 24 | 1 | observable_immediate_copy+stable_projection_oracle | True | False |
| 45 | internal_copy_missed_as_literal | 25 | 1 | observable_immediate_copy+stable_projection_oracle | True | False |
| 55 | copy_length_drift_same_source | 20 | 1 | observable_immediate_copy+stable_projection_oracle | True | False |
| 57 | literal_understop | 20 | 1 | observable_literal_stop+stable_projection_oracle | True | False |

## Best Top-3 Residual Rows

| book | class | branches | stable rank | top label | top stable? | top active? |
| --- | --- | --- | --- | --- | --- | --- |
| 14 | literal_understop | 19 | 6 | observable_literal_stop | False | False |
| 16 | copy_started_inside_stable_literal | 9 | 8 | observable_immediate_copy | False | False |
| 20 | internal_copy_missed_as_literal | 24 | 2 | observable_immediate_copy | False | False |
| 21 | book_start_copy_missed_as_literal | 26 | 2 | observable_immediate_copy | False | False |
| 26 | book_start_copy_missed_as_literal | 22 | 1 | observable_immediate_copy+stable_projection_oracle | True | False |
| 34 | internal_copy_missed_as_literal | 13 | 1 | observable_immediate_copy+stable_projection_oracle | True | False |
| 39 | book_start_copy_missed_as_literal | 24 | 1 | observable_immediate_copy+stable_projection_oracle | True | False |
| 45 | internal_copy_missed_as_literal | 25 | 1 | observable_immediate_copy+stable_projection_oracle | True | False |
| 55 | copy_length_drift_same_source | 20 | 1 | observable_immediate_copy+stable_projection_oracle | True | False |
| 57 | literal_understop | 20 | 1 | observable_literal_stop+stable_projection_oracle | True | False |

## Decision

No branch-rank rule is promoted. The best observable top-1 ordering explains
only a minority of residuals and damages clean controls; even the best top-3
coverage leaves residuals outside the near-top set. This rejects a simple
rank/ordering heuristic as the missing segmentation mechanism.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
