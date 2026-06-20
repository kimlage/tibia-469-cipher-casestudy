# Post-Itemctx Param Address/Payload Context-Alpha Pair Search

Verdict: `post_itemctx_param_address_payload_context_alpha_pair_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit combines the post-itemctx_param address-model frontier with
the literal-payload context/shared-alpha frontier. A pair can promote
only if the address side is decodable; no-mode literal-seed address
rows remain optimistic lower bounds.

## Coverage

- Address candidates: `10`
- Literal-payload context/alpha candidates: `4928`
- Pair candidates proven by component minima: `49280`

## Top Pairs

| Rank | Address model | Payload family | Payload split | Payload alpha | Decodable | Total bits | Delta |
|---:|---|---|---:|---:|---:|---:|---:|
| `1` | `literal_seed_address_optimistic_no_mode` | `active_global` | `` | `1` | `False` | `8492.396` | `-69.396` |
| `2` | `literal_seed_address_optimistic_no_mode` | `fixed_book_midpoint` | `` | `1` | `False` | `8494.145` | `-67.647` |
| `3` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `39` | `1` | `False` | `8504.009` | `-57.783` |
| `4` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `40` | `1` | `False` | `8504.388` | `-57.404` |
| `5` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `35` | `1` | `False` | `8505.145` | `-56.647` |
| `6` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `36` | `1` | `False` | `8505.145` | `-56.647` |
| `7` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `37` | `1` | `False` | `8505.145` | `-56.647` |
| `8` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `38` | `1` | `False` | `8505.145` | `-56.647` |
| `9` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `26` | `1` | `False` | `8505.414` | `-56.377` |
| `10` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `27` | `1` | `False` | `8505.414` | `-56.377` |
| `11` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `28` | `1` | `False` | `8505.414` | `-56.377` |
| `12` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `29` | `1` | `False` | `8505.414` | `-56.377` |
| `13` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `30` | `1` | `False` | `8505.414` | `-56.377` |
| `14` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `41` | `1` | `False` | `8505.676` | `-56.116` |
| `15` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `42` | `1` | `False` | `8505.676` | `-56.116` |
| `16` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `33` | `1` | `False` | `8506.578` | `-55.214` |
| `17` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `34` | `1` | `False` | `8506.578` | `-55.214` |
| `18` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `31` | `1` | `False` | `8507.414` | `-54.377` |
| `19` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `32` | `1` | `False` | `8507.414` | `-54.377` |
| `20` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `43` | `1` | `False` | `8507.572` | `-54.220` |

## Best Decodable Pair

- Delta vs current: `-0.000` bits
- Address: `absolute_digit_source_pos_min_len_bounded`
- Payload: `active_global`, alpha `1`

## Best Changed Decodable Pair

- Delta vs current: `1.749` bits
- Address: `absolute_digit_source_pos_min_len_bounded`
- Payload: `fixed_book_midpoint`, alpha `1`

## Best Decodable Pair With Both Components Changed

- Delta vs current: `10.809` bits
- Address: `literal_seed_sparse_run_list_seed_required`
- Payload: `fixed_book_midpoint`, alpha `1`

## Interpretation

The best overall pair is an optimistic lower bound because it uses the
literal-seed no-mode address row. The best decodable pair is the
active ledger, and every changed decodable pair is worse after
address-mode and payload declaration costs.

## Boundary

This is a mechanical cost-ledger audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
