# Seed Walk Source Model Gate

Classification: `seed_walk_source_model_rejected`
Translation delta: `NONE`

## Purpose

Test whether seed-derived references in the innovation tape can use a
source-position walk instead of paying absolute source addresses for every
copy item.

## Summary

- Literal tape digits: `266`.
- Seed text digits: `1696`.
- Best min length: `5`.
- Best Rice k: `8`.
- Best walk total bits: `1106.842`.
- Best absolute total bits: `1063.761`.
- Best raw bits: `883.633`.
- Best walk saving vs raw: `-223.209`.
- Best walk saving vs absolute: `-43.081`.
- Best control walk-vs-raw p95: `-252.491`.
- Best control walk-vs-absolute p95: `0.456`.
- Best copy digits: `87`.
- Best copy items: `16`.
- Best negative deltas: `9`.
- Promotes seed-walk subcodec: `False`.
- Weak seed-walk clue: `False`.

This gate asks whether seed references in the innovation tape form a cheaper source-position walk than absolute source declarations, and whether that walk becomes a paid subcodec against raw tape and shuffled controls. Coverage can still beat controls while the walk itself is rejected if it costs more than absolute source positions.

## Rows

| Min len | k | Walk bits | Absolute bits | Raw bits | Walk saving raw | Walk saving abs | Control raw p95 | Control abs p95 | Copy digits | Copy items |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `3` | `8` | `1355.330` | `1311.461` | `883.633` | `-471.697` | `-43.869` | `-518.583` | `-19.511` | `231` | `63` |
| `4` | `8` | `1146.317` | `1113.339` | `883.633` | `-262.684` | `-32.979` | `-268.930` | `-0.533` | `153` | `34` |
| `5` | `8` | `1106.842` | `1063.761` | `883.633` | `-223.209` | `-43.081` | `-252.491` | `0.456` | `87` | `16` |

## Decision

- A seed-walk subcodec is promoted only if it beats raw tape and shuffled controls.
- A weak clue is retained only if the walk improves over absolute source positions and beats controls.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
