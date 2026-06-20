# Contextual Address Model Search

Verdict: `contextual_address_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit retests copy-source address ledgers on the active contextual
copy/reference formula. The recipe, copy lengths, book lengths, literal
payload model, item-type model, and forced rules are fixed; only the copy
source-address ledger changes.

## Address Models

| Model | Copy bits | Total bits | Delta vs current | Decodable | Seed copies |
|---|---:|---:|---:|---:|---:|
| `literal_seed_address_optimistic_no_mode` | `5061.0` | `8739.3` | `-63.8` | `False` | `26` |
| `absolute_digit_source_pos` | `5124.8` | `8803.1` | `0.0` | `True` | `0` |
| `literal_seed_sparse_run_list_seed_required` | `5135.5` | `8813.8` | `10.7` | `True` | `1` |
| `literal_seed_address_conservative_mode_per_copy` | `5342.0` | `9020.3` | `217.2` | `True` | `26` |
| `book_delta_digit_offset_delta_gamma` | `6833.0` | `10511.3` | `1708.2` | `True` | `0` |
| `book_delta_digit_offset_gamma` | `6980.0` | `10658.3` | `1855.2` | `True` | `0` |
| `digit_back_distance_delta_gamma` | `6988.0` | `10666.3` | `1863.2` | `True` | `0` |
| `source_digit_pos_delta_gamma` | `7081.0` | `10759.3` | `1956.2` | `True` | `0` |
| `mixed_same_book_digit_distance_else_book_offset` | `7246.0` | `10924.3` | `2121.2` | `True` | `0` |
| `digit_back_distance_gamma` | `7887.0` | `11565.3` | `2762.2` | `True` | `0` |

## Seed Address Shape

| Metric | Value |
|---|---:|
| Copy items | `281` |
| Same-book copy items | `7` |
| Copy items with any prior literal-seed address | `69` |
| Copy items with positive optimistic seed saving | `26` |
| Optimistic seed address savings | `63.8` bits |
| Best sparse seed extra cost | `10.7` bits |

## Interpretation

Absolute digit-only `source_digit_pos` remains the active decodable
address ledger unless another decodable row beats it. Literal-seed
addressing remains an optimistic lower bound when source-mode bits are
not declared.

## Boundary

This is a mechanical address-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
