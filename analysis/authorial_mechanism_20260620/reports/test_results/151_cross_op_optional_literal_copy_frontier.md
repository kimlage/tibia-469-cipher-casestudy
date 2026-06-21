# 151. Cross-Op Optional Literal Copy Frontier

Classification: `cross_op_optional_literal_copy_repairs_rejected_active_parser_retained`
Translation delta: `NONE`

## Purpose

Audit 150 rejected copy-prefix repairs contained inside one optional
literal run. This audit tests the next broader repair family: a copy
candidate at an optional literal start may cross the literal boundary
and consume part of following operations, after which the remaining
recipe is trimmed conservatively and rescored under the active ledger.

## Scope

- Active total bits recomputed: `8177.317`
- Optional literal starts: `14`
- Cross-op candidates attempted: `465`
- Valid cross-op candidates: `465`
- Invalid generated candidates: `0`

## Best Candidates

| Rank | Delta bits | Total bits | Book | Op | Source | Copy len | Crossed digits |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `1` | `0.027` | `8177.344` | `12` | `8` | `102` | `11` | `7` |
| `2` | `0.027` | `8177.344` | `12` | `8` | `1803` | `11` | `7` |
| `3` | `0.095` | `8177.412` | `12` | `8` | `367` | `6` | `2` |
| `4` | `0.096` | `8177.413` | `12` | `8` | `701` | `6` | `2` |
| `5` | `0.633` | `8177.950` | `44` | `0` | `101` | `12` | `7` |
| `6` | `1.047` | `8178.364` | `44` | `0` | `101` | `8` | `3` |
| `7` | `1.096` | `8178.413` | `12` | `8` | `102` | `6` | `2` |
| `8` | `1.096` | `8178.413` | `12` | `8` | `785` | `6` | `2` |
| `9` | `1.096` | `8178.413` | `12` | `8` | `1408` | `6` | `2` |
| `10` | `1.096` | `8178.413` | `12` | `8` | `1492` | `6` | `2` |

## Decision

- Improving candidates: `0`
- Best candidate is `0.027` bits worse than active.
- Compression bound unchanged.
- Active parser retained for this repair family.
- Row0 origin, plaintext, and semantic status unchanged.

## Interpretation

Allowing the copy to cross the optional literal boundary does not rescue
the residual literal frontier. Every valid cross-op repair is worse
than the active parser choice under the same active ledger. This closes
the immediate extension of audit 150; future repair tests should move
to explicitly reparsing a bounded suffix, not ad hoc local copy swaps.
