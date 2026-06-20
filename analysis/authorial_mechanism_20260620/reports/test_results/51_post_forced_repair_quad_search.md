# Post-Forced-Repair Quad Search

Verdict: `post_forced_repair_quad_not_promoted`. Translation delta: `NONE`.

This audit tests whether four compatible literal-to-copy repairs become
cheaper together after the forced-length local repair. The full active
cost model is used: adaptive literal payload, forced literal lengths,
digit-only absolute copy addresses, copy length coding, and the
book-start Markov item-type stream with deterministic type rules.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8922.8` |
| Single repair candidates | `22` |
| Compatible quads tested | `6596` |
| Incompatible quads skipped | `719` |
| Best single delta | `0.7` |
| Best quad total bits | `8926.7` |
| Best quad delta vs current | `3.9` |

## Best Quad

| Book | Literal offset | Chunk | Source digit pos | Length | Single delta |
|---:|---:|---|---:|---:|---:|
| `0` | `56` | `11800` | `57` | `5` | `1.3` |
| `2` | `2` | `18003` | `58` | `5` | `0.7` |
| `3` | `12` | `60199` | `22` | `5` | `1.1` |
| `17` | `1` | `477090` | `208` | `6` | `1.0` |

## Interpretation

A quad is promoted only if exact rescoring beats the active
forced-length repaired formula. If the best quad remains worse,
the local literal-to-copy frontier is closed under compatible repair
quartets for this cost model.

## Boundary

This is a mechanical recipe audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
