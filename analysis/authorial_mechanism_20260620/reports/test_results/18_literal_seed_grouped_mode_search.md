# Literal Seed Grouped-Mode Search

Verdict: `literal_seed_grouped_mode_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit tests the next refinement after the literal-seed address
search: maybe source-mode bits should be paid by grouped masks or sparse
seed runs, rather than once per copy operation.

## Address Models

| Model | Copy bits | Total bits | Delta vs current | Seed copies | Decodable mixed ledger |
|---|---:|---:|---:|---:|---:|
| `literal_seed_address_optimistic_no_mode` | `5520.9` | `9752.8` | `-70.5` | `28` | `False` |
| `absolute_flat_source_pos` | `5591.4` | `9823.3` | `-0.0` | `0` | `True` |
| `literal_seed_sparse_run_list_seed_required` | `5598.0` | `9830.0` | `6.7` | `2` | `True` |
| `literal_seed_grouped_rle_mode_optional_seed` | `5609.4` | `9841.3` | `18.0` | `0` | `True` |
| `literal_seed_grouped_rle_mode_seed_required` | `5611.0` | `9843.0` | `19.7` | `2` | `True` |
| `literal_seed_address_conservative_mode_per_copy` | `5801.9` | `10033.8` | `210.5` | `28` | `True` |

## Best Grouped Ledgers

| Ledger | Net extra vs absolute | Gross mode bits | Seed savings used | Seed copies | Seed runs |
|---|---:|---:|---:|---:|---:|
| RLE mode mask, seed required | `19.7` | `28.0` | `8.3` | `2` | `1` |
| Sparse seed-run list, seed required | `6.7` | `15.0` | `8.3` | `2` | `1` |

## Interpretation

Grouped source-mode ledgers reduce the cost of the earlier per-copy
mode model, but they still do not beat the current absolute
`source_pos` formula. The best seed-using decodable ledger is the
sparse seed-run list, which remains above the baseline. If seed use is
optional, the RLE ledger simply chooses zero seed copies and pays only
mask overhead, which is not a promoted seed-address formula.

## Boundary

This is a mechanical address-cost audit only. It does not alter the book
strings, explain row0, or introduce plaintext.
