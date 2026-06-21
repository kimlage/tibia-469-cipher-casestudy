# Integrated Parser Policy and Drift Audit

Classification: `integrated_parser_policy_prequential_partial_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 08 improved full greedy parsing from `39/60` to `46/60`, but
left `14` drift books. This gate tests whether that drift is just a
bad stop-policy hyperparameter inside the same local-peak family, and
maps the residual first-diff topology.

## Policy Scoreboard

- Policies tested: `25`.
- First-match exact books: `39/60`.
- Active gate-08 policy `max_copy_length:window6` exact books: `46/60`.
- Best full-corpus policy `max_copy_length:window5` exact books: `48/60`.
- Exact-book improvement vs active: `2`.

| Policy | Exact books | Literal gaps | Literal digits | Drift classes |
|---|---:|---:|---:|---|
| `max_copy_length:window5` | `48/60` | `66` | `265` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}` |
| `max_copy_length:window6` | `46/60` | `69` | `329` | `{'book_start_copy_missed_as_literal': 4, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 6, 'literal_overstop': 1, 'literal_understop': 2}` |
| `max_copy_length:window3` | `44/60` | `61` | `214` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 3, 'internal_copy_missed_as_literal': 3, 'literal_understop': 6}` |
| `max_copy_length:window4` | `44/60` | `64` | `235` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 3, 'internal_copy_missed_as_literal': 3, 'literal_understop': 6}` |
| `total_advance:window3` | `44/60` | `64` | `249` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 3, 'literal_overstop': 2, 'literal_understop': 5}` |
| `total_advance:window5` | `43/60` | `68` | `359` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 5, 'literal_overstop': 4, 'literal_understop': 4}` |
| `total_advance:window4` | `42/60` | `67` | `292` | `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 2, 'internal_copy_missed_as_literal': 4, 'literal_overstop': 3, 'literal_understop': 5}` |
| `total_advance:window6` | `42/60` | `66` | `429` | `{'book_start_copy_missed_as_literal': 4, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 7, 'literal_overstop': 6}` |
| `max_copy_length:window2` | `41/60` | `55` | `186` | `{'book_start_copy_missed_as_literal': 2, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 8, 'internal_copy_missed_as_literal': 2, 'literal_understop': 6}` |
| `total_advance:window2` | `41/60` | `59` | `209` | `{'book_start_copy_missed_as_literal': 2, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 7, 'internal_copy_missed_as_literal': 2, 'literal_overstop': 1, 'literal_understop': 6}` |
| `max_copy_length:window7` | `40/60` | `72` | `389` | `{'book_start_copy_missed_as_literal': 6, 'copy_length_drift_same_source': 1, 'internal_copy_missed_as_literal': 7, 'literal_overstop': 4, 'literal_understop': 2}` |
| `total_advance:window1` | `40/60` | `54` | `180` | `{'book_start_copy_missed_as_literal': 2, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 10, 'internal_copy_missed_as_literal': 1, 'literal_understop': 6}` |

## Prequential Policy Selection

| Cutoff | Selected | Train hits | Test hits | Oracle | Oracle test hits |
|---:|---|---:|---:|---|---:|
| `20` | `max_copy_length:window5` | `8/10` | `40/50` | `max_copy_length:window5` | `40/50` |
| `30` | `max_copy_length:window5` | `14/20` | `34/40` | `max_copy_length:window5` | `34/40` |
| `40` | `max_copy_length:window5` | `22/30` | `26/30` | `max_copy_length:window5` | `26/30` |
| `50` | `max_copy_length:window5` | `30/40` | `18/20` | `max_copy_length:window5` | `18/20` |
| `60` | `max_copy_length:window5` | `38/50` | `10/10` | `max_copy_length:window5` | `10/10` |

## Active Drift Topology

- Active mismatch books: `[14, 16, 20, 21, 26, 28, 30, 34, 36, 39, 45, 55, 57, 63]`.
- Active drift classes: `{'literal_understop': 2, 'internal_copy_missed_as_literal': 6, 'book_start_copy_missed_as_literal': 4, 'literal_overstop': 1, 'copy_length_drift_same_source': 1}`.

| Book | Class | First diff |
|---:|---|---|
| `14` | `literal_understop` | `{"index": 0, "predicted": {"length": 18, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 39, "source": null, "target_start": 0, "type": "literal"}}` |
| `16` | `internal_copy_missed_as_literal` | `{"index": 6, "predicted": {"length": 7, "source": null, "target_start": 144, "type": "literal"}, "stable_projection": {"length": 6, "source": 274, "target_start": 144, "type": "copy"}}` |
| `20` | `internal_copy_missed_as_literal` | `{"index": 1, "predicted": {"length": 9, "source": null, "target_start": 15, "type": "literal"}, "stable_projection": {"length": 6, "source": 190, "target_start": 15, "type": "copy"}}` |
| `21` | `book_start_copy_missed_as_literal` | `{"index": 0, "predicted": {"length": 7, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 9, "source": 197, "target_start": 0, "type": "copy"}}` |
| `26` | `book_start_copy_missed_as_literal` | `{"index": 0, "predicted": {"length": 1, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 11, "source": 3054, "target_start": 0, "type": "copy"}}` |
| `28` | `internal_copy_missed_as_literal` | `{"index": 1, "predicted": {"length": 6, "source": null, "target_start": 89, "type": "literal"}, "stable_projection": {"length": 7, "source": 2778, "target_start": 89, "type": "copy"}}` |
| `30` | `internal_copy_missed_as_literal` | `{"index": 1, "predicted": {"length": 6, "source": null, "target_start": 17, "type": "literal"}, "stable_projection": {"length": 6, "source": 255, "target_start": 17, "type": "copy"}}` |
| `34` | `literal_overstop` | `{"index": 0, "predicted": {"length": 10, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 4, "source": null, "target_start": 0, "type": "literal"}}` |
| `36` | `internal_copy_missed_as_literal` | `{"index": 4, "predicted": {"length": 6, "source": null, "target_start": 78, "type": "literal"}, "stable_projection": {"length": 7, "source": 2327, "target_start": 78, "type": "copy"}}` |
| `39` | `book_start_copy_missed_as_literal` | `{"index": 0, "predicted": {"length": 7, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 5, "source": 2520, "target_start": 0, "type": "copy"}}` |
| `45` | `internal_copy_missed_as_literal` | `{"index": 1, "predicted": {"length": 1, "source": null, "target_start": 62, "type": "literal"}, "stable_projection": {"length": 8, "source": 2850, "target_start": 62, "type": "copy"}}` |
| `55` | `copy_length_drift_same_source` | `{"index": 2, "predicted": {"length": 45, "source": 2757, "target_start": 67, "type": "copy"}, "stable_projection": {"length": 44, "source": 2757, "target_start": 67, "type": "copy"}}` |
| `57` | `literal_understop` | `{"index": 2, "predicted": {"length": 11, "source": null, "target_start": 69, "type": "literal"}, "stable_projection": {"length": 28, "source": null, "target_start": 69, "type": "literal"}}` |
| `63` | `book_start_copy_missed_as_literal` | `{"index": 0, "predicted": {"length": 6, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 47, "source": 6978, "target_start": 0, "type": "copy"}}` |

## Decision

- Promotes integrated parser policy: `False`.
- Retuning the simple local-peak stop family from confirmation window 6 to 5 is prefix-stable and reduces drift, but it still does not remove integrated parser drift or reach exact stable projection coverage.
- The result remains target-text-aware and analysis-only.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
