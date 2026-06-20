# Post-Forced-Repair Pair Search

Verdict: `post_forced_repair_pair_not_promoted`. Translation delta: `NONE`.

This audit tests whether two compatible literal-to-copy repairs become
cheaper together after the forced-length local repair. The full active
cost model is used: adaptive literal payload, forced literal lengths,
digit-only absolute copy addresses, copy length coding, and the
book-start Markov item-type stream with deterministic type rules.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8922.8` |
| Single repair candidates | `22` |
| Compatible pairs tested | `227` |
| Overlapping pairs skipped | `4` |
| Best single delta | `0.7` |
| Best pair total bits | `8924.4` |
| Best pair delta vs current | `1.6` |

## Best Pair

| Book | Literal offset | Chunk | Source digit pos | Length | Single delta |
|---:|---:|---|---:|---:|---:|
| `2` | `2` | `18003` | `58` | `5` | `0.7` |
| `17` | `1` | `477090` | `208` | `6` | `1.0` |

## Interpretation

A pair is promoted only if exact rescoring beats the active
forced-length repaired formula. If the best pair remains worse, the
local literal-to-copy frontier is closed under compatible repair
pairs for this cost model.

## Boundary

This is a mechanical recipe audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
