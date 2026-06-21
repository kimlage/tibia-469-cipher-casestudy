# Residual Site Detector Gate

Classification: `residual_site_detector_rejected`
Translation delta: `NONE`

## Purpose

Gate 48 tests the missing condition from gate 47: can the residual sites be
detected from observable branch ambiguity and ranker-disagreement features,
without granting a residual-site lookup?

## Summary

- Decisions scored: `234`.
- Residual sites: `10`.
- Clean controls: `224`.
- Predicates: `1196`.
- Scored single/pair rules: `4356`.
- Best predicate: `active_top_count_le_1__and__max_copy_length_le_10`.
- Best TP/FP/FN: `6/6/4`.
- Best precision/recall: `0.500` / `0.600`.
- Best zero-FP predicate: `literal_stop_branch_count_ge_22__and__nonactive_top_count_ge_10`.
- Best zero-FP TP: `3`.
- Prequential cells with residuals: `4`.
- Prequential zero-FP cells: `2/4`.
- Prequential cover-all-residual cells: `0/4`.
- Promotes residual site detector: `False`.

## Scoreboard

| predicate | TP | FP | FN | precision | recall | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| active_top_count_le_1__and__max_copy_length_le_10 | 6 | 6 | 4 | 0.500 | 0.600 | 0.545 |
| nonactive_top_count_ge_13__and__max_copy_length_le_10 | 6 | 6 | 4 | 0.500 | 0.600 | 0.545 |
| branch_count_ge_24__and__max_copy_length_le_10 | 4 | 1 | 6 | 0.800 | 0.400 | 0.533 |
| active_top_count_le_1__and__copy_branch_count_le_3 | 6 | 7 | 4 | 0.462 | 0.600 | 0.522 |
| active_top_count_le_1__and__immediate_copy_branch_count_le_3 | 6 | 7 | 4 | 0.462 | 0.600 | 0.522 |
| active_top_count_le_1__and__max_copy_length_le_11 | 6 | 7 | 4 | 0.462 | 0.600 | 0.522 |
| active_top_count_le_1__and__max_copy_length_le_12 | 6 | 7 | 4 | 0.462 | 0.600 | 0.522 |
| active_top_count_le_1__and__max_copy_length_le_13 | 6 | 7 | 4 | 0.462 | 0.600 | 0.522 |
| active_top_count_le_1__and__max_copy_length_le_14 | 6 | 7 | 4 | 0.462 | 0.600 | 0.522 |
| active_top_count_le_1__and__max_copy_length_le_15 | 6 | 7 | 4 | 0.462 | 0.600 | 0.522 |
| active_top_count_le_1__and__max_copy_length_le_16 | 6 | 7 | 4 | 0.462 | 0.600 | 0.522 |
| active_top_count_le_1__and__max_copy_length_le_17 | 6 | 7 | 4 | 0.462 | 0.600 | 0.522 |

## Prefix/Holdout

| cutoff | selected predicate | train TP/FP/FN | test TP/FP/FN | test F1 |
| --- | --- | --- | --- | --- |
| 20 | active_repair_applied_eq_True | [1, 0, 1] | [1, 2, 7] | 0.182 |
| 30 | ranker_disagreement_ops_ge_6 | [2, 0, 3] | [0, 0, 5] | 0.000 |
| 40 | nonactive_top_count_ge_13 | [5, 7, 2] | [1, 5, 2] | 0.222 |
| 50 | literal_stop_branch_count_ge_22 | [3, 2, 5] | [0, 0, 2] | 0.000 |
| 60 | nonactive_top_count_ge_13 | [6, 11, 4] | [0, 1, 0] | 0.000 |

## Decision

No residual-site detector is promoted. Observable branch ambiguity and ranker
disagreement do not identify the residual sites cleanly enough to make the
gate-47 residual-gated ranker source-free. The apparent residual-gated saving
therefore remains lookup-dependent.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
