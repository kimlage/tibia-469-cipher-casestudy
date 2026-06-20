# Post-Itemctx Param Copy-Length/Item-Type Pair Context Search

Verdict: `post_itemctx_param_copy_length_item_type_pair_not_promoted`. Translation delta: `NONE`.

This audit combines the post-itemctx_param copy-length context frontier
with the post-itemctx_param item-type context-family frontier. Copy-length
and item-type costs are independent MDL components here, so all pairs are
enumerated by summed component deltas and the top pairs are checked by
authoritative item-type rescoring plus copy-length delta.

## Coverage

- Copy-length candidates: `79`
- Item-type candidates: `17024`
- Pair candidates: `1344896`

## Top Pairs

| Rank | Copy family | Copy split | Item family | Item split | Order | Alpha | Total bits | Delta |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| `1` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `6` | `1` | `2` | `8561.792` | `0.000` |
| `2` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `6` | `1` | `1` | `8562.207` | `0.415` |
| `3` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `9` | `1` | `2` | `8563.127` | `1.335` |
| `4` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `4` | `1` | `2` | `8563.526` | `1.734` |
| `5` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `4` | `1` | `1` | `8563.674` | `1.882` |
| `6` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `9` | `1` | `1` | `8563.698` | `1.906` |
| `7` | `fixed_book_quartile` | `` | `searched_single_book_split` | `6` | `1` | `2` | `8563.733` | `1.941` |
| `8` | `searched_single_book_split` | `18` | `searched_single_book_split` | `6` | `1` | `2` | `8564.087` | `2.296` |
| `9` | `fixed_book_quartile` | `` | `searched_single_book_split` | `6` | `1` | `1` | `8564.149` | `2.357` |
| `10` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `6` | `1` | `3` | `8564.259` | `2.467` |
| `11` | `searched_single_book_split` | `18` | `searched_single_book_split` | `6` | `1` | `1` | `8564.503` | `2.711` |
| `12` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `18` | `1` | `1` | `8564.735` | `2.943` |
| `13` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `18` | `1` | `2` | `8564.768` | `2.976` |
| `14` | `fixed_book_midpoint` | `` | `fixed_book_quartile` | `` | `1` | `1` | `8564.959` | `3.167` |
| `15` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `6` | `1` | `4` | `8564.994` | `3.202` |
| `16` | `fixed_book_quartile` | `` | `searched_single_book_split` | `9` | `1` | `2` | `8565.069` | `3.277` |
| `17` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `14` | `1` | `2` | `8565.304` | `3.512` |
| `18` | `searched_single_book_split` | `16` | `searched_single_book_split` | `6` | `1` | `2` | `8565.373` | `3.581` |
| `19` | `searched_single_book_split` | `18` | `searched_single_book_split` | `9` | `1` | `2` | `8565.423` | `3.631` |
| `20` | `fixed_book_quartile` | `` | `searched_single_book_split` | `4` | `1` | `2` | `8565.468` | `3.676` |

## Best Changed Pair

- Delta vs current: `0.415` bits
- Copy-length: `fixed_book_midpoint`
- Item-type: `searched_single_book_split` split `6`, order `1`, alpha `1`

## Best Pair With Both Components Changed

- Delta vs current: `2.357` bits
- Copy-length: `fixed_book_quartile`
- Item-type: `searched_single_book_split` split `6`, order `1`, alpha `1`

## Interpretation

No copy-length/item-type context pair beats the active book-midpoint
copy-length context plus searched item-type split at book `6`, order
`1`, alpha `2`. The best changed pair is still worse after
declaration cost.

## Boundary

This is a mechanical cost-ledger audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
