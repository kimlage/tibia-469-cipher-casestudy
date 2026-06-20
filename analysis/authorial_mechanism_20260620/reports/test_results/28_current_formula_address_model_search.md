# Current Formula Address Model Search

Verdict: `current_formula_address_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit retests copy-source address ledgers on the current best
sequential LZ formula, including Rice copy lengths, Rice literal-run
lengths, and adaptive literal payload coding. The recipe is fixed; only
the copy source-address ledger changes.

## Address Models

| Model | Copy bits | Total bits | Delta vs current | Decodable | Seed copies |
|---|---:|---:|---:|---:|---:|
| `literal_seed_address_optimistic_no_mode` | `5316.5` | `9478.6` | `-59.4` | `False` | `23` |
| `absolute_flat_source_pos` | `5375.9` | `9538.0` | `0.0` | `True` | `0` |
| `literal_seed_sparse_run_list_seed_required` | `5386.6` | `9548.7` | `10.7` | `True` | `1` |
| `literal_seed_address_conservative_mode_per_copy` | `5595.5` | `9757.6` | `219.6` | `True` | `23` |
| `book_delta_offset_delta_gamma` | `7072.0` | `11234.1` | `1696.1` | `True` | `0` |
| `book_delta_offset_gamma` | `7211.0` | `11373.1` | `1835.1` | `True` | `0` |
| `back_distance_delta_gamma` | `7270.0` | `11432.1` | `1894.1` | `True` | `0` |
| `source_pos_delta_gamma` | `7328.0` | `11490.1` | `1952.1` | `True` | `0` |
| `mixed_same_book_distance_else_book_offset` | `7475.0` | `11637.1` | `2099.1` | `True` | `0` |
| `back_distance_gamma` | `8122.0` | `12284.1` | `2746.1` | `True` | `0` |

## Seed Address Shape

| Metric | Value |
|---|---:|
| Copy items | `279` |
| Same-book copy items | `7` |
| Copy items with any prior literal-seed address | `69` |
| Copy items with positive optimistic seed saving | `23` |
| Optimistic seed address savings | `59.4` bits |
| Best sparse seed extra cost | `10.7` bits |

## Interpretation

Absolute `source_pos` remains the best decodable address ledger for the
current formula if no decodable row beats it. Any non-decodable
literal-seed lower bound is recorded as an optimistic clue only.

## Boundary

This is a mechanical address-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
