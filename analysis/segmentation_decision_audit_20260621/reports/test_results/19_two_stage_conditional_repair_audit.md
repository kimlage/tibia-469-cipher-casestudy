# Two-Stage Conditional Repair Audit

Classification: `two_stage_conditional_repair_rejected`
Translation delta: `NONE`

## Purpose

Gate 19 keeps the gate-18 repair as the first stage and tests whether
one additional observable predicate-action rule can close more of the
remaining `10/60` drift books without using the stable projection as
an oracle.

## Pipeline Scoreboard

- Active first stage: `if_peak_len_le5_then_skip_to_next_peak_ge5`.
- Active exact books: `50/60`.
- Pipelines tested: `25`.
- Best pipeline: `if_peak_len_le5_then_skip_to_next_peak_ge5`.
- Best exact books: `50/60`.
- Exact delta vs active first stage: `0`.

| Pipeline | Exact books | Repairs | Drift classes |
|---|---:|---:|---|
| `if_peak_len_le5_then_skip_to_next_peak_ge5` | `50/60` | `4` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_immediate_copy_ge13_then_force_internal_copy_ge13` | `49/60` | `5` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_immediate_copy_ge10_then_force_internal_copy_ge10` | `48/60` | `7` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 3, 'internal_copy_missed_as_literal': 3, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_book_start_then_force_book_start_copy_ge8` | `48/60` | `10` | `{'book_start_copy_missed_as_literal': 1, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 5, 'internal_copy_missed_as_literal': 3, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_internal_then_force_internal_copy_ge8` | `48/60` | `10` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 4, 'internal_copy_missed_as_literal': 2, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_literal_with_immediate_copy_then_force_internal_copy_ge8` | `48/60` | `10` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 4, 'internal_copy_missed_as_literal': 2, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_predicted_copy_then_literal1_for_short_copy_le5` | `47/60` | `10` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 6, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_book_start_then_force_book_start_copy_ge5` | `47/60` | `13` | `{'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 7, 'internal_copy_missed_as_literal': 3, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_internal_then_force_internal_copy_ge5` | `47/60` | `17` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 7, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_literal_with_immediate_copy_then_force_internal_copy_ge5` | `47/60` | `17` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 7, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_book_start_then_force_book_start_copy_ge13` | `46/60` | `8` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 5, 'internal_copy_missed_as_literal': 3, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_literal_with_immediate_copy_then_force_immediate_copy_ge8` | `46/60` | `16` | `{'book_start_copy_missed_as_literal': 1, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 8, 'internal_copy_missed_as_literal': 2, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_literal_with_immediate_copy_then_force_immediate_copy_ge13` | `45/60` | `9` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 6, 'internal_copy_missed_as_literal': 3, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_literal_len_le1_then_skip_to_next_peak_ge5` | `45/60` | `13` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 3, 'literal_overstop': 6, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_peak_len_le8_then_skip_to_next_peak_ge5` | `45/60` | `15` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 2, 'literal_overstop': 7, 'literal_understop': 2}` |
| `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_literal_with_immediate_copy_then_force_immediate_copy_ge5` | `43/60` | `27` | `{'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 14, 'literal_understop': 2}` |

## Prequential Selection

| Cutoff | Selected | Train hits | Test hits | Oracle | Oracle test hits |
|---:|---|---:|---:|---|---:|
| `20` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `8/10` | `42/50` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `42/50` |
| `30` | `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_book_start_then_force_book_start_copy_ge8` | `16/20` | `32/40` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `35/40` |
| `40` | `if_peak_len_le5_then_skip_to_next_peak_ge5__then__if_book_start_then_force_book_start_copy_ge8` | `24/30` | `24/30` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `27/30` |
| `50` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `32/40` | `18/20` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `18/20` |
| `60` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `40/50` | `10/10` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `10/10` |

## Decision

- Promotes two-stage repair: `False`.
- Prequential selected matches oracle cells: `3/5`.
- Two-stage repair tests whether the gate18 prefix-stable repair can be followed by one more observable predicate-action rule. The second stage is scored end-to-end and selected by prefix/holdout.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
