# Integrated Parser Peak Strength Audit

Classification: `integrated_peak_strength_policy_rejected`
Translation delta: `NONE`

## Purpose

Gate 10 rejected immediate-copy overrides. This gate tests the
opposite structural rescue: require a stronger accepted local peak
before ending a literal run, to see whether residual literal
understops are caused by weak early copy peaks.

## Scoreboard

- Policies tested: `26`.
- Baseline `window5:min_peak_len5` exact books: `48/60`.
- Best policy `window5:min_peak_len5` exact books: `48/60`.
- Exact-book improvement vs baseline: `0`.

| Policy | Exact books | Literal gaps | Literal digits | Drift classes |
|---|---:|---:|---:|---|
| `window5:min_peak_len5` | `48/60` | `66` | `265` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:min_peak_len6` | `48/60` | `62` | `310` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 5, 'literal_overstop': 1, 'literal_understop': 1}` |
| `window5:min_peak_len7` | `43/60` | `62` | `370` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 8, 'literal_overstop': 5}` |
| `window5:min_peak_len8` | `39/60` | `65` | `423` | `{'book_start_copy_missed_as_literal': 4, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 9, 'literal_overstop': 7}` |
| `window5:min_peak_len9` | `37/60` | `67` | `485` | `{'book_start_copy_missed_as_literal': 5, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 9, 'literal_overstop': 8}` |
| `window5:min_peak_len10` | `33/60` | `68` | `573` | `{'book_start_copy_missed_as_literal': 6, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 11, 'literal_overstop': 9}` |
| `window5:min_peak_len11` | `32/60` | `66` | `643` | `{'book_start_copy_missed_as_literal': 6, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 12, 'literal_overstop': 9}` |
| `window5:min_peak_len12` | `31/60` | `65` | `713` | `{'book_start_copy_missed_as_literal': 7, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 12, 'literal_overstop': 9}` |
| `window5:min_peak_len13` | `30/60` | `64` | `829` | `{'book_start_copy_missed_as_literal': 7, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 14, 'literal_overstop': 8}` |
| `window5:min_peak_len14` | `30/60` | `64` | `925` | `{'book_start_copy_missed_as_literal': 8, 'internal_copy_missed_as_literal': 13, 'literal_overstop': 9}` |
| `window5:min_peak_len15` | `30/60` | `61` | `1009` | `{'book_start_copy_missed_as_literal': 8, 'internal_copy_missed_as_literal': 12, 'literal_overstop': 10}` |
| `window5:min_peak_len16` | `30/60` | `61` | `1024` | `{'book_start_copy_missed_as_literal': 9, 'internal_copy_missed_as_literal': 11, 'literal_overstop': 10}` |
| `window5:min_peak_len17` | `30/60` | `61` | `1024` | `{'book_start_copy_missed_as_literal': 9, 'internal_copy_missed_as_literal': 11, 'literal_overstop': 10}` |
| `window5:min_peak_len18` | `29/60` | `61` | `1116` | `{'book_start_copy_missed_as_literal': 10, 'internal_copy_missed_as_literal': 11, 'literal_overstop': 10}` |

## Prequential Policy Selection

| Cutoff | Selected | Train hits | Test hits | Oracle | Oracle test hits |
|---:|---|---:|---:|---|---:|
| `20` | `window5:min_peak_len5` | `8/10` | `40/50` | `window5:min_peak_len6` | `41/50` |
| `30` | `window5:min_peak_len6` | `14/20` | `34/40` | `window5:min_peak_len5` | `34/40` |
| `40` | `window5:min_peak_len6` | `22/30` | `26/30` | `window5:min_peak_len5` | `26/30` |
| `50` | `window5:min_peak_len5` | `30/40` | `18/20` | `window5:min_peak_len6` | `19/20` |
| `60` | `window5:min_peak_len6` | `38/50` | `10/10` | `window5:min_peak_len5` | `10/10` |

## Best Residual Drift

- Best mismatch books: `[14, 16, 20, 21, 23, 26, 34, 39, 45, 49, 55, 57]`.
- Best drift classes: `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}`.

| Book | Class | First diff |
|---:|---|---|
| `14` | `literal_understop` | `{"index": 0, "predicted": {"length": 18, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 39, "source": null, "target_start": 0, "type": "literal"}}` |
| `16` | `copy_started_inside_stable_literal` | `{"index": 9, "predicted": {"length": 8, "source": 473, "target_start": 164, "type": "copy"}, "stable_projection": {"length": 1, "source": null, "target_start": 164, "type": "literal"}}` |
| `20` | `internal_copy_missed_as_literal` | `{"index": 2, "predicted": {"length": 3, "source": null, "target_start": 21, "type": "literal"}, "stable_projection": {"length": 10, "source": 180, "target_start": 21, "type": "copy"}}` |
| `21` | `book_start_copy_missed_as_literal` | `{"index": 0, "predicted": {"length": 7, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 9, "source": 197, "target_start": 0, "type": "copy"}}` |
| `23` | `literal_understop` | `{"index": 7, "predicted": {"length": 1, "source": null, "target_start": 110, "type": "literal"}, "stable_projection": {"length": 7, "source": null, "target_start": 110, "type": "literal"}}` |
| `26` | `book_start_copy_missed_as_literal` | `{"index": 0, "predicted": {"length": 1, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 11, "source": 3054, "target_start": 0, "type": "copy"}}` |
| `34` | `internal_copy_missed_as_literal` | `{"index": 7, "predicted": {"length": 5, "source": null, "target_start": 105, "type": "literal"}, "stable_projection": {"length": 5, "source": 183, "target_start": 105, "type": "copy"}}` |
| `39` | `book_start_copy_missed_as_literal` | `{"index": 0, "predicted": {"length": 7, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 5, "source": 2520, "target_start": 0, "type": "copy"}}` |
| `45` | `internal_copy_missed_as_literal` | `{"index": 1, "predicted": {"length": 1, "source": null, "target_start": 62, "type": "literal"}, "stable_projection": {"length": 8, "source": 2850, "target_start": 62, "type": "copy"}}` |
| `49` | `literal_understop` | `{"index": 2, "predicted": {"length": 1, "source": null, "target_start": 18, "type": "literal"}, "stable_projection": {"length": 7, "source": null, "target_start": 18, "type": "literal"}}` |
| `55` | `copy_length_drift_same_source` | `{"index": 2, "predicted": {"length": 45, "source": 2757, "target_start": 67, "type": "copy"}, "stable_projection": {"length": 44, "source": 2757, "target_start": 67, "type": "copy"}}` |
| `57` | `literal_understop` | `{"index": 2, "predicted": {"length": 11, "source": null, "target_start": 69, "type": "literal"}, "stable_projection": {"length": 28, "source": null, "target_start": 69, "type": "literal"}}` |

## Decision

- Promotes peak-strength policy: `False`.
- Minimum peak strength tests whether residual literal understops come from accepting weak local peaks. The family is promoted only if it improves exact stable projection coverage under prefix selection without turning missed copies into new exceptions.
- The result remains target-text-aware and analysis-only.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
