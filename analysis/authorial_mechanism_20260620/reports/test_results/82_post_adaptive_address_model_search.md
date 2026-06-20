# Post-Adaptive Address Model Search

Verdict: `post_adaptive_address_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit retests copy-source address ledgers after adaptive bounded
copy-length coding became active. The recipe, copy lengths, book lengths,
literal payload model, item-type model, forced rules, and adaptive
copy-length model are fixed; only the copy source-address ledger changes.

## Address Models

| Model | Copy bits | Total bits | Delta vs current | Decodable | Seed copies |
|---|---:|---:|---:|---:|---:|
| `literal_seed_address_optimistic_no_mode` | `4854.6` | `8506.6` | `-69.4` | `False` | `27` |
| `absolute_digit_source_pos_min_len_bounded` | `4924.0` | `8576.0` | `-0.0` | `True` | `0` |
| `literal_seed_sparse_run_list_seed_required` | `4933.1` | `8585.0` | `9.1` | `True` | `1` |
| `literal_seed_address_conservative_mode_per_copy` | `5137.6` | `8789.6` | `213.6` | `True` | `27` |
| `book_delta_digit_offset_delta_gamma` | `6649.2` | `10301.2` | `1725.2` | `True` | `0` |
| `book_delta_digit_offset_gamma` | `6797.2` | `10449.2` | `1873.2` | `True` | `0` |
| `digit_back_distance_delta_gamma` | `6817.2` | `10469.2` | `1893.2` | `True` | `0` |
| `source_digit_pos_delta_gamma` | `6908.2` | `10560.2` | `1984.2` | `True` | `0` |
| `mixed_same_book_digit_distance_else_book_offset` | `7065.2` | `10717.2` | `2141.2` | `True` | `0` |
| `digit_back_distance_gamma` | `7706.2` | `11358.2` | `2782.2` | `True` | `0` |

## Seed Address Shape

| Metric | Value |
|---|---:|
| Copy items | `283` |
| Same-book copy items | `7` |
| Copy items with any prior literal-seed address | `68` |
| Copy items with positive optimistic seed saving | `27` |
| Optimistic seed address savings | `69.4` bits |
| Best sparse seed extra cost | `9.1` bits |

## Interpretation

The active min_len-bounded absolute digit source position ledger remains
promoted unless another decodable row beats it under full rescoring.
Literal-seed addressing is still recorded as an optimistic lower bound
when source-mode bits are not declared.

## Boundary

This is a mechanical address-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
