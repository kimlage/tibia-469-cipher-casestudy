# Post-Midpoint Alpha1 Address Model Search

Verdict: `post_midpoint_alpha1_address_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit retests copy-source address ledgers after the midpoint
copy-length context and `alpha=1` became active. The recipe, copy
lengths, book lengths, literal payload model, item-type model, forced
rules, midpoint context, and alpha=1 copy-length model are fixed; only
the copy source-address ledger changes.

## Address Models

| Model | Copy bits | Total bits | Delta vs current | Decodable | Seed copies |
|---|---:|---:|---:|---:|---:|
| `literal_seed_address_optimistic_no_mode` | `4846.9` | `8502.9` | `-69.4` | `False` | `27` |
| `absolute_digit_source_pos_min_len_bounded` | `4916.3` | `8572.3` | `-0.0` | `True` | `0` |
| `literal_seed_sparse_run_list_seed_required` | `4925.3` | `8581.3` | `9.1` | `True` | `1` |
| `literal_seed_address_conservative_mode_per_copy` | `5129.9` | `8785.9` | `213.6` | `True` | `27` |
| `book_delta_digit_offset_delta_gamma` | `6641.5` | `10297.5` | `1725.2` | `True` | `0` |
| `book_delta_digit_offset_gamma` | `6789.5` | `10445.5` | `1873.2` | `True` | `0` |
| `digit_back_distance_delta_gamma` | `6809.5` | `10465.5` | `1893.2` | `True` | `0` |
| `source_digit_pos_delta_gamma` | `6900.5` | `10556.5` | `1984.2` | `True` | `0` |
| `mixed_same_book_digit_distance_else_book_offset` | `7057.5` | `10713.5` | `2141.2` | `True` | `0` |
| `digit_back_distance_gamma` | `7698.5` | `11354.5` | `2782.2` | `True` | `0` |

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
