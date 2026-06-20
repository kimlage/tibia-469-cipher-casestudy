# Post-Repair Address Model Search

Verdict: `post_repair_address_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit retests copy-source address ledgers after the local
literal-to-copy repair. The repaired recipe is fixed; only the copy
source-address ledger changes.

## Address Models

| Model | Copy bits | Total bits | Delta vs current | Decodable | Seed copies |
|---|---:|---:|---:|---:|---:|
| `literal_seed_address_optimistic_no_mode` | `5327.5` | `9472.4` | `-64.8` | `False` | `26` |
| `absolute_flat_source_pos` | `5392.3` | `9537.3` | `0.0` | `True` | `0` |
| `literal_seed_sparse_run_list_seed_required` | `5403.1` | `9548.0` | `10.7` | `True` | `1` |
| `literal_seed_address_conservative_mode_per_copy` | `5607.5` | `9752.4` | `215.2` | `True` | `26` |
| `book_delta_offset_delta_gamma` | `7085.0` | `11229.9` | `1692.7` | `True` | `0` |
| `book_delta_offset_gamma` | `7237.0` | `11381.9` | `1844.7` | `True` | `0` |
| `back_distance_delta_gamma` | `7284.0` | `11428.9` | `1891.7` | `True` | `0` |
| `source_pos_delta_gamma` | `7340.0` | `11484.9` | `1947.7` | `True` | `0` |
| `mixed_same_book_distance_else_book_offset` | `7502.0` | `11646.9` | `2109.7` | `True` | `0` |
| `back_distance_gamma` | `8147.0` | `12291.9` | `2754.7` | `True` | `0` |

## Seed Address Shape

| Metric | Value |
|---|---:|
| Copy items | `280` |
| Same-book copy items | `7` |
| Copy items with any prior literal-seed address | `69` |
| Copy items with positive optimistic seed saving | `26` |
| Optimistic seed address savings | `64.8` bits |
| Best sparse seed extra cost | `10.7` bits |

## Interpretation

Absolute `source_pos` remains the best decodable address ledger for the
post-repair formula if no decodable row beats it. Any non-decodable
literal-seed lower bound is recorded as an optimistic clue only.

## Boundary

This is a mechanical address-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
