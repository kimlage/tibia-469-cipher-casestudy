# Post-Itemctx Param Copy/Payload/Item Context-Alpha Triple Search

Verdict: `post_itemctx_param_copy_payload_item_context_alpha_triple_not_promoted`. Translation delta: `NONE`.

This audit combines the post-itemctx_param copy-length context/shared-alpha,
literal-payload context/shared-alpha, and item-type context/order/alpha
frontiers. These are independent MDL components in the current ledger,
so the full triple space is proven by component minima and the top triples
are generated with a sorted heap. The top triples are checked by
authoritative item-type rescoring plus copy and payload deltas.

## Coverage

- Copy-length context/alpha candidates: `5056`
- Literal-payload context/alpha candidates: `4928`
- Item-type candidates: `17024`
- Triple candidates proven by component minima: `424169439232`

## Top Triples

| Rank | Copy family | Copy alpha | Payload family | Payload alpha | Item family | Item split | Order | Alpha | Total bits | Delta |
|---:|---|---:|---|---:|---|---:|---:|---:|---:|---:|
| `1` | `fixed_book_midpoint` | `1` | `active_global` | `1` | `searched_single_book_split` | `6` | `1` | `2` | `8561.792` | `0.000` |
| `2` | `fixed_book_midpoint` | `1` | `active_global` | `1` | `searched_single_book_split` | `6` | `1` | `1` | `8562.207` | `0.415` |
| `3` | `fixed_book_midpoint` | `1` | `active_global` | `1` | `searched_single_book_split` | `9` | `1` | `2` | `8563.127` | `1.335` |
| `4` | `fixed_book_midpoint` | `1` | `active_global` | `1` | `searched_single_book_split` | `4` | `1` | `2` | `8563.526` | `1.734` |
| `5` | `fixed_book_midpoint` | `1` | `fixed_book_midpoint` | `1` | `searched_single_book_split` | `6` | `1` | `2` | `8563.541` | `1.749` |
| `6` | `fixed_book_midpoint` | `1` | `active_global` | `1` | `searched_single_book_split` | `4` | `1` | `1` | `8563.674` | `1.882` |
| `7` | `fixed_book_midpoint` | `1` | `active_global` | `1` | `searched_single_book_split` | `9` | `1` | `1` | `8563.698` | `1.906` |
| `8` | `fixed_book_quartile` | `1` | `active_global` | `1` | `searched_single_book_split` | `6` | `1` | `2` | `8563.733` | `1.941` |
| `9` | `fixed_book_midpoint` | `2` | `active_global` | `1` | `searched_single_book_split` | `6` | `1` | `2` | `8563.932` | `2.140` |
| `10` | `fixed_book_midpoint` | `1` | `fixed_book_midpoint` | `1` | `searched_single_book_split` | `6` | `1` | `1` | `8563.956` | `2.164` |
| `11` | `searched_single_book_split` | `1` | `active_global` | `1` | `searched_single_book_split` | `6` | `1` | `2` | `8564.087` | `2.296` |
| `12` | `fixed_book_quartile` | `1` | `active_global` | `1` | `searched_single_book_split` | `6` | `1` | `1` | `8564.149` | `2.357` |
| `13` | `fixed_book_midpoint` | `1` | `active_global` | `1` | `searched_single_book_split` | `6` | `1` | `3` | `8564.259` | `2.467` |
| `14` | `fixed_book_midpoint` | `2` | `active_global` | `1` | `searched_single_book_split` | `6` | `1` | `1` | `8564.347` | `2.555` |
| `15` | `searched_single_book_split` | `1` | `active_global` | `1` | `searched_single_book_split` | `6` | `1` | `1` | `8564.503` | `2.711` |
| `16` | `fixed_book_midpoint` | `1` | `active_global` | `1` | `searched_single_book_split` | `18` | `1` | `1` | `8564.735` | `2.943` |
| `17` | `fixed_book_midpoint` | `1` | `active_global` | `1` | `searched_single_book_split` | `18` | `1` | `2` | `8564.768` | `2.976` |
| `18` | `fixed_book_midpoint` | `1` | `fixed_book_midpoint` | `1` | `searched_single_book_split` | `9` | `1` | `2` | `8564.876` | `3.084` |
| `19` | `fixed_book_midpoint` | `1` | `active_global` | `1` | `fixed_book_quartile` | `` | `1` | `1` | `8564.959` | `3.167` |
| `20` | `fixed_book_midpoint` | `1` | `active_global` | `1` | `searched_single_book_split` | `6` | `1` | `4` | `8564.994` | `3.202` |

## Best Changed Triple

- Delta vs current: `0.415` bits
- Copy: `fixed_book_midpoint`, alpha `1`
- Payload: `active_global`, alpha `1`
- Item-type: `searched_single_book_split`, order `1`, alpha `1`

## Best Triple With All Three Components Changed

- Delta vs current: `4.106` bits
- Copy: `fixed_book_quartile`, alpha `1`
- Payload: `fixed_book_midpoint`, alpha `1`
- Item-type: `searched_single_book_split`, order `1`, alpha `1`

## Interpretation

No copy/payload/item context-alpha triple beats the active
book-midpoint copy-length `alpha=1`, global payload `alpha=1`, and
searched item-type split at book `6`, order `1`, alpha `2`. The full
triple space is closed by the non-negative minima of the three complete
component frontiers.

## Boundary

This is a mechanical cost-ledger audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
