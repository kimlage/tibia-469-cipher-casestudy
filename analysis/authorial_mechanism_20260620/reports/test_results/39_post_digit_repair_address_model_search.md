# Post-Digit-Repair Address Model Search

Verdict: `post_digit_repair_address_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit retests copy-source address ledgers after the latest
digit-address literal-to-copy repair. The recipe is fixed; only the
copy source-address ledger changes.

## Address Models

| Model | Copy bits | Total bits | Delta vs current | Decodable | Seed copies |
|---|---:|---:|---:|---:|---:|
| `literal_seed_address_optimistic_no_mode` | `5342.5` | `9005.5` | `-64.6` | `False` | `26` |
| `absolute_digit_source_pos` | `5407.1` | `9070.1` | `0.0` | `True` | `0` |
| `literal_seed_sparse_run_list_seed_required` | `5417.8` | `9080.8` | `10.7` | `True` | `1` |
| `literal_seed_address_conservative_mode_per_copy` | `5623.5` | `9286.5` | `216.4` | `True` | `26` |
| `book_delta_digit_offset_delta_gamma` | `7115.0` | `10778.0` | `1707.9` | `True` | `0` |
| `book_delta_digit_offset_gamma` | `7265.0` | `10928.0` | `1857.9` | `True` | `0` |
| `digit_back_distance_delta_gamma` | `7275.0` | `10938.0` | `1867.9` | `True` | `0` |
| `source_digit_pos_delta_gamma` | `7362.0` | `11025.0` | `1954.9` | `True` | `0` |
| `mixed_same_book_digit_distance_else_book_offset` | `7531.0` | `11194.0` | `2123.9` | `True` | `0` |
| `digit_back_distance_gamma` | `8170.0` | `11833.0` | `2762.9` | `True` | `0` |

## Seed Address Shape

| Metric | Value |
|---|---:|
| Copy items | `281` |
| Same-book copy items | `7` |
| Copy items with any prior literal-seed address | `69` |
| Copy items with positive optimistic seed saving | `26` |
| Optimistic seed address savings | `64.6` bits |
| Best sparse seed extra cost | `10.7` bits |

## Interpretation

Absolute digit-only `source_digit_pos` remains the best decodable ledger
if no decodable row beats it. Any non-decodable literal-seed lower
bound is recorded as an optimistic clue only.

## Boundary

This is a mechanical address-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
