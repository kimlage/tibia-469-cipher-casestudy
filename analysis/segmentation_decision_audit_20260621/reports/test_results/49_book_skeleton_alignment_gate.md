# Book Skeleton Alignment Gate

Classification: `book_skeleton_alignment_rejected`
Translation delta: `NONE`

## Purpose

Gate 49 tests a book-level parser hypothesis: perhaps the
remaining residual `(source,length)` decisions are selected
by alignment to operation skeletons from books already parsed
exactly, not by a local branch feature.

Credit is stricter than type/length label matching. A residual
hit counts only when the predicted type/length maps to one
unique observable branch at the site, so source choice is not
silently granted by the stable projection.

## Summary

- Exact books used as skeleton source: `50`.
- Residual books: `10`.
- Decisions: `234`.
- Configurations tested: `27`.
- Best family: `full_edit_type_only`.
- Best k: `5`.
- Best residual unique-branch hits: `0/10`.
- Best residual label hits: `0/10`.
- Best clean false changes: `211`.
- Unsupported predictions: `0`.
- Non-unique branch predictions: `113`.
- Shuffle p(>= observed): `1.000`.

## Scoreboard

| Family | k | Residual unique branch hits | Residual label hits | Clean false changes | Unsupported | Non-unique |
|---|---:|---:|---:|---:|---:|---:|
| `full_edit_type_only` | `5` | `0/10` | `0/10` | `211` | `0` | `113` |
| `tail3_type_only` | `5` | `0/10` | `0/10` | `213` | `0` | `101` |
| `full_edit_type_only` | `3` | `0/10` | `0/10` | `213` | `0` | `121` |
| `tail3_type_only` | `3` | `0/10` | `0/10` | `214` | `0` | `103` |
| `tail5_type_only` | `5` | `0/10` | `0/10` | `214` | `0` | `104` |
| `tail5_type_only` | `3` | `0/10` | `0/10` | `214` | `0` | `110` |
| `full_edit_type_only` | `1` | `0/10` | `0/10` | `218` | `0` | `125` |
| `tail3_type_len_bucket` | `3` | `0/10` | `0/10` | `218` | `0` | `129` |
| `full_edit_type_len_bucket` | `1` | `0/10` | `0/10` | `218` | `0` | `144` |
| `tail5_type_len_bucket` | `1` | `0/10` | `0/10` | `218` | `0` | `150` |
| `full_edit_exact_len` | `5` | `0/10` | `0/10` | `219` | `0` | `117` |
| `tail3_type_len_bucket` | `5` | `0/10` | `0/10` | `219` | `0` | `125` |

## Prefix/Holdout

| Cutoff | Selected family | k | Test residual unique hits | Test residual label hits | Test clean false changes | Unsupported | Non-unique |
|---:|---|---:|---:|---:|---:|---:|---:|
| `20` | `tail3_type_only` | `3` | `0/8` | `0/8` | `151` | `0` | `52` |
| `30` | `full_edit_type_len_bucket` | `1` | `0/5` | `0/5` | `123` | `0` | `75` |
| `40` | `full_edit_type_only` | `5` | `0/3` | `0/3` | `83` | `0` | `40` |
| `50` | `full_edit_type_only` | `5` | `0/2` | `0/2` | `48` | `0` | `17` |
| `60` | `full_edit_type_only` | `5` | `0/0` | `0/0` | `20` | `0` | `4` |

## Residual Rows Under Best Config

| Book | Op | Class | Active | Stable | Predicted | Label hit | Unique branch hit | Branch matches |
|---:|---:|---|---|---|---|---:|---:|---:|
| `14` | `0` | `literal_understop` | `('literal', 27)` | `('literal', 39)` | `('literal', 6)` | `False` | `False` | `0` |
| `16` | `9` | `copy_started_inside_stable_literal` | `('copy', 8)` | `('literal', 1)` | `('copy', 52)` | `False` | `False` | `0` |
| `20` | `2` | `internal_copy_missed_as_literal` | `('literal', 3)` | `('copy', 10)` | `('copy', 7)` | `False` | `False` | `0` |
| `21` | `0` | `book_start_copy_missed_as_literal` | `('literal', 7)` | `('copy', 9)` | `('literal', 6)` | `False` | `False` | `1` |
| `26` | `0` | `book_start_copy_missed_as_literal` | `('literal', 1)` | `('copy', 11)` | `('literal', 6)` | `False` | `False` | `1` |
| `34` | `7` | `internal_copy_missed_as_literal` | `('literal', 5)` | `('copy', 5)` | `('literal', 4)` | `False` | `False` | `0` |
| `39` | `0` | `book_start_copy_missed_as_literal` | `('literal', 7)` | `('copy', 5)` | `('literal', 6)` | `False` | `False` | `1` |
| `45` | `1` | `internal_copy_missed_as_literal` | `('literal', 1)` | `('copy', 8)` | `('literal', 2)` | `False` | `False` | `1` |
| `55` | `2` | `copy_length_drift_same_source` | `('copy', 45)` | `('copy', 44)` | `('copy', 7)` | `False` | `False` | `0` |
| `57` | `2` | `literal_understop` | `('literal', 17)` | `('literal', 28)` | `('copy', 7)` | `False` | `False` | `0` |

## Decision

- Promotes book-skeleton alignment parser: `False`.
- Prequential cover-all-residual cells: `0/4`.
- Prequential zero-clean-false-change cells: `0/5`.
- Gate 49 tests whether the remaining residual branch choices are recoverable from book-level operation skeleton alignment against exact books. Credit for source/length reduction is granted only when the predicted type/length maps to a unique observable branch at the decision site.
- Book-level skeleton alignment does not remove the remaining source/length dependency.
- The result is analysis-only and does not change the compression bound.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
