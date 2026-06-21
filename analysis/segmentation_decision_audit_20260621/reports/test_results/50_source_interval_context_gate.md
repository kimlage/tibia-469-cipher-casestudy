# Source Interval Context Gate

Classification: `source_interval_context_weak_clue_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 50 tests whether the remaining branch choices are selected
by source-side content structure: copied payload recurrence,
source interval boundary recurrence, or source-target neighborhood
similarity around the start/end of a candidate copy interval.

The test uses observable branches from the residual branch
continuation audit. It does not use plaintext, row0 semantics,
or compression-bound retuning.

## Summary

- Decisions: `234`.
- Residual decisions: `10`.
- Clean controls: `224`.
- Policies tested: `12`.
- Active baseline residual hits: `0/10`.
- Best policy: `min_source_target_start_distance`.
- Best residual hits: `5/10`.
- Best clean false changes: `189`.
- Random p(>= observed): `0.002`.

## Scoreboard

| Policy | Residual hits | Total hits | Clean false changes | Copy branches selected |
|---|---:|---:|---:|---:|
| `min_source_target_start_distance` | `5/10` | `40/234` | `189` | `200` |
| `max_payload_occurrences` | `5/10` | `40/234` | `189` | `200` |
| `min_source_context_recurrence` | `4/10` | `69/234` | `159` | `200` |
| `max_context_recurrence_r8` | `4/10` | `66/234` | `162` | `200` |
| `max_context_recurrence_r4` | `3/10` | `65/234` | `162` | `200` |
| `max_context_recurrence_r2` | `2/10` | `46/234` | `180` | `200` |
| `max_source_context_recurrence` | `2/10` | `44/234` | `182` | `200` |
| `min_interval_distance_r8` | `2/10` | `16/234` | `210` | `200` |
| `min_source_target_interval_distance` | `2/10` | `7/234` | `219` | `200` |
| `min_source_target_end_distance` | `2/10` | `7/234` | `219` | `200` |
| `min_interval_distance_r4` | `2/10` | `7/234` | `219` | `200` |
| `min_interval_distance_r2` | `2/10` | `7/234` | `219` | `200` |

## Prefix/Holdout

| Cutoff | Selected policy | Train residual hits | Test residual hits | Test clean false changes | Oracle test policy | Oracle test residual hits |
|---:|---|---:|---:|---:|---|---:|
| `20` | `min_source_context_recurrence` | `0/2` | `4/8` | `110` | `min_source_target_start_distance` | `5/8` |
| `30` | `min_source_target_start_distance` | `3/5` | `2/5` | `118` | `max_context_recurrence_r4` | `2/5` |
| `40` | `min_source_target_start_distance` | `5/7` | `0/3` | `80` | `max_context_recurrence_r4` | `0/3` |
| `50` | `min_source_target_start_distance` | `5/8` | `0/2` | `46` | `max_context_recurrence_r4` | `0/2` |
| `60` | `min_source_target_start_distance` | `5/10` | `0/0` | `19` | `min_source_context_recurrence` | `0/0` |

## Residual Rows Under Best Policy

| Book | Op | Class | Active | Stable | Chosen | Hit | Payload occ. | Interval distance | Context recurrence |
|---:|---:|---|---|---|---|---:|---:|---:|---:|
| `14` | `0` | `literal_understop` | `{'type': 'literal', 'target_start': 0, 'length': 27, 'source': None}` | `{'type': 'literal', 'target_start': 0, 'length': 39, 'source': None}` | `{'type': 'literal', 'target_start': 0, 'length': 133, 'source': None}` | `False` | `0` | `1000000000` | `0` |
| `16` | `9` | `copy_started_inside_stable_literal` | `{'type': 'copy', 'target_start': 164, 'length': 8, 'source': 473}` | `{'type': 'literal', 'target_start': 164, 'length': 1, 'source': None}` | `{'type': 'copy', 'target_start': 164, 'length': 8, 'source': 473}` | `False` | `4` | `4` | `4` |
| `20` | `2` | `internal_copy_missed_as_literal` | `{'type': 'literal', 'target_start': 21, 'length': 3, 'source': None}` | `{'type': 'copy', 'target_start': 21, 'length': 10, 'source': 180}` | `{'type': 'copy', 'target_start': 21, 'length': 10, 'source': 180}` | `True` | `4` | `3` | `4` |
| `21` | `0` | `book_start_copy_missed_as_literal` | `{'type': 'literal', 'target_start': 0, 'length': 7, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 9, 'source': 197}` | `{'type': 'copy', 'target_start': 0, 'length': 9, 'source': 197}` | `True` | `4` | `4` | `3` |
| `26` | `0` | `book_start_copy_missed_as_literal` | `{'type': 'literal', 'target_start': 0, 'length': 1, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 11, 'source': 3054}` | `{'type': 'copy', 'target_start': 0, 'length': 11, 'source': 3054}` | `True` | `1` | `4` | `1` |
| `34` | `7` | `internal_copy_missed_as_literal` | `{'type': 'literal', 'target_start': 105, 'length': 5, 'source': None}` | `{'type': 'copy', 'target_start': 105, 'length': 5, 'source': 183}` | `{'type': 'copy', 'target_start': 105, 'length': 5, 'source': 183}` | `True` | `14` | `4` | `27` |
| `39` | `0` | `book_start_copy_missed_as_literal` | `{'type': 'literal', 'target_start': 0, 'length': 7, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 5, 'source': 2520}` | `{'type': 'copy', 'target_start': 0, 'length': 5, 'source': 2520}` | `True` | `1` | `4` | `18` |
| `45` | `1` | `internal_copy_missed_as_literal` | `{'type': 'literal', 'target_start': 62, 'length': 1, 'source': None}` | `{'type': 'copy', 'target_start': 62, 'length': 8, 'source': 2850}` | `{'type': 'copy', 'target_start': 62, 'length': 5, 'source': 2850}` | `False` | `13` | `1` | `2` |
| `55` | `2` | `copy_length_drift_same_source` | `{'type': 'copy', 'target_start': 67, 'length': 45, 'source': 2757}` | `{'type': 'copy', 'target_start': 67, 'length': 44, 'source': 2757}` | `{'type': 'copy', 'target_start': 67, 'length': 5, 'source': 2757}` | `False` | `3` | `2` | `12` |
| `57` | `2` | `literal_understop` | `{'type': 'literal', 'target_start': 69, 'length': 17, 'source': None}` | `{'type': 'literal', 'target_start': 69, 'length': 28, 'source': None}` | `{'type': 'literal', 'target_start': 69, 'length': 161, 'source': None}` | `False` | `0` | `1000000000` | `0` |

## Decision

- Promotes source-interval context parser: `False`.
- Prequential cover-all-residual cells: `0/4`.
- Prequential zero-clean-false-change cells: `0/5`.
- Gate 50 tests whether source interval context, payload recurrence, or source-target neighborhood similarity selects the remaining branch choices. It is a source/content structural test, not a compression sweep.
- Source interval context does not remove the remaining source/length dependency.
- The result is analysis-only and does not change the compression bound.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
