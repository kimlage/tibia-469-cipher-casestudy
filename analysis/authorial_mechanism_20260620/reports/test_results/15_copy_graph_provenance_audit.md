# Copy Graph Provenance Audit

Verdict: `copy_graph_literal_seed_atlas_compiled_no_formula_promotion`. Translation delta: `NONE`.

This audit materializes the DP LZ formula as copy edges and literal seed
runs. It is diagnostic: it explains where the current generator copies
from, which literal runs become later source material, and which books are
source hubs. It does not introduce a new lower-cost formula.

## Summary

| Metric | Value |
|---|---:|
| Copy items | `281` |
| Copied digits | `10468` |
| Same-book copy items | `5` |
| Immediate-previous-book copy items | `25` |
| Source books used | `32` |
| Literal runs | `84` |
| Literal digits | `795` |
| Literal runs reused later | `52` |
| Literal digits reused later | `640` |
| Row0 alignment failures | `0` |

## Top Source Books By Copied Digits

| Book | Copied-out digits |
|---:|---:|
| `10` | `1066` |
| `2` | `1052` |
| `5` | `979` |
| `3` | `942` |
| `0` | `679` |
| `8` | `503` |
| `1` | `487` |
| `9` | `466` |
| `17` | `460` |
| `12` | `404` |

## Outputs

- [Copy graph CSV](../../tables/dp_lz_copy_graph_edges.csv)
- [Literal seed atlas CSV](../../tables/dp_lz_literal_seed_atlas.csv)
- [Literal seed atlas Markdown](../../tables/dp_lz_literal_seed_atlas.md)

## Boundary

The atlas uses row0 symbols as mechanical overlap labels only. It does
not promote plaintext, authorial intent, or a row0 pair-table origin.
