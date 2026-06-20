# Rice Copy Address Model Search

Verdict: `rice_copy_address_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit retests copy-source address ledgers on the promoted
Rice-length parse. The book order, parse, copy lengths, and Rice length
code are fixed; only the source-address ledger changes.

## Address Models

| Model | Copy bits | Total bits | Delta vs current | Decodable | Seed copies |
|---|---:|---:|---:|---:|---:|
| `literal_seed_address_optimistic_no_mode` | `5323.4` | `9549.5` | `-47.0` | `False` | `18` |
| `absolute_flat_source_pos` | `5370.4` | `9596.5` | `0.0` | `True` | `0` |
| `literal_seed_sparse_run_list_seed_required` | `5381.0` | `9607.1` | `10.6` | `True` | `1` |
| `literal_seed_address_conservative_mode_per_copy` | `5601.4` | `9827.5` | `231.0` | `True` | `18` |
| `book_delta_offset_delta_gamma` | `7063.0` | `11289.1` | `1692.6` | `True` | `0` |
| `book_delta_offset_gamma` | `7199.0` | `11425.1` | `1828.6` | `True` | `0` |
| `back_distance_delta_gamma` | `7272.0` | `11498.1` | `1901.6` | `True` | `0` |
| `source_pos_delta_gamma` | `7334.0` | `11560.1` | `1963.6` | `True` | `0` |
| `mixed_same_book_distance_else_book_offset` | `7470.0` | `11696.1` | `2099.6` | `True` | `0` |
| `back_distance_gamma` | `8133.0` | `12359.1` | `2762.6` | `True` | `0` |

## Seed Address Shape

| Metric | Value |
|---|---:|
| Copy items | `278` |
| Copy items with any prior literal-seed address | `84` |
| Copy items with positive optimistic seed saving | `18` |
| Optimistic seed address savings | `47.0` bits |
| Best sparse seed extra cost | `10.6` bits |

## Interpretation

Absolute `source_pos` remains the best decodable address ledger for the
Rice-length parse. Literal-seed addressing is again only an optimistic
lower bound: without source-mode bits it is cheaper, but the best
decodable sparse seed-run ledger is still worse than the promoted
formula. No new address model is promoted.

## Boundary

This is a mechanical address-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
