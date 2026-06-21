# Observable Repair Policy Audit

Classification: `observable_repair_policy_rejected`
Translation delta: `NONE`

## Purpose

Gate 16 showed that a stable-projection oracle repair at the first
drift closes `11/12` residual books and two repairs close `12/12`.
Gate 17 asks whether a small observable repair policy can replace
that oracle without granting the stable projection.

Repair templates tested: immediate-copy forcing, book-start/internal
copy forcing, skipping to the next confirmed local peak, short-copy
literal substitution, copy shortening by one, and one combined policy.

## Policy Scoreboard

- Policies tested: `36`.
- Baseline exact books: `48/60`.
- Best policy: `baseline_window5`.
- Best exact books: `48/60`.
- Exact delta vs baseline: `0`.

| Policy | Exact books | Repairs applied | Drift classes |
|---|---:|---:|---|
| `baseline_window5` | `48/60` | `0` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `force_internal_copy_ge13` | `47/60` | `1` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `force_internal_copy_ge21` | `47/60` | `1` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `force_internal_copy_ge10` | `46/60` | `3` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 3, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `force_book_start_copy_ge8` | `46/60` | `6` | `{'book_start_copy_missed_as_literal': 1, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 5, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `force_internal_copy_ge8` | `46/60` | `6` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 4, 'internal_copy_missed_as_literal': 2, 'literal_understop': 4}` |
| `literal1_for_short_copy_le5` | `46/60` | `10` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 5, 'literal_understop': 4}` |
| `force_book_start_copy_ge21` | `45/60` | `3` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 4, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `force_book_start_copy_ge10` | `45/60` | `5` | `{'book_start_copy_missed_as_literal': 2, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 5, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `force_book_start_copy_ge5` | `45/60` | `9` | `{'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 7, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `force_internal_copy_ge6` | `45/60` | `9` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 5, 'internal_copy_missed_as_literal': 2, 'literal_understop': 4}` |
| `force_internal_copy_ge5` | `45/60` | `13` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 7, 'literal_understop': 4}` |
| `force_book_start_copy_ge13` | `44/60` | `4` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 5, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `force_immediate_copy_ge21` | `44/60` | `4` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 5, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `force_book_start_copy_ge6` | `44/60` | `8` | `{'book_start_copy_missed_as_literal': 1, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 7, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `force_immediate_copy_ge8` | `44/60` | `12` | `{'book_start_copy_missed_as_literal': 1, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 8, 'internal_copy_missed_as_literal': 2, 'literal_understop': 4}` |

## Prequential Selection

| Cutoff | Selected | Train hits | Test hits | Oracle | Oracle test hits |
|---:|---|---:|---:|---|---:|
| `20` | `baseline_window5` | `8/10` | `40/50` | `baseline_window5` | `40/50` |
| `30` | `force_book_start_copy_ge8` | `15/20` | `31/40` | `baseline_window5` | `34/40` |
| `40` | `force_book_start_copy_ge8` | `23/30` | `23/30` | `baseline_window5` | `26/30` |
| `50` | `baseline_window5` | `30/40` | `18/20` | `baseline_window5` | `18/20` |
| `60` | `baseline_window5` | `38/50` | `10/10` | `baseline_window5` | `10/10` |

## Decision

- Promotes observable repair policy: `False`.
- Prequential selected matches oracle cells: `3/5`.
- Observable repair templates test whether the gate16 oracle map can be replaced by a small target-text-aware parser rule. Promotion requires exact coverage and prefix/holdout stability.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
