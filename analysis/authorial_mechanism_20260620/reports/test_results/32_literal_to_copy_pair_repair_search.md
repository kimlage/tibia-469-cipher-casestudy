# Literal-to-Copy Pair Repair Search

Verdict: `literal_to_copy_pair_repair_not_promoted`. Translation delta: `NONE`.

This audit tests whether two literal-to-copy repairs become cheaper
together under the adaptive literal-payload model, even when the second
repair is not individually profitable after the known local repair.

## Search Summary

| Metric | Value |
|---|---:|
| Source formula bits | `9538.0` |
| Current repaired formula bits | `9537.3` |
| Single repair candidates | `25` |
| Compatible pairs tested | `293` |
| Overlapping pairs skipped | `7` |
| Best pair total bits | `9538.2` |
| Best pair delta vs source | `0.2` |
| Best pair delta vs repaired | `0.9` |

## Best Pair

| Book | Literal offset | Chunk | Source pos | Length | Single delta vs source |
|---:|---:|---|---:|---:|---:|
| `2` | `2` | `18003` | `58` | `5` | `0.9` |
| `8` | `2` | `972783` | `370` | `6` | `-0.7` |

## Interpretation

The best compatible two-repair recipe is still worse than the current
one-step repaired formula. The local literal-to-copy frontier remains
closed under single repairs and compatible repair pairs.

## Boundary

This is a mechanical recipe audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
