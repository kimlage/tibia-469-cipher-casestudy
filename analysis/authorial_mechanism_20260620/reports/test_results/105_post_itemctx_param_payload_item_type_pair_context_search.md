# Post-Itemctx Param Payload/Item-Type Pair Context Search

Verdict: `post_itemctx_param_payload_item_type_pair_not_promoted`. Translation delta: `NONE`.

This audit combines the post-itemctx_param literal-payload context
frontier with the post-itemctx_param item-type context-family frontier.
Payload and item-type costs are independent MDL components here, so all
pairs are enumerated by summed component deltas and the top pairs are
checked by authoritative item-type rescoring plus payload delta.

## Coverage

- Payload candidates: `77`
- Item-type candidates: `17024`
- Pair candidates: `1310848`

## Top Pairs

| Rank | Payload family | Payload split | Item family | Item split | Order | Alpha | Total bits | Delta |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| `1` | `active_global` | `` | `searched_single_book_split` | `6` | `1` | `2` | `8561.792` | `0.000` |
| `2` | `active_global` | `` | `searched_single_book_split` | `6` | `1` | `1` | `8562.207` | `0.415` |
| `3` | `active_global` | `` | `searched_single_book_split` | `9` | `1` | `2` | `8563.127` | `1.335` |
| `4` | `active_global` | `` | `searched_single_book_split` | `4` | `1` | `2` | `8563.526` | `1.734` |
| `5` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `6` | `1` | `2` | `8563.541` | `1.749` |
| `6` | `active_global` | `` | `searched_single_book_split` | `4` | `1` | `1` | `8563.674` | `1.882` |
| `7` | `active_global` | `` | `searched_single_book_split` | `9` | `1` | `1` | `8563.698` | `1.906` |
| `8` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `6` | `1` | `1` | `8563.956` | `2.164` |
| `9` | `active_global` | `` | `searched_single_book_split` | `6` | `1` | `3` | `8564.259` | `2.467` |
| `10` | `active_global` | `` | `searched_single_book_split` | `18` | `1` | `1` | `8564.735` | `2.943` |
| `11` | `active_global` | `` | `searched_single_book_split` | `18` | `1` | `2` | `8564.768` | `2.976` |
| `12` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `9` | `1` | `2` | `8564.876` | `3.084` |
| `13` | `active_global` | `` | `fixed_book_quartile` | `` | `1` | `1` | `8564.959` | `3.167` |
| `14` | `active_global` | `` | `searched_single_book_split` | `6` | `1` | `4` | `8564.994` | `3.202` |
| `15` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `4` | `1` | `2` | `8565.275` | `3.483` |
| `16` | `active_global` | `` | `searched_single_book_split` | `14` | `1` | `2` | `8565.304` | `3.512` |
| `17` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `4` | `1` | `1` | `8565.423` | `3.631` |
| `18` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `9` | `1` | `1` | `8565.447` | `3.655` |
| `19` | `active_global` | `` | `searched_single_book_split` | `9` | `1` | `3` | `8565.496` | `3.704` |
| `20` | `active_global` | `` | `searched_single_book_split` | `5` | `1` | `2` | `8565.626` | `3.834` |

## Best Changed Pair

- Delta vs current: `0.415` bits
- Payload: `active_global`
- Item-type: `searched_single_book_split` split `6`, order `1`, alpha `1`

## Best Pair With Both Components Changed

- Delta vs current: `2.164` bits
- Payload: `fixed_book_midpoint`
- Item-type: `searched_single_book_split` split `6`, order `1`, alpha `1`

## Interpretation

No payload/item-type context pair beats the active searched split at
book `6`, order `1`, alpha `2` with the active global literal-payload
model. The best changed pair is still worse after declaration cost.

## Boundary

This is a mechanical cost-ledger audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
