# 150. Optional Literal Copy Repair Frontier

Classification: `optional_literal_copy_repairs_rejected_active_parser_retained`
Translation delta: `NONE`

## Purpose

Audit 149 localized the residual literal parser frontier to optional
literal starts where copy candidates exist. This audit tests the
lowest-risk repair family: replace a prefix of one optional literal run
with a legal prior copy, leaving any literal suffix intact, then rescore
the complete active ledger.

## Scope

- Active total bits declared: `8177.317`
- Active total bits recomputed: `8177.317`
- Optional literal starts from audit 149: `14`
- Eligible starts with in-literal legal copy length: `5`
- Candidate repairs scored: `74`

## Eligible Starts

| Book | Op | Pos | Literal len | Candidates | Max copy len | Preview |
|---:|---:|---:|---:|---:|---:|---|
| `8` | `4` | `103` | `19` | `4` | `5` | `4519121128883046467` |
| `16` | `6` | `144` | `7` | `9` | `6` | `6512887` |
| `30` | `1` | `17` | `6` | `17` | `6` | `800364` |
| `39` | `0` | `0` | `7` | `1` | `5` | `5765219` |
| `44` | `0` | `0` | `5` | `27` | `18` | `21972` |

## Best Candidates

| Rank | Delta bits | Total bits | Book | Op | Source | Copy len | Literal remainder |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `1` | `1.180` | `8178.496` | `30` | `1` | `3395` | `6` | `0` |
| `2` | `1.180` | `8178.496` | `30` | `1` | `255` | `6` | `0` |
| `3` | `1.180` | `8178.496` | `30` | `1` | `1317` | `6` | `0` |
| `4` | `1.180` | `8178.496` | `30` | `1` | `1956` | `6` | `0` |
| `5` | `1.180` | `8178.496` | `30` | `1` | `2226` | `6` | `0` |
| `6` | `1.180` | `8178.496` | `30` | `1` | `2252` | `6` | `0` |
| `7` | `1.180` | `8178.496` | `30` | `1` | `3226` | `6` | `0` |
| `8` | `1.180` | `8178.496` | `30` | `1` | `3520` | `6` | `0` |
| `9` | `1.180` | `8178.496` | `30` | `1` | `3792` | `6` | `0` |
| `10` | `1.180` | `8178.496` | `30` | `1` | `3941` | `6` | `0` |

## Decision

- Improving candidates: `0`
- Best candidate is still `1.180` bits worse than active.
- The active parser is retained for this repair family.
- Compression bound unchanged.
- Row0 origin, plaintext, and semantic status unchanged.

## Interpretation

The optional literal starts are not automatically mistakes. Under the
active cost ledger, every tested in-literal copy repair is worse than
the current parser choice. This closes the simplest residual repair
frontier left by audit 149; broader repairs that cross op boundaries
would need separate charging and controls.
