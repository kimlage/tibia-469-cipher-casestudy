# 124. Item-Type Split-Only Alpha Resweep

Classification: `item_type_split_only_alpha_resweep_retains_current`
Translation delta: `NONE`

## Purpose

After audit 123 promoted split-only item-type coding, this audit retests
the smoothing alpha for that new structural model. The recipe, forced
rules, split at book `6`, copy model, literal model, and address ledger
are fixed.

## Result

- Current formula bits: `8558.667`
- Current alpha: `2`
- Best alpha: `2`
- Best total bits: `8558.667`
- Delta vs current: `0.000` bits

## Top Alpha Rows

| Rank | Alpha | Item bits | Decl delta | Total bits | Delta vs current |
|---:|---:|---:|---:|---:|---:|
| `1` | `2` | `220.287` | `0` | `8558.667` | `0.000` |
| `2` | `1` | `220.595` | `0` | `8558.975` | `0.309` |
| `3` | `3` | `220.473` | `2` | `8560.853` | `2.186` |
| `4` | `4` | `220.829` | `2` | `8561.209` | `2.543` |
| `5` | `5` | `221.265` | `2` | `8561.645` | `2.978` |
| `6` | `6` | `221.741` | `2` | `8562.121` | `3.454` |
| `7` | `7` | `222.239` | `4` | `8564.619` | `5.952` |
| `8` | `8` | `222.747` | `4` | `8565.128` | `6.461` |
| `9` | `9` | `223.261` | `4` | `8565.641` | `6.974` |
| `10` | `10` | `223.776` | `4` | `8566.156` | `7.489` |

## Interpretation

The active `alpha=2` split-only item-type model remains best after
charging alpha declaration deltas. The new `8558.667` compression bound
is retained; no follow-up parameter promotion is justified here.

## Boundary

- No row0/table origin formula is promoted.
- No plaintext, glossary, or authorial-intent claim is introduced.
