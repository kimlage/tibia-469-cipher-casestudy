# Chayenne Copy Source Overlap Gate

Classification: `chayenne_copy_source_overlap_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

| Metric | Observed | Control |
| --- | ---: | ---: |
| Copy rows with overlap | `17` | p95 `20`, p99 `23` |
| Total overlap digits | `337` | p95 `333`, p99 `402` |
| Source starts inside spans | `7` | p95 `9` |
| Fully contained copy rows | `4` | p95 `4` |

## Hit Rows

| Book | Op | Source Span | Length | Overlap Digits |
| ---: | ---: | --- | ---: | ---: |
| `10` | `1` | `0-276` | `276` | `36` |
| `13` | `8` | `350-402` | `52` | `10` |
| `14` | `4` | `154-180` | `26` | `20` |
| `16` | `10` | `157-165` | `8` | `5` |
| `19` | `1` | `148-196` | `48` | `36` |
| `20` | `1` | `190-196` | `6` | `6` |
| `20` | `2` | `180-190` | `10` | `10` |
| `22` | `0` | `274-411` | `137` | `13` |
| `23` | `9` | `356-379` | `23` | `4` |
| `27` | `0` | `147-271` | `124` | `36` |
| `31` | `1` | `177-221` | `44` | `19` |
| `31` | `3` | `147-177` | `30` | `17` |
| `31` | `5` | `158-210` | `52` | `36` |
| `34` | `7` | `183-188` | `5` | `5` |
| `35` | `1` | `147-274` | `127` | `36` |
| `41` | `2` | `142-207` | `65` | `36` |
| `42` | `2` | `347-359` | `12` | `12` |

## Decision

`Chayenne seed subspans are not overrepresented as copy-source intervals after same-length controls`

Next blocker: `copy-source overlap alone does not derive source choice, event policy, or innovation origin`

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
