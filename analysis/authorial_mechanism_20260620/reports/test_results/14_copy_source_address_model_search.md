# Copy Source Address Model Search

Verdict: `copy_source_address_absolute_retained`. Translation delta: `NONE`.

This audit tests whether the DP sequential LZ formula can be improved by
charging copy source addresses differently. The parse and emitted books
are held fixed; only the address ledger changes.

## Address Models

| Model | Copy bits | Total bits | Delta vs current |
|---|---:|---:|---:|
| `absolute_flat_source_pos` | `5591.4` | `9823.3` | `-0.0` |
| `book_delta_offset_delta_gamma` | `7276.0` | `11507.9` | `1684.6` |
| `back_distance_delta_gamma` | `7437.0` | `11668.9` | `1845.6` |
| `book_delta_offset_gamma` | `7454.0` | `11685.9` | `1862.6` |
| `source_pos_delta_gamma` | `7479.0` | `11710.9` | `1887.6` |
| `mixed_same_book_distance_else_book_offset` | `7728.0` | `11959.9` | `2136.6` |
| `back_distance_gamma` | `8389.0` | `12620.9` | `2797.6` |

## Interpretation

The current absolute `source_pos` ledger remains cheapest. Back-distance,
source-delta, and book-relative source models all add cost under this
fixed parse. Therefore no new address model is promoted in this cycle.

## Boundary

This is a mechanical cost audit only. It does not alter the book text,
explain row0, or introduce plaintext.
