# Copy Hub Macro Model Search

Verdict: `copy_hub_macro_model_not_promoted`. Translation delta: `NONE`.

This audit tests whether the DP LZ copy ledger can be improved by
declaring source-book hubs or default source books, then addressing
copies as `hub + source_offset` rather than absolute `source_pos`.
The parse, book order, emitted digits, and copy lengths are fixed.

## Address Models

| Model | Table bits | Copy bits | Total bits | Delta vs current | Decodable |
|---|---:|---:|---:|---:|---:|
| `absolute_flat_source_pos` | `0.0` | `5591.4` | `9823.3` | `-0.0` | `True` |
| `target_default_source_optimistic_no_mode` | `580.0` | `5515.0` | `10326.9` | `503.6` | `False` |
| `target_default_source_mode_per_copy` | `580.0` | `5618.2` | `10430.2` | `606.9` | `True` |
| `target_default_source_sparse_exception_list` | `1069.0` | `5515.0` | `10815.9` | `992.6` | `True` |
| `global_source_book_hub_offset_gamma` | `275.0` | `6696.0` | `11202.9` | `1379.6` | `True` |
| `target_source_book_hub_offset_log2` | `1786.0` | `5721.8` | `11739.7` | `1916.4` | `True` |
| `target_source_book_hub_offset_ceil` | `1786.0` | `5793.0` | `11810.9` | `1987.6` | `True` |

## Hub Shape

| Metric | Value |
|---|---:|
| Copy items | `281` |
| Target books with copies | `70` |
| Global source books | `32` |
| Target-source hubs total | `188` |
| Single-source target books | `13` |
| Max source hubs in one target | `7` |
| Max copy items in one target | `11` |

## Interpretation

The source-hub idea does not reduce the current DP LZ formula. The
target-local hub table is too expensive, and even the optimistic
default-source lower bound stays above the current absolute
`source_pos` ledger. This closes the immediate copy-hub macro variant
without changing the accepted mechanical baseline.

## Boundary

This is a mechanical address-cost audit only. It does not alter the book
strings, explain row0, or introduce plaintext.
