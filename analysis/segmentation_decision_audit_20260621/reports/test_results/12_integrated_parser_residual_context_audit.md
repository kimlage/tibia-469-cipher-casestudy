# Integrated Parser Residual Context Audit

Classification: `residual_context_rule_rejected`
Translation delta: `NONE`

## Purpose

The prior controls rejected immediate-copy and weak-peak fixes. This
gate turns each aligned parser decision into observable context
features and asks whether simple predicates can identify the first
remaining drift decision without broad false positives.

## Summary

- Decision rows: `221`.
- Error rows: `12`.
- Exact books: `48/60`.
- Mismatch books: `[14, 16, 20, 21, 23, 26, 34, 39, 45, 49, 55, 57]`.
- Drift classes: `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}`.
- Predicate count: `64`.

## Best Predicate

- Predicate: `peak_len_le5`.
- TP/FP/FN/TN: `4/3/8/206`.
- Precision: `0.571`.
- Recall: `0.333`.
- Flagged clean books: `[12, 40]`.

## Predicate Scoreboard

| Predicate | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| `peak_len_le5` | `4` | `3` | `8` | `0.571` | `0.333` |
| `predicted_literal_len_le1` | `4` | `6` | `8` | `0.400` | `0.333` |
| `literal_with_immediate_copy_ge8` | `4` | `8` | `8` | `0.333` | `0.333` |
| `book_start_literal_with_immediate_copy` | `3` | `6` | `9` | `0.333` | `0.250` |
| `copy_available_at_literal` | `6` | `13` | `6` | `0.316` | `0.500` |
| `literal_with_immediate_copy_ge5` | `6` | `13` | `6` | `0.316` | `0.500` |
| `literal_with_immediate_copy_ge6` | `4` | `11` | `8` | `0.267` | `0.333` |
| `literal_with_immediate_copy_ge10` | `2` | `6` | `10` | `0.250` | `0.167` |
| `peak_len_le6` | `4` | `14` | `8` | `0.222` | `0.333` |
| `predicted_literal` | `10` | `40` | `2` | `0.200` | `0.833` |
| `predicted_literal_len_le21` | `10` | `40` | `2` | `0.200` | `0.833` |
| `predicted_literal_len_le34` | `10` | `40` | `2` | `0.200` | `0.833` |
| `predicted_literal_len_le2` | `4` | `16` | `8` | `0.200` | `0.333` |
| `internal_literal_with_short_predicted_len` | `5` | `22` | `7` | `0.185` | `0.417` |
| `predicted_literal_len_le13` | `9` | `40` | `3` | `0.184` | `0.750` |

## Prequential Predicate Selection

| Cutoff | Selected | Train TP/FP | Test TP/FP | Oracle | Oracle TP/FP |
|---:|---|---:|---:|---|---:|
| `20` | `peak_len_le5` | `1/2` | `3/1` | `predicted_literal_len_le1` | `4/1` |
| `30` | `literal_with_immediate_copy_ge8` | `3/3` | `1/5` | `predicted_literal_len_le1` | `2/1` |
| `40` | `book_start_literal_with_immediate_copy` | `3/3` | `0/3` | `predicted_literal_len_le1` | `2/1` |
| `50` | `peak_len_le5` | `3/3` | `1/0` | `peak_len_le5` | `1/0` |
| `60` | `peak_len_le5` | `4/3` | `0/0` | `None` | `0/0` |

## Residual Error Rows

| Book | Op | Class | Context |
|---:|---:|---|---|
| `14` | `0` | `literal_understop` | `{"immediate_copy_len": 0, "peak_len": 5, "peak_offset": 18, "predicted_length": 18, "predicted_type": "literal", "previous_type": "BOS", "target_start": 0}` |
| `16` | `9` | `copy_started_inside_stable_literal` | `{"immediate_copy_len": 8, "peak_len": 8, "peak_offset": 0, "predicted_length": 8, "predicted_type": "copy", "previous_type": "copy", "target_start": 164}` |
| `20` | `2` | `internal_copy_missed_as_literal` | `{"immediate_copy_len": 10, "peak_len": 11, "peak_offset": 3, "predicted_length": 3, "predicted_type": "literal", "previous_type": "copy", "target_start": 21}` |
| `21` | `0` | `book_start_copy_missed_as_literal` | `{"immediate_copy_len": 9, "peak_len": 137, "peak_offset": 7, "predicted_length": 7, "predicted_type": "literal", "previous_type": "BOS", "target_start": 0}` |
| `23` | `7` | `literal_understop` | `{"immediate_copy_len": 0, "peak_len": 5, "peak_offset": 1, "predicted_length": 1, "predicted_type": "literal", "previous_type": "copy", "target_start": 110}` |
| `26` | `0` | `book_start_copy_missed_as_literal` | `{"immediate_copy_len": 11, "peak_len": 12, "peak_offset": 1, "predicted_length": 1, "predicted_type": "literal", "previous_type": "BOS", "target_start": 0}` |
| `34` | `7` | `internal_copy_missed_as_literal` | `{"immediate_copy_len": 5, "peak_len": 13, "peak_offset": 5, "predicted_length": 5, "predicted_type": "literal", "previous_type": "copy", "target_start": 105}` |
| `39` | `0` | `book_start_copy_missed_as_literal` | `{"immediate_copy_len": 5, "peak_len": 52, "peak_offset": 7, "predicted_length": 7, "predicted_type": "literal", "previous_type": "BOS", "target_start": 0}` |
| `45` | `1` | `internal_copy_missed_as_literal` | `{"immediate_copy_len": 8, "peak_len": 17, "peak_offset": 1, "predicted_length": 1, "predicted_type": "literal", "previous_type": "copy", "target_start": 62}` |
| `49` | `2` | `literal_understop` | `{"immediate_copy_len": 0, "peak_len": 5, "peak_offset": 1, "predicted_length": 1, "predicted_type": "literal", "previous_type": "copy", "target_start": 18}` |
| `55` | `2` | `copy_length_drift_same_source` | `{"immediate_copy_len": 45, "peak_len": 45, "peak_offset": 0, "predicted_length": 45, "predicted_type": "copy", "previous_type": "copy", "target_start": 67}` |
| `57` | `2` | `literal_understop` | `{"immediate_copy_len": 0, "peak_len": 5, "peak_offset": 11, "predicted_length": 11, "predicted_type": "literal", "previous_type": "copy", "target_start": 69}` |

## Decision

- Promotes context rule: `False`.
- Residual context predicates test whether a simple observable parser-state flag can identify the remaining first-drift decisions. A promotable correction must isolate the residuals without broad false positives and survive prefix selection.
- The result remains target-text-aware and analysis-only.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
