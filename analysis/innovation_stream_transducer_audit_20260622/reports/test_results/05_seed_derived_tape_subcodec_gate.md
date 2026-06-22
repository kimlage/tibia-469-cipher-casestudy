# Seed Derived Tape Subcodec Gate

Classification: `seed_derived_tape_subcodec_weak_clue`
Translation delta: `NONE`

## Purpose

Convert the seed-coverage clue for the innovation tape into a paid
subcodec: references to substrings in seed books plus literal residual
digits. Compare against raw tape bits and shuffled same-multiset controls.

## Summary

- Literal tape digits: `266`.
- Seed text digits: `1696`.
- Best min length: `5`.
- Best total bits: `1063.761`.
- Best raw bits: `883.633`.
- Best saving vs raw: `-180.128`.
- Best control saving p95: `-249.663`.
- Best copy digits: `87`.
- Best literal digits: `179`.
- Best copy items: `16`.
- Best control coverage p95: `20.050`.
- Promotes seed subcodec: `False`.
- Weak seed subcodec clue: `True`.

This gate prices the promoted seed-coverage structure as a concrete subcodec for the innovation tape: seed substring references plus literal residual digits, compared to raw tape bits and shuffled same-multiset controls.

## Rows

| Min len | Total bits | Raw bits | Saving | Control saving p95 | Copy digits | Literal digits | Copy items | Coverage p95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `3` | `1311.461` | `883.633` | `-427.828` | `-476.718` | `231` | `35` | `63` | `187.050` |
| `4` | `1113.339` | `883.633` | `-229.706` | `-260.511` | `153` | `113` | `34` | `73.000` |
| `5` | `1063.761` | `883.633` | `-180.128` | `-249.663` | `87` | `179` | `16` | `20.050` |

## Decision

- A seed-derived subcodec is promoted only if paid bits beat raw tape and shuffled controls.
- A weak clue may be retained when coverage beats controls but paid bits do not.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
