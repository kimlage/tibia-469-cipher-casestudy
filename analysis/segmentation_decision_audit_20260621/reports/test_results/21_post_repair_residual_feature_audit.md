# Post-Repair Residual Feature Audit

Classification: `post_repair_residual_feature_screen_rejected`
Translation delta: `NONE`

## Purpose

Gate 21 asks whether the gate-20 residual oracle map can be replaced
by a non-oracle observable feature rule. The ten first residual drifts
are positives; active-parser aligned decisions before any drift are
negative controls.

## Feature Screen

- Active classifier: `if_peak_len_le5_then_skip_to_next_peak_ge5`.
- Active exact books: `50/60`.
- Residual books: `[14, 16, 20, 21, 26, 34, 39, 45, 55, 57]`.
- Clean decision controls: `224`.
- Predicates tested: `365`.
- Residual drift classes: `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 2}`.

| Predicate | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| `active_literal_immediate_copy_ge1` | `6` | `13` | `4` | `0.316` | `0.600` |
| `active_literal_immediate_copy_ge2` | `6` | `13` | `4` | `0.316` | `0.600` |
| `active_literal_immediate_copy_ge3` | `6` | `13` | `4` | `0.316` | `0.600` |
| `active_literal_immediate_copy_ge5` | `6` | `13` | `4` | `0.316` | `0.600` |
| `active_literal_with_immediate_copy` | `6` | `13` | `4` | `0.316` | `0.600` |
| `active_len_le8__and__active_literal_immediate_copy_ge5` | `6` | `13` | `4` | `0.316` | `0.600` |
| `active_literal__and__active_literal_immediate_copy_ge5` | `6` | `13` | `4` | `0.316` | `0.600` |
| `active_literal__and__active_literal_with_immediate_copy` | `6` | `13` | `4` | `0.316` | `0.600` |
| `active_literal__and__immediate_copy_ge5` | `6` | `13` | `4` | `0.316` | `0.600` |
| `active_literal_immediate_copy_ge5__and__immediate_copy_ge5` | `6` | `13` | `4` | `0.316` | `0.600` |
| `active_literal_immediate_copy_ge5__and__next_peak_ge5` | `6` | `13` | `4` | `0.316` | `0.600` |
| `active_literal_stops_before_next_peak__and__active_literal_immediate_copy_ge5` | `6` | `13` | `4` | `0.316` | `0.600` |

## Zero-False-Positive Controls

- Best zero-FP predicate: `active_literal_immediate_copy_ge5__and__remaining_le20`.
- Best zero-FP TP: `1/10`.
- Full zero-FP detector: `None`.

| Predicate | TP | Positive books |
|---|---:|---|
| `active_literal_immediate_copy_ge5__and__remaining_le20` | `1` | `[34]` |
| `active_literal_with_immediate_copy__and__remaining_le20` | `1` | `[34]` |
| `book_start__and__active_classifier_applied` | `1` | `[14]` |
| `book_start__and__peak_len_le5` | `1` | `[14]` |
| `position_end__and__active_literal_immediate_copy_ge5` | `1` | `[34]` |
| `position_end__and__active_literal_with_immediate_copy` | `1` | `[34]` |

## Prefix/Holdout

| Cutoff | Selected predicate | Train TP/FP/FN | Test TP/FP/FN | Oracle predicate |
|---:|---|---:|---:|---|
| `20` | `active_classifier_applied` | `1/0/1` | `1/2/7` | `active_literal_with_immediate_copy` |
| `30` | `active_len_le8__and__immediate_copy_ge8` | `4/5/1` | `1/8/4` | `active_literal_with_immediate_copy` |
| `40` | `active_literal_with_immediate_copy` | `5/8/2` | `1/5/2` | `active_classifier_applied` |
| `50` | `active_literal_with_immediate_copy` | `6/10/2` | `0/3/2` | `peak_len_le5` |
| `60` | `active_literal_with_immediate_copy` | `6/12/4` | `0/1/0` | `remaining_le10` |

## Residual Feature Rows

| Book | Class | Target | Active op | Stable op | Immediate copy | Peak/next peak |
|---:|---|---:|---|---|---:|---|
| `14` | `literal_understop` | `0` | `literal:27` | `literal:39` | `0` | `5/5` |
| `16` | `copy_started_inside_stable_literal` | `164` | `copy:8` | `literal:1` | `8` | `8/8` |
| `20` | `internal_copy_missed_as_literal` | `21` | `literal:3` | `copy:10` | `10` | `11/10` |
| `21` | `book_start_copy_missed_as_literal` | `0` | `literal:7` | `copy:9` | `9` | `137/136` |
| `26` | `book_start_copy_missed_as_literal` | `0` | `literal:1` | `copy:11` | `11` | `12/11` |
| `34` | `internal_copy_missed_as_literal` | `105` | `literal:5` | `copy:5` | `5` | `13/12` |
| `39` | `book_start_copy_missed_as_literal` | `0` | `literal:7` | `copy:5` | `5` | `52/51` |
| `45` | `internal_copy_missed_as_literal` | `62` | `literal:1` | `copy:8` | `8` | `17/16` |
| `55` | `copy_length_drift_same_source` | `67` | `copy:45` | `copy:44` | `45` | `45/44` |
| `57` | `literal_understop` | `69` | `literal:17` | `literal:28` | `0` | `5/5` |

## Decision

- Promotes residual feature rule: `False`.
- Prequential zero-test-FP cells: `0/5`.
- Prequential cover-all-test-residual cells: `1/5`.
- Prequential selected matches oracle-F1 cells: `1/5`.
- Gate 21 treats the ten gate-20 first residual drifts as positives and all active-parser aligned decisions before any drift as negative controls. A feature rule is promotable only if it separates residuals without false positives and remains stable under prefix/holdout selection.
- No predicate separates all residual repairs from clean decisions.
- The remaining blocker is still a richer path/state segmentation rule, not a simple residual feature flag.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
