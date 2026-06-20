# Post-Forced-Repair Triple Search

Verdict: `post_forced_repair_triple_not_promoted`. Translation delta: `NONE`.

This audit tests whether three compatible literal-to-copy repairs become
cheaper together after the forced-length local repair. The full active
cost model is used: adaptive literal payload, forced literal lengths,
digit-only absolute copy addresses, copy length coding, and the
book-start Markov item-type stream with deterministic type rules.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8922.8` |
| Single repair candidates | `22` |
| Compatible triples tested | `1462` |
| Incompatible triples skipped | `78` |
| Best single delta | `0.7` |
| Best triple total bits | `8925.5` |
| Best triple delta vs current | `2.7` |

## Best Triple

| Book | Literal offset | Chunk | Source digit pos | Length | Single delta |
|---:|---:|---|---:|---:|---:|
| `2` | `2` | `18003` | `58` | `5` | `0.7` |
| `3` | `12` | `60199` | `22` | `5` | `1.1` |
| `17` | `1` | `477090` | `208` | `6` | `1.0` |

## Interpretation

A triple is promoted only if exact rescoring beats the active
forced-length repaired formula. If the best triple remains worse,
the local literal-to-copy frontier is closed under compatible repair
triples for this cost model.

## Boundary

This is a mechanical recipe audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
