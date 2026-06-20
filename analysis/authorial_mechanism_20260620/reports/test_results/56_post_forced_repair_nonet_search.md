# Post-Forced-Repair Nonet Search

Verdict: `post_forced_repair_nonet_not_promoted`. Translation delta: `NONE`.

This audit tests whether nine compatible literal-to-copy repairs become
cheaper together after the forced-length local repair. The full active
cost model is used: adaptive literal payload, forced literal lengths,
digit-only absolute copy addresses, copy length coding, and the
book-start Markov item-type stream with deterministic type rules.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8922.8` |
| Single repair candidates | `22` |
| Compatible nonets tested | `262548` |
| Incompatible nonets skipped | `234872` |
| Best single delta | `0.7` |
| Best nonet total bits | `8935.7` |
| Best nonet delta vs current | `12.9` |

## Best Nonet

| Book | Op | Book pos | Literal offset | Chunk | Source digit pos | Length | Single delta |
|---:|---:|---:|---:|---|---:|---:|---:|
| `0` | `2` | `60` | `56` | `11800` | `57` | `5` | `1.3` |
| `1` | `4` | `34` | `6` | `57651` | `92` | `5` | `1.8` |
| `2` | `7` | `36` | `2` | `65128` | `50` | `5` | `1.6` |
| `2` | `9` | `71` | `2` | `18003` | `58` | `5` | `0.7` |
| `2` | `9` | `71` | `16` | `72611` | `68` | `5` | `2.1` |
| `2` | `11` | `137` | `30` | `11216` | `225` | `5` | `1.9` |
| `3` | `4` | `29` | `12` | `60199` | `22` | `5` | `1.1` |
| `17` | `1` | `7` | `1` | `477090` | `208` | `6` | `1.0` |
| `57` | `2` | `69` | `23` | `74519` | `3292` | `5` | `1.8` |

## Interpretation

A nonet is promoted only if exact rescoring beats the active
forced-length repaired formula. If the best nonet remains worse,
the local literal-to-copy frontier is closed under compatible repair
nonets for this cost model.

## Boundary

This is a mechanical recipe audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
