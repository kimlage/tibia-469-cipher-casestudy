# Post-Adaptive Pair Frontier

Verdict: `post_adaptive_pair_frontier_closed`. Translation delta: `NONE`.

This audit retests compatible pairs of local recipe edits after adaptive
bounded copy-length coding became the active formula. It scores pairs of
single literal-to-copy and copy-to-literal edits under full adaptive
rescoring.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8575.986` |
| Literal-to-copy candidates tested | `21` |
| Copy-to-literal candidates tested | `283` |
| Invalid single candidates | `115` |
| Valid single candidates | `189` |
| Total pairs considered | `17766` |
| Compatible pairs | `17762` |
| Invalid compatible pairs | `99` |
| Valid pairs scored | `17663` |
| Best single delta | `1.084` |
| Best pair total bits | `8578.501` |
| Best pair delta | `2.516` |

## Best Pair

| Type | Book | Op | Text | Length | Single delta |
|---|---:|---:|---|---:|---:|
| `copy_to_literal` | `14` | `2` | `71288` | `5` | `1.600` |
| `copy_to_literal` | `34` | `7` | `45765` | `5` | `1.084` |

## Interpretation

The pair frontier is closed if the best fully rescored compatible pair
remains at or above zero delta. This is a mechanical recipe audit only;
it does not introduce plaintext, row0 meaning, or authorial intent.
