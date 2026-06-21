# Book-Start Copy Subclass Gate

Classification: `book_start_copy_subclass_weak_clue_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 54 tests whether the residual subclass where an active
literal at book start should instead be a copy has an observable
subrule. It does not use `drift_class` as a predicate; the firing
condition is limited to book-start literal state plus observable
copy-candidate features.

## Summary

- Decisions: `234`.
- Rules tested: `105072`.
- Residual decisions: `10`.
- Book-start copy residuals: `3`.
- Best predicate: `min_start_distance__len_ge_5__payload_ge_1__interval_le_4__active_literal_len_le_98`.
- Best book-start copy hits: `3/3`.
- Best residual hits overall: `3/10`.
- Best clean false changes: `6`.
- Best zero-FP predicate: `min_start_distance__len_ge_5__payload_ge_1__interval_le_4__active_literal_len_le_1`.
- Best zero-FP book-start copy hits: `1/3`.
- Best priced bits: `88.031`.
- Best priced net vs lookup: `8.670`.
- Random p(>= observed): `1.000`.
- Promotes parser rule: `False`.

## Cost Rows

| Predicate | Book-start hits | Residual hits | Clean false changes | Total bits | Net vs lookup |
|---|---:|---:|---:|---:|---:|
| `min_start_distance__len_ge_5__payload_ge_1__interval_le_4__active_literal_len_le_98` | `3` | `3` | `6` | `111.782` | `32.421` |
| `min_start_distance__len_ge_5__payload_ge_1__interval_le_4__active_literal_len_le_1` | `1` | `1` | `0` | `88.031` | `8.670` |

## Prefix/Holdout

| Cutoff | Selected predicate | Train residual hits | Test residual hits | Test clean false changes | Oracle test book-start hits | Matches oracle |
|---:|---|---:|---:|---:|---:|---:|
| `20` | `min_start_distance__len_ge_9__payload_ge_9__interval_le_4` | `0/2` | `0/8` | `2` | `3` | `False` |
| `30` | `min_start_distance__len_ge_9__payload_ge_1__interval_le_4` | `2/5` | `0/5` | `3` | `1` | `False` |
| `40` | `min_start_distance__len_ge_5__payload_ge_1__interval_le_4__active_literal_len_le_98` | `3/7` | `0/3` | `3` | `0` | `False` |
| `50` | `min_start_distance__len_ge_5__payload_ge_1__interval_le_4__active_literal_len_le_98` | `3/8` | `0/2` | `2` | `0` | `False` |
| `60` | `min_start_distance__len_ge_5__payload_ge_1__interval_le_4__active_literal_len_le_98` | `3/10` | `0/0` | `1` | `0` | `False` |

## Selected Rows Under Best Predicate

| Book | Op | Kind | Class | Active | Stable | Chosen | Hit | Payload occ. | Interval distance |
|---:|---:|---|---|---|---|---|---:|---:|---:|
| `10` | `0` | `clean_control` | `None` | `{'type': 'literal', 'target_start': 0, 'length': 5, 'source': None}` | `{'type': 'literal', 'target_start': 0, 'length': 5, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 5, 'source': 1595}` | `False` | `6` | `2` |
| `12` | `0` | `clean_control` | `None` | `{'type': 'literal', 'target_start': 0, 'length': 2, 'source': None}` | `{'type': 'literal', 'target_start': 0, 'length': 2, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 5, 'source': 171}` | `False` | `12` | `3` |
| `21` | `0` | `residual_first_drift` | `book_start_copy_missed_as_literal` | `{'type': 'literal', 'target_start': 0, 'length': 7, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 9, 'source': 197}` | `{'type': 'copy', 'target_start': 0, 'length': 9, 'source': 197}` | `True` | `4` | `4` |
| `25` | `0` | `clean_control` | `None` | `{'type': 'literal', 'target_start': 0, 'length': 3, 'source': None}` | `{'type': 'literal', 'target_start': 0, 'length': 3, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 5, 'source': 101}` | `False` | `16` | `2` |
| `26` | `0` | `residual_first_drift` | `book_start_copy_missed_as_literal` | `{'type': 'literal', 'target_start': 0, 'length': 1, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 11, 'source': 3054}` | `{'type': 'copy', 'target_start': 0, 'length': 11, 'source': 3054}` | `True` | `1` | `4` |
| `39` | `0` | `residual_first_drift` | `book_start_copy_missed_as_literal` | `{'type': 'literal', 'target_start': 0, 'length': 7, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 5, 'source': 2520}` | `{'type': 'copy', 'target_start': 0, 'length': 5, 'source': 2520}` | `True` | `1` | `4` |
| `44` | `0` | `clean_control` | `None` | `{'type': 'literal', 'target_start': 0, 'length': 5, 'source': None}` | `{'type': 'literal', 'target_start': 0, 'length': 5, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 5, 'source': 2195}` | `False` | `27` | `2` |
| `52` | `0` | `clean_control` | `None` | `{'type': 'literal', 'target_start': 0, 'length': 3, 'source': None}` | `{'type': 'literal', 'target_start': 0, 'length': 3, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 5, 'source': 2192}` | `False` | `59` | `2` |
| `65` | `0` | `clean_control` | `None` | `{'type': 'literal', 'target_start': 0, 'length': 3, 'source': None}` | `{'type': 'literal', 'target_start': 0, 'length': 3, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 5, 'source': 4511}` | `False` | `7` | `2` |

## Interpretation

The subclass has visible signal, but it is still not a promoted
segmentation rule unless it clears all gates at once: no clean
false changes, lower paid description than residual lookup, and
stable prefix/holdout behavior. This gate therefore keeps the
result as weak/audit-only when the signal is local or post-hoc.
