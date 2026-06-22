# Book-Opcount Start-Anchor Program Gate

Classification: `WEAK_BOOK_OPCOUNT_START_ANCHOR_CLUE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can decoded book-level `op_count` decide when start-only source-boundary anchors are active, reducing v4 without enabling the full cascade everywhere?

## Summary

- Best rule: `op_count_le_3`.
- Rule family size: `16`; declaration bits: `4.000`.
- Delta before declaration vs v4: `-25.957` bits.
- Delta after declaration vs v4: `-21.957` bits.
- Candidate external bits excluding seed: `4087.182`.
- Fixed `op_count_le_3` positive splits: `4/5`.
- Fixed `op_count_le_3` aggregate test delta: `-60.727` bits.
- Prefix-selected positive splits: `3/5`.
- Prefix-selected aggregate test delta: `-22.552` bits.

## Random Op-Count Control

- Observed best saving: `25.957` bits.
- Random p50/p95/p99 saving: `17.921` / `29.826` / `32.603`.
- Beats random p95: `False`.

## Rule Costs

| Rule | Enabled books | Delta before declaration | Delta after declaration |
| --- | ---: | ---: | ---: |
| `none` | `0` | `0.000` | `4.000` |
| `all` | `60` | `-16.722` | `-12.722` |
| `op_count_le_1` | `12` | `0.899` | `4.899` |
| `op_count_le_2` | `25` | `-9.226` | `-5.226` |
| `op_count_le_3` | `35` | `-25.957` | `-21.957` |
| `op_count_le_4` | `40` | `-23.171` | `-19.171` |
| `op_count_le_5` | `42` | `-23.287` | `-19.287` |
| `op_count_le_6` | `46` | `-21.941` | `-17.941` |
| `op_count_le_7` | `48` | `-22.158` | `-18.158` |
| `op_count_le_8` | `51` | `-9.525` | `-5.525` |
| `op_count_le_9` | `53` | `-11.793` | `-7.793` |
| `op_count_le_10` | `54` | `-11.793` | `-7.793` |
| `op_count_le_11` | `55` | `-11.793` | `-7.793` |
| `op_count_le_12` | `59` | `-14.652` | `-10.652` |
| `op_count_le_13` | `59` | `-14.652` | `-10.652` |
| `op_count_le_14` | `60` | `-16.722` | `-12.722` |

## Fixed Holdout

| Cutoff | Train delta | Test delta |
| ---: | ---: | ---: |
| `20` | `-1.952` | `-24.005` |
| `30` | `-9.831` | `-16.126` |
| `40` | `-14.242` | `-11.715` |
| `50` | `-16.330` | `-9.627` |
| `60` | `-26.704` | `0.747` |

## Decision

`WEAK_BOOK_OPCOUNT_START_ANCHOR_CLUE`: the rule reduces v4 and has fixed holdout support, but does not beat random-opcount p95.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
