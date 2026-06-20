# Post-Forced-Repair Address Model Search

Verdict: `post_forced_repair_address_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit retests copy-source address ledgers after the forced-length
literal-to-copy repair. The recipe, copy lengths, item-type ledger,
literal payload model, forced literal-length rule, and book-length
ledger are fixed; only the copy source-address ledger changes.

## Address Models

| Model | Copy bits | Total bits | Delta vs current | Decodable | Seed copies |
|---|---:|---:|---:|---:|---:|
| `literal_seed_address_optimistic_no_mode` | `5074.9` | `8855.5` | `-67.3` | `False` | `27` |
| `absolute_digit_source_pos` | `5142.2` | `8922.8` | `0.0` | `True` | `0` |
| `literal_seed_sparse_run_list_seed_required` | `5152.9` | `8933.5` | `10.7` | `True` | `1` |
| `literal_seed_address_conservative_mode_per_copy` | `5356.9` | `9137.5` | `214.7` | `True` | `27` |
| `book_delta_digit_offset_delta_gamma` | `6857.0` | `10637.6` | `1714.8` | `True` | `0` |
| `book_delta_digit_offset_gamma` | `7007.0` | `10787.6` | `1864.8` | `True` | `0` |
| `digit_back_distance_delta_gamma` | `7025.0` | `10805.6` | `1882.8` | `True` | `0` |
| `source_digit_pos_delta_gamma` | `7112.0` | `10892.6` | `1969.8` | `True` | `0` |
| `mixed_same_book_digit_distance_else_book_offset` | `7274.0` | `11054.6` | `2131.8` | `True` | `0` |
| `digit_back_distance_gamma` | `7917.0` | `11697.6` | `2774.8` | `True` | `0` |

## Seed Address Shape

| Metric | Value |
|---|---:|
| Copy items | `282` |
| Same-book copy items | `7` |
| Copy items with any prior literal-seed address | `70` |
| Copy items with positive optimistic seed saving | `27` |
| Optimistic seed address savings | `67.3` bits |
| Best sparse seed extra cost | `10.7` bits |

## Interpretation

Absolute digit-only `source_digit_pos` remains the best decodable ledger
if no decodable row beats it. Any non-decodable literal-seed lower
bound is recorded as an optimistic clue only.

## Boundary

This is a mechanical address-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
