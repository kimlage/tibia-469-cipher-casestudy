# Latent Path-State Budget Gate

Classification: `latent_path_state_budget_rejected_lookup_repackaging`
Translation delta: `NONE`

## Purpose

Gate 57 prices what remains after observable candidate signatures and short
sequential signatures fail. A latent path-state explanation must do more than
rename the residual lookup: it has to cover residual sites and labels without
receiving either for free.

This is not a compression sweep and not a promoted parser.

## Summary

- Decision universe: `267`.
- Residual decisions: `10`.
- Unsupported residuals under gate 56 best signature:
  `10/10`.
- Distinct stable shape labels: `9`.
- Site bits: `58.570`.
- Label-order bits: `20.791`.
- Baseline lookup bits: `79.361`.
- Best valid model: `explicit_residual_shape_lookup`.
- Best valid net vs lookup: `0.000`.
- Best invalid/oracle model: `residual_site_oracle_labels_only`.
- Best invalid/oracle net vs lookup: `-58.570`.
- Gate 48 best zero-FP residual-site detector TP:
  `3/10`.
- Promotes latent path-state budget: `False`.

## Cost Rows

| model | valid | site oracle | site bits | label bits | dictionary bits | total bits | net vs lookup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| explicit_residual_shape_lookup | True | False | 58.570 | 20.791 | 0.000 | 79.361 | 0.000 |
| latent_state_ids_with_label_dictionary | True | False | 58.570 | 20.791 | 0.000 | 79.361 | 0.000 |
| zero_fp_site_detector_plus_remaining_lookup_lower_bound | False | False | 0.000 | 55.310 | 0.000 | 55.310 | -24.050 |
| residual_site_oracle_labels_only | False | True | 0.000 | 20.791 | 0.000 | 20.791 | -58.570 |
| one_state_per_distinct_label_with_site_oracle | False | True | 0.000 | 20.791 | 3.170 | 23.961 | -55.400 |

## Residual Rows

| book | op | class | stable label | gate56 status |
| --- | --- | --- | --- | --- |
| 14 | 0 | literal_understop | ['literal', 39] | out_of_support |
| 16 | 9 | copy_started_inside_stable_literal | ['literal', 1] | out_of_support |
| 20 | 2 | internal_copy_missed_as_literal | ['copy', 10] | out_of_support |
| 21 | 0 | book_start_copy_missed_as_literal | ['copy', 9] | out_of_support |
| 26 | 0 | book_start_copy_missed_as_literal | ['copy', 11] | out_of_support |
| 34 | 7 | internal_copy_missed_as_literal | ['copy', 5] | out_of_support |
| 39 | 0 | book_start_copy_missed_as_literal | ['copy', 5] | out_of_support |
| 45 | 1 | internal_copy_missed_as_literal | ['copy', 8] | out_of_support |
| 55 | 2 | copy_length_drift_same_source | ['copy', 44] | out_of_support |
| 57 | 2 | literal_understop | ['literal', 28] | out_of_support |

## Decision

No latent path-state budget is promoted. The best valid latent-state accounting
is the explicit residual shape lookup itself: it pays the same `79.361`
bits before any interpretable state rule is charged. The cheaper rows are
invalid as parser explanations because they grant residual sites or ignore the
failed site detector.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
