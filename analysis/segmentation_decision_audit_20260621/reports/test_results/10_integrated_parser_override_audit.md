# Integrated Parser Override Audit

Classification: `integrated_override_policy_rejected`
Translation delta: `NONE`

## Purpose

Gate 09 left `12` drift books under the prefix-stable `window5`
local-peak parser. This gate tests explicit immediate-copy overrides
for book-start, internal, and any-position matches, each with a
minimum copy-length threshold.

## Scoreboard

- Policies tested: `49`.
- Baseline `window5:no_override` exact books: `48/60`.
- Best policy `window5:no_override` exact books: `48/60`.
- Exact-book improvement vs baseline: `0`.

| Policy | Exact books | Literal gaps | Literal digits | Drift classes |
|---|---:|---:|---:|---|
| `window5:no_override` | `48/60` | `66` | `265` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:internal_immediate_len12` | `47/60` | `65` | `262` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:internal_immediate_len13` | `47/60` | `65` | `262` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:internal_immediate_len14` | `47/60` | `65` | `262` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:internal_immediate_len15` | `47/60` | `65` | `262` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:internal_immediate_len16` | `47/60` | `65` | `262` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:internal_immediate_len17` | `47/60` | `65` | `262` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:internal_immediate_len18` | `47/60` | `65` | `262` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:internal_immediate_len19` | `47/60` | `65` | `262` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:internal_immediate_len20` | `47/60` | `65` | `262` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:book_start_immediate_len8` | `46/60` | `61` | `244` | `{'book_start_copy_missed_as_literal': 1, 'book_start_false_copy': 4, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:book_start_immediate_len9` | `46/60` | `61` | `244` | `{'book_start_copy_missed_as_literal': 1, 'book_start_false_copy': 4, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:internal_immediate_len10` | `46/60` | `64` | `262` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 3, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `window5:internal_immediate_len11` | `46/60` | `65` | `264` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 3, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |

## Prequential Policy Selection

| Cutoff | Selected | Train hits | Test hits | Oracle | Oracle test hits |
|---:|---|---:|---:|---|---:|
| `20` | `window5:no_override` | `8/10` | `40/50` | `window5:no_override` | `40/50` |
| `30` | `window5:book_start_immediate_len9` | `15/20` | `31/40` | `window5:no_override` | `34/40` |
| `40` | `window5:book_start_immediate_len9` | `23/30` | `23/30` | `window5:no_override` | `26/30` |
| `50` | `window5:no_override` | `30/40` | `18/20` | `window5:no_override` | `18/20` |
| `60` | `window5:no_override` | `38/50` | `10/10` | `window5:no_override` | `10/10` |

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

- Promotes override policy: `False`.
- Immediate-copy overrides test whether residual window5 drift is mainly a missed-copy problem. The family is promoted only if it reaches exact stable projection coverage under prefix selection.
- The result remains target-text-aware and analysis-only.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
