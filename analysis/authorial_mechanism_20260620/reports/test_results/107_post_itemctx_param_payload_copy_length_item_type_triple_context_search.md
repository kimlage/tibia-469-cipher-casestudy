# Post-Itemctx Param Payload/Copy-Length/Item-Type Triple Context Search

Verdict: `post_itemctx_param_payload_copy_length_item_type_triple_not_promoted`. Translation delta: `NONE`.

This audit combines the post-itemctx_param literal-payload, copy-length,
and item-type context frontiers. These are independent MDL components in
the current ledger, so the full triple space is proven by component
minima and the top triples are generated with a sorted heap. The top
triples are then checked by authoritative item-type rescoring plus
payload and copy-length deltas.

## Coverage

- Payload candidates: `77`
- Copy-length candidates: `79`
- Item-type candidates: `17024`
- Triple candidates proven by component minima: `103556992`

## Top Triples

| Rank | Payload | Copy | Copy split | Item | Item split | Order | Alpha | Total bits | Delta |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|
| `1` | `active_global` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `6` | `1` | `2` | `8561.792` | `0.000` |
| `2` | `active_global` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `6` | `1` | `1` | `8562.207` | `0.415` |
| `3` | `active_global` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `9` | `1` | `2` | `8563.127` | `1.335` |
| `4` | `active_global` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `4` | `1` | `2` | `8563.526` | `1.734` |
| `5` | `fixed_book_midpoint` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `6` | `1` | `2` | `8563.541` | `1.749` |
| `6` | `active_global` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `4` | `1` | `1` | `8563.674` | `1.882` |
| `7` | `active_global` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `9` | `1` | `1` | `8563.698` | `1.906` |
| `8` | `active_global` | `fixed_book_quartile` | `` | `searched_single_book_split` | `6` | `1` | `2` | `8563.733` | `1.941` |
| `9` | `fixed_book_midpoint` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `6` | `1` | `1` | `8563.956` | `2.164` |
| `10` | `active_global` | `searched_single_book_split` | `18` | `searched_single_book_split` | `6` | `1` | `2` | `8564.087` | `2.296` |
| `11` | `active_global` | `fixed_book_quartile` | `` | `searched_single_book_split` | `6` | `1` | `1` | `8564.149` | `2.357` |
| `12` | `active_global` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `6` | `1` | `3` | `8564.259` | `2.467` |
| `13` | `active_global` | `searched_single_book_split` | `18` | `searched_single_book_split` | `6` | `1` | `1` | `8564.503` | `2.711` |
| `14` | `active_global` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `18` | `1` | `1` | `8564.735` | `2.943` |
| `15` | `active_global` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `18` | `1` | `2` | `8564.768` | `2.976` |
| `16` | `fixed_book_midpoint` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `9` | `1` | `2` | `8564.876` | `3.084` |
| `17` | `active_global` | `fixed_book_midpoint` | `` | `fixed_book_quartile` | `` | `1` | `1` | `8564.959` | `3.167` |
| `18` | `active_global` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `6` | `1` | `4` | `8564.994` | `3.202` |
| `19` | `active_global` | `fixed_book_quartile` | `` | `searched_single_book_split` | `9` | `1` | `2` | `8565.069` | `3.277` |
| `20` | `fixed_book_midpoint` | `fixed_book_midpoint` | `` | `searched_single_book_split` | `4` | `1` | `2` | `8565.275` | `3.483` |

## Best Changed Triple

- Delta vs current: `0.415` bits
- Payload: `active_global`
- Copy-length: `fixed_book_midpoint`
- Item-type: `searched_single_book_split` split `6`, order `1`, alpha `1`

## Best Triple With All Three Components Changed

- Delta vs current: `4.106` bits
- Payload: `fixed_book_midpoint`
- Copy-length: `fixed_book_quartile`
- Item-type: `searched_single_book_split` split `6`, order `1`, alpha `1`

## Interpretation

No payload/copy-length/item-type context triple beats the active global
payload, book-midpoint copy-length context, and searched item-type split
at book `6`, order `1`, alpha `2`. The full triple space is closed by
the non-negative minima of the three complete component frontiers.

## Boundary

This is a mechanical cost-ledger audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
