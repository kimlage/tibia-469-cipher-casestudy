# 122. Simplified Generation Profile Compile

Classification: `simplified_generation_profile_costs_more_than_compression_bound`
Translation delta: `NONE`

## Purpose

Audit 121 found that some simpler component contexts predict prefix
holdouts better than the active compression-bound contexts. This compile
measures that simplified generation profile on the full 70-book corpus
while preserving the same recipe and 70/70 roundtrip validation.

## Result

- Active compression bound: `8561.792` bits
- Simplified generation profile: `8613.581` bits
- Delta vs compression bound: `51.789` bits
- Roundtrip: `70/70`
- Cost basis: stream-substitution profile over the active validated
  recipe and fixed declaration ledger; not a promoted re-declared
  compression formula.

## Component Deltas

| Component | Active | Simplified profile | Active bits | Simplified bits | Delta |
|---|---|---|---:|---:|---:|
| `literal_payload` | `active_order2` | `order1_previous_digit` | `2434.095` | `2489.009` | `54.914` |
| `item_type` | `active_split6_prev1` | `split6_only` | `223.412` | `220.287` | `-3.125` |

## Interpretation

The simplified profile is not promoted as a new lower MDL bound. It costs
more on the full corpus because the active formula is still the best
charged post-hoc code. Its value is explanatory: it records the simpler
component choices that generalize better under prefix holdout.

## Boundary

- `compression_bound` remains the active `8561.792` bit formula.
- `generation_explanation_profile` is compiled but not a stronger code.
- No row0/table origin formula is promoted.
- No plaintext, glossary, or authorial-intent claim is introduced.
