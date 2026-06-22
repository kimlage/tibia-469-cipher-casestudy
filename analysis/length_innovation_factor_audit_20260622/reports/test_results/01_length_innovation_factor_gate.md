# Length Innovation Factor Gate

Classification: `length_innovation_factorization_clue_residual_external`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

This gate tests whether exact operation lengths are better represented as a coarse `type:length_bucket` control stream plus a within-bucket residual innovation tape. It is a representation test, not a plaintext or row0 test.

## Factorization Ledger

- Rows: `261`.
- Independent `op_type + exact_length` bits: `1855.639`.
- `type:length_bucket` stream bits: `775.003`.
- Uniform residual-within-bucket bits: `966.638`.
- Factorized total bits: `1741.641`.
- Factorized saving: `113.998` bits.

## Residual Codec Gate

| Feature | Bits | Saving | Random p95 | Top1 Hits | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| `global` | `2421.198` | `-476.124` | `-308.923` | `42/493` | `REJECTED_RESIDUAL_MODEL` |
| `length_bucket` | `2113.637` | `-168.563` | `-137.785` | `34/493` | `REJECTED_RESIDUAL_MODEL` |
| `op_type` | `2349.442` | `-404.368` | `-292.501` | `45/493` | `REJECTED_RESIDUAL_MODEL` |
| `remaining_bucket` | `2252.821` | `-307.748` | `-222.949` | `40/493` | `REJECTED_RESIDUAL_MODEL` |
| `type_bucket` | `2063.071` | `-117.997` | `-171.115` | `53/493` | `WEAK_RESIDUAL_CODEC_CLUE` |
| `type_bucket_prev_bucket` | `2121.739` | `-176.665` | `-139.125` | `51/493` | `REJECTED_RESIDUAL_MODEL` |
| `type_bucket_remaining` | `2086.178` | `-141.104` | `-123.736` | `60/493` | `REJECTED_RESIDUAL_MODEL` |

## Best Residual Feature

- Best residual feature: `type_bucket`.
- Best residual bits: `2063.071`.
- Best residual saving vs uniform residual: `-117.997`.
- Best residual shuffled p95 saving: `-171.115`.
- Promoted residual features: `[]`.

## Decision

The bucket+residual representation is promoted as a useful dependency factorization, but the exact residual tape remains external. This narrows the blocker from exact length as a whole to within-bucket length innovation.

`row0`, translation, plaintext, and the compression bound remain unchanged.

## Remaining External Fields

- `type:length_bucket` control stream
- within-bucket length residual innovation tape
- literal innovation tape payload and schedule
- copy-hint rank stream
- seed books `0..9`
- `row0`
