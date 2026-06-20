# 123. Item-Type Split-Only Formula Compile

Classification: `controlled_item_type_split_only_formula_improvement`
Translation delta: `NONE`

## Purpose

Audit 121 found that item-type `split6_only` predicts prefix holdouts
better than the active split-plus-previous-item context. This compile
tests whether that simpler component can be promoted as a decodable
full-corpus formula under the active recipe and a conservative unchanged
item-type declaration charge.

## Result

- Active compression bound: `8561.792` bits
- Split-only candidate: `8558.667` bits
- Gain vs active: `3.125` bits
- Candidate with one extra declaration bit: `8559.667` bits
- Gain with one extra declaration bit: `2.125` bits
- Roundtrip: `70/70`

## Component

| Component | Active bits | Split-only bits | Gain |
|---|---:|---:|---:|
| `item_type` | `223.412` | `220.287` | `3.125` |

## Interpretation

The simpler item-type model is not just a holdout explanation: under the
same declaration charge it also improves the full-corpus mechanical code.
It remains a book-generation formula change only. It does not explain
row0, introduce plaintext, or make an authorial-intent claim.

## Boundary

- Recipe, copy addresses, copy lengths, literal lengths, and literal payload
  model are unchanged.
- Forced item-type rules remain enforced.
- `translation_delta`: `NONE`.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_param_minaddr_repair2_formula_469.json](../../sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_param_minaddr_repair2_formula_469.json)
