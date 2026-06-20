# Post-Repair2 Pair Frontier

Verdict: `post_repair2_pair_frontier_closed`. Translation delta: `NONE`.

This audit tests whether two compatible local edits become cheaper
together after the one-step post-repair2 frontier closed. It uses the
active full rescoring model: contextual literal payload, contextual
item types with forced rules, bounded copy lengths, and min_len-bounded
absolute source addresses.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8609.773` |
| Literal-to-copy candidates tested | `21` |
| Copy-to-literal candidates tested | `283` |
| Invalid single candidates | `115` |
| Valid single candidates | `189` |
| Total pairs considered | `17766` |
| Compatible pairs | `17762` |
| Invalid compatible pairs | `99` |
| Valid pairs scored | `17663` |
| Best single delta | `0.121` |
| Best pair total bits | `8610.465` |
| Best pair delta | `0.692` |

## Best Pair

| Type | Book | Op | Text | Length | Single delta |
|---|---:|---:|---|---:|---:|
| `copy_to_literal` | `14` | `2` | `71288` | `5` | `0.586` |
| `copy_to_literal` | `26` | `2` | `94343` | `5` | `0.121` |

## Interpretation

The compatible-pair frontier is closed if the best fully rescored pair
remains at or above zero delta. This is a mechanical recipe audit only;
it does not introduce plaintext, row0 meaning, or authorial intent.
