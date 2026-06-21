# Cutoff 60 Source-State Reparse Prototype Gate

Classification: `cutoff60_source_state_reprice_roundtrip_positive_unpromoted`
Translation delta: `NONE`

## Purpose

Gate 36 showed that `previous_copy_end` makes the source-state frontier
small enough for book-local prototyping by proxy. This gate executes
the first cheaper operational step at cutoff `60`: deterministic reparse
recipes are roundtrip-checked and then repriced with the active
`previous_copy_end` default/exception source ledger. It does not
reoptimize segmentation under source-state cost.

## Summary

- Roundtrip books: `10/10`.
- Books beating raw digit uniform: `10/10`.
- Books beating old uniform-address reparse: `4/10`.
- Source-state prototype bits: `368.180`.
- Uniform-address reparse bits on same cutoff: `378.420`.
- Source-state minus uniform-address bits: `-10.241`.
- Gain versus raw digit uniform: `4478.514` bits.
- Source defaults/exceptions: `1` / `17`.

## Book Rows

| Book | Bits | Uniform-address reparse | Delta | Raw gain | Copy items | Defaults | Exceptions |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `60` | `104.448` | `105.128` | `-0.679` | `397.163` | `5` | `0` | `5` |
| `61` | `36.612` | `38.070` | `-1.458` | `445.068` | `2` | `0` | `2` |
| `62` | `20.313` | `20.250` | `+0.063` | `398.250` | `1` | `0` | `1` |
| `63` | `39.570` | `40.444` | `-0.874` | `378.993` | `2` | `0` | `2` |
| `64` | `34.568` | `42.228` | `-7.660` | `467.043` | `2` | `1` | `1` |
| `65` | `46.399` | `46.276` | `+0.124` | `515.006` | `2` | `0` | `2` |
| `66` | `21.968` | `21.907` | `+0.062` | `675.637` | `1` | `0` | `1` |
| `67` | `21.120` | `21.059` | `+0.061` | `304.429` | `1` | `0` | `1` |
| `68` | `21.605` | `21.545` | `+0.061` | `453.430` | `1` | `0` | `1` |
| `69` | `21.575` | `21.515` | `+0.060` | `443.495` | `1` | `0` | `1` |

## Interpretation

The compressed source-state ledger is now executable for the cutoff-60
suffix on deterministic reparse recipes: all ten held-out books
roundtrip and keep positive gain against raw digit coding. This is a
real implementation advance over a pure state proxy.

It is not a promoted generation method. On this cutoff, charging the
active source default/exception model inside the deterministic reparse
is cheaper in aggregate than the older uniform-address comparator,
but only `4/10` books improve individually and this gate does not
reoptimize the recipes under source-state cost.

## Boundary

- No compression-bound change is introduced.
- No complete active parser or global recipe-discovery promotion is introduced.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
