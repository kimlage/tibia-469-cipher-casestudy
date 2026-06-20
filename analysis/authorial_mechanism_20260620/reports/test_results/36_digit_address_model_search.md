# Digit Address Model Search

Verdict: `digit_address_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit retests copy-source address ledgers after the promoted
digit-only absolute address compile. The recipe is fixed; only the
copy source-address ledger changes.

## Address Models

| Model | Copy bits | Total bits | Delta vs current | Decodable | Seed copies |
|---|---:|---:|---:|---:|---:|
| `literal_seed_address_optimistic_no_mode` | `5325.3` | `9006.2` | `-64.6` | `False` | `26` |
| `absolute_digit_source_pos` | `5389.9` | `9070.8` | `-0.0` | `True` | `0` |
| `literal_seed_sparse_run_list_seed_required` | `5400.6` | `9081.5` | `10.7` | `True` | `1` |
| `literal_seed_address_conservative_mode_per_copy` | `5605.3` | `9286.2` | `215.4` | `True` | `26` |
| `book_delta_digit_offset_delta_gamma` | `7085.0` | `10765.9` | `1695.1` | `True` | `0` |
| `book_delta_digit_offset_gamma` | `7237.0` | `10917.9` | `1847.1` | `True` | `0` |
| `digit_back_distance_delta_gamma` | `7247.0` | `10927.9` | `1857.1` | `True` | `0` |
| `source_digit_pos_delta_gamma` | `7334.0` | `11014.9` | `1944.1` | `True` | `0` |
| `mixed_same_book_digit_distance_else_book_offset` | `7502.0` | `11182.9` | `2112.1` | `True` | `0` |
| `digit_back_distance_gamma` | `8147.0` | `11827.9` | `2757.1` | `True` | `0` |

## Seed Address Shape

| Metric | Value |
|---|---:|
| Copy items | `280` |
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
