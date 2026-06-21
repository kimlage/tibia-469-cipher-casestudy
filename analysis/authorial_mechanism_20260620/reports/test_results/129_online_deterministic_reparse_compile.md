# 129. Online Deterministic Reparse Compile

Classification: `controlled_online_reparse_formula_improvement`
Translation delta: `NONE`

## Purpose

Audits 126-128 showed that deterministic reparsing has predictive suffix
signal but does not promote numeric order as authorial. This compile asks
whether the same deterministic parser can replace the active full-corpus
recipe: each book is parsed using only counts from previously committed
books, then the complete candidate formula is rescored under the active
cost ledger.

## Result

- Active compression bound: `8558.667` bits
- Online reparse candidate: `8343.062` bits
- Delta vs active: `-215.605` bits
- Roundtrip: `70/70`

| Metric | Active | Candidate |
|---|---:|---:|
| Literal runs | `85` | `87` |
| Literal digits | `773` | `857` |
| Copy items | `283` | `261` |
| Copied digits | `10490` | `10406` |

## Interpretation

The deterministic online parser improves the full-corpus charged
formula while preserving roundtrip and all non-semantic boundaries.
This is a mechanical recipe-generation improvement, not a row0 or
plaintext claim.

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_formula_469.json)

## Boundary

- No plaintext or translation is introduced.
- Row0/table origin is unchanged.
- Any promotion is mechanical recipe generation only.
