# Conditional Repair Classifier Audit

Classification: `conditional_repair_classifier_partial_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 18 tests a richer non-oracle replacement for the gate-16
stable-projection repair map. Each candidate classifier is one
observable predicate plus one observable repair action. The classifier
is applied end-to-end while parsing, and prefix/holdout selection is
reported separately from full-corpus best score.

## Classifier Scoreboard

- Predicates tested: `54`.
- Actions tested: `32`.
- Classifiers tested: `26`.
- Baseline exact books: `48/60`.
- Best classifier: `if_peak_len_le5_then_skip_to_next_peak_ge5`.
- Best exact books: `50/60`.
- Exact delta vs baseline: `2`.

| Classifier | Exact books | Repairs | Drift classes |
|---|---:|---:|---|
| `if_peak_len_le5_then_skip_to_next_peak_ge5` | `50/60` | `4` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 2}` |
| `baseline_window5` | `48/60` | `0` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `if_immediate_copy_ge13_then_force_internal_copy_ge13` | `47/60` | `1` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `if_immediate_copy_ge10_then_force_internal_copy_ge10` | `46/60` | `3` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 3, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `if_book_start_then_force_book_start_copy_ge8` | `46/60` | `6` | `{'book_start_copy_missed_as_literal': 1, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 5, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `if_internal_then_force_internal_copy_ge8` | `46/60` | `6` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 4, 'internal_copy_missed_as_literal': 2, 'literal_understop': 4}` |
| `if_literal_with_immediate_copy_then_force_internal_copy_ge8` | `46/60` | `6` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 4, 'internal_copy_missed_as_literal': 2, 'literal_understop': 4}` |
| `if_predicted_copy_then_literal1_for_short_copy_le5` | `46/60` | `10` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 5, 'literal_understop': 4}` |
| `if_book_start_then_force_book_start_copy_ge5` | `45/60` | `9` | `{'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 7, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `if_literal_len_le1_then_skip_to_next_peak_ge5` | `45/60` | `12` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 3, 'literal_overstop': 6, 'literal_understop': 2}` |
| `if_internal_then_force_internal_copy_ge5` | `45/60` | `13` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 7, 'literal_understop': 4}` |
| `if_literal_with_immediate_copy_then_force_internal_copy_ge5` | `45/60` | `13` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 7, 'literal_understop': 4}` |
| `if_peak_len_le8_then_skip_to_next_peak_ge5` | `45/60` | `15` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 2, 'literal_overstop': 7, 'literal_understop': 2}` |
| `if_book_start_then_force_book_start_copy_ge13` | `44/60` | `4` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 5, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `if_literal_with_immediate_copy_then_force_immediate_copy_ge8` | `44/60` | `12` | `{'book_start_copy_missed_as_literal': 1, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 8, 'internal_copy_missed_as_literal': 2, 'literal_understop': 4}` |
| `if_literal_with_immediate_copy_then_force_immediate_copy_ge13` | `43/60` | `5` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 6, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |

## Prequential Selection

| Cutoff | Selected | Train hits | Test hits | Oracle | Oracle test hits |
|---:|---|---:|---:|---|---:|
| `20` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `8/10` | `42/50` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `42/50` |
| `30` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `15/20` | `35/40` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `35/40` |
| `40` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `23/30` | `27/30` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `27/30` |
| `50` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `32/40` | `18/20` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `18/20` |
| `60` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `40/50` | `10/10` | `if_peak_len_le5_then_skip_to_next_peak_ge5` | `10/10` |

## Decision

- Promotes conditional repair classifier: `False`.
- Prequential selected matches oracle cells: `5/5`.
- Conditional repair classifiers test whether a single observable predicate-action pair can replace gate16's stable-projection oracle. They are scored end-to-end and selected by prefix/holdout.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
