# Post-Itemctx Param Address/Item-Type Pair Search

Verdict: `post_itemctx_param_address_item_type_pair_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit combines the post-itemctx_param address-model frontier with
the item-type context/order/alpha frontier. A pair can promote only if
the address side is decodable; no-mode literal-seed address rows remain
optimistic lower bounds.

## Coverage

- Address candidates: `10`
- Item-type candidates: `17024`
- Pair candidates proven by component minima: `170240`

## Top Pairs

| Rank | Address model | Item family | Item split | Order | Alpha | Decodable | Total bits | Delta |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| `1` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `6` | `1` | `2` | `False` | `8492.396` | `-69.396` |
| `2` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `6` | `1` | `1` | `False` | `8492.811` | `-68.981` |
| `3` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `9` | `1` | `2` | `False` | `8493.731` | `-68.061` |
| `4` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `4` | `1` | `2` | `False` | `8494.130` | `-67.662` |
| `5` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `4` | `1` | `1` | `False` | `8494.278` | `-67.514` |
| `6` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `9` | `1` | `1` | `False` | `8494.302` | `-67.490` |
| `7` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `6` | `1` | `3` | `False` | `8494.863` | `-66.929` |
| `8` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `18` | `1` | `1` | `False` | `8495.339` | `-66.453` |
| `9` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `18` | `1` | `2` | `False` | `8495.371` | `-66.420` |
| `10` | `literal_seed_address_optimistic_no_mode` | `fixed_book_quartile` | `` | `1` | `1` | `False` | `8495.563` | `-66.229` |
| `11` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `6` | `1` | `4` | `False` | `8495.598` | `-66.194` |
| `12` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `14` | `1` | `2` | `False` | `8495.908` | `-65.884` |
| `13` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `9` | `1` | `3` | `False` | `8496.100` | `-65.692` |
| `14` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `5` | `1` | `2` | `False` | `8496.230` | `-65.562` |
| `15` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `14` | `1` | `1` | `False` | `8496.319` | `-65.473` |
| `16` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `10` | `1` | `2` | `False` | `8496.337` | `-65.455` |
| `17` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `6` | `1` | `5` | `False` | `8496.435` | `-65.357` |
| `18` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `19` | `1` | `1` | `False` | `8496.702` | `-65.090` |
| `19` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `19` | `1` | `2` | `False` | `8496.715` | `-65.077` |
| `20` | `literal_seed_address_optimistic_no_mode` | `searched_single_book_split` | `4` | `1` | `3` | `False` | `8496.757` | `-65.035` |

## Best Decodable Pair

- Delta vs current: `-0.000` bits
- Address: `absolute_digit_source_pos_min_len_bounded`
- Item-type: `searched_single_book_split`, order `1`, alpha `2`

## Best Changed Decodable Pair

- Delta vs current: `0.415` bits
- Address: `absolute_digit_source_pos_min_len_bounded`
- Item-type: `searched_single_book_split`, order `1`, alpha `1`

## Best Decodable Pair With Both Components Changed

- Delta vs current: `9.476` bits
- Address: `literal_seed_sparse_run_list_seed_required`
- Item-type: `searched_single_book_split`, order `1`, alpha `1`

## Interpretation

The best overall pairs are optimistic lower bounds because they use the
literal-seed no-mode address row. The best decodable pair is the active
ledger, and every changed decodable pair is worse after declaration and
mode costs.

## Boundary

This is a mechanical cost-ledger audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
