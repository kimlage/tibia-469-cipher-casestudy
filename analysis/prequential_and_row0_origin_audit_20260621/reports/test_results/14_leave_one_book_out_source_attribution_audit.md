# Leave-One-Book-Out Source Attribution Audit

Classification: `loo_source_attribution_mapped_with_boundary_crossings`
Translation delta: `NONE`

## Purpose

Audit 13 showed every individual book can be reparsed without preloading
that book into the inventory. This audit maps where copied digits come
from: concrete source books or the already-emitted current-book prefix.
It also counts copies that cross artificial source-book boundaries in the
concatenated complement inventory.

## Summary

- Books checked: `70`.
- Roundtrip books: `70/70`.
- Copy items: `189`.
- Copied digits: `11062`.
- Cross-boundary copy items: `23`.
- Cross-boundary copied digits: `3001`.
- Cross-boundary copied digit share: `0.271289`.
- Current-prefix copied digits: `8`.
- Current-prefix copied digit share: `0.000723`.
- Current-prefix target books: `[49]`.
- Mean distinct source books per target: `2.171`.
- Mean top-source share: `0.772`.

## Highest Top-Source Shares

| Target | Top source | Top share | Copied digits |
|---:|---:|---:|---:|
| `0` | `book:10` | `1.000` | `144` |
| `1` | `book:10` | `1.000` | `92` |
| `4` | `book:3` | `1.000` | `132` |
| `12` | `book:21` | `1.000` | `137` |
| `22` | `book:2` | `1.000` | `137` |
| `23` | `book:2` | `1.000` | `150` |
| `25` | `book:39` | `1.000` | `35` |
| `28` | `book:48` | `1.000` | `146` |
| `32` | `book:58` | `1.000` | `137` |
| `39` | `book:15` | `1.000` | `52` |

## Widest Source Rows

| Target | Distinct source books | Copied digits |
|---:|---:|---:|
| `14` | `5` | `116` |
| `56` | `5` | `263` |
| `6` | `4` | `169` |
| `16` | `4` | `174` |
| `17` | `4` | `274` |
| `26` | `4` | `170` |
| `34` | `4` | `110` |
| `40` | `4` | `165` |
| `59` | `4` | `272` |
| `18` | `3` | `93` |

## Top Edges

| Target | Source | Copied digits |
|---:|---:|---:|
| `35` | `book:10` | `277` |
| `5` | `book:9` | `271` |
| `9` | `book:5` | `269` |
| `46` | `book:51` | `253` |
| `53` | `book:46` | `234` |
| `51` | `book:46` | `211` |
| `10` | `book:66` | `210` |
| `66` | `book:10` | `210` |
| `57` | `book:31` | `188` |
| `23` | `book:2` | `150` |
| `28` | `book:48` | `146` |
| `31` | `book:1` | `146` |
| `61` | `book:65` | `145` |
| `0` | `book:10` | `144` |
| `21` | `book:26` | `144` |
| `26` | `book:21` | `143` |
| `68` | `book:17` | `143` |
| `50` | `book:9` | `141` |
| `69` | `book:9` | `140` |
| `12` | `book:21` | `137` |

## Decision

- Singleton holdout source attribution is now explicit as target-book to source-book/current-prefix copied-digit edges.
- Cross-boundary copies are measured rather than hidden; they are a boundary condition of the concatenated complement inventory.
- This improves the mechanical dependency map but does not derive row0, plaintext, or authorial order.
