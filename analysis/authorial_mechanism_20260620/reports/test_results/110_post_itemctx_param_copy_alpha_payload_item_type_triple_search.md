# Post-Itemctx Param Copy-Alpha/Payload/Item-Type Triple Search

Verdict: `post_itemctx_param_copy_alpha_payload_item_type_triple_not_promoted`. Translation delta: `NONE`.

This audit combines the post-itemctx_param copy-length alpha-by-context,
literal-payload context, and item-type context frontiers. These are
independent MDL components in the current ledger, so the full triple space
is proven by component minima and the top triples are generated with a
sorted heap. The top triples are then checked by authoritative item-type
rescoring plus copy-alpha and payload deltas.

## Coverage

- Copy-length alpha candidates: `4097`
- Payload candidates: `77`
- Item-type candidates: `17024`
- Triple candidates proven by component minima: `5370544256`

## Top Triples

| Rank | Copy alpha | Payload | Item family | Item split | Order | Alpha | Total bits | Delta |
|---:|---|---|---|---:|---:|---:|---:|---:|
| `1` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `searched_single_book_split` | `6` | `1` | `2` | `8561.792` | `0.000` |
| `2` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `searched_single_book_split` | `6` | `1` | `1` | `8562.207` | `0.415` |
| `3` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `searched_single_book_split` | `9` | `1` | `2` | `8563.127` | `1.335` |
| `4` | `{'first_half': 1, 'second_half': 2}` | `active_global` | `searched_single_book_split` | `6` | `1` | `2` | `8563.181` | `1.389` |
| `5` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `searched_single_book_split` | `4` | `1` | `2` | `8563.526` | `1.734` |
| `6` | `{'first_half': 1, 'second_half': 1}` | `fixed_book_midpoint` | `searched_single_book_split` | `6` | `1` | `2` | `8563.541` | `1.749` |
| `7` | `{'first_half': 1, 'second_half': 2}` | `active_global` | `searched_single_book_split` | `6` | `1` | `1` | `8563.596` | `1.804` |
| `8` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `searched_single_book_split` | `4` | `1` | `1` | `8563.674` | `1.882` |
| `9` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `searched_single_book_split` | `9` | `1` | `1` | `8563.698` | `1.906` |
| `10` | `{'first_half': 1, 'second_half': 1}` | `fixed_book_midpoint` | `searched_single_book_split` | `6` | `1` | `1` | `8563.956` | `2.164` |
| `11` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `searched_single_book_split` | `6` | `1` | `3` | `8564.259` | `2.467` |
| `12` | `{'first_half': 1, 'second_half': 2}` | `active_global` | `searched_single_book_split` | `9` | `1` | `2` | `8564.516` | `2.724` |
| `13` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `searched_single_book_split` | `18` | `1` | `1` | `8564.735` | `2.943` |
| `14` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `searched_single_book_split` | `18` | `1` | `2` | `8564.768` | `2.976` |
| `15` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `searched_single_book_split` | `6` | `1` | `2` | `8564.792` | `3.000` |
| `16` | `{'first_half': 1, 'second_half': 1}` | `fixed_book_midpoint` | `searched_single_book_split` | `9` | `1` | `2` | `8564.876` | `3.084` |
| `17` | `{'first_half': 1, 'second_half': 2}` | `active_global` | `searched_single_book_split` | `4` | `1` | `2` | `8564.915` | `3.123` |
| `18` | `{'first_half': 1, 'second_half': 2}` | `fixed_book_midpoint` | `searched_single_book_split` | `6` | `1` | `2` | `8564.930` | `3.138` |
| `19` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `fixed_book_quartile` | `` | `1` | `1` | `8564.959` | `3.167` |
| `20` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `searched_single_book_split` | `6` | `1` | `4` | `8564.994` | `3.202` |

## Best Changed Triple

- Delta vs current: `0.415` bits
- Copy alpha: `{'first_half': 1, 'second_half': 1}`
- Payload: `active_global`
- Item-type: `searched_single_book_split` split `6`, order `1`, alpha `1`

## Best Triple With All Three Components Changed

- Delta vs current: `3.553` bits
- Copy alpha: `{'first_half': 1, 'second_half': 2}`
- Payload: `fixed_book_midpoint`
- Item-type: `searched_single_book_split` split `6`, order `1`, alpha `1`

## Interpretation

No copy-alpha/payload/item-type triple beats the active shared
copy-length alpha `1`, global payload, and searched item-type split
at book `6`, order `1`, alpha `2`. The full triple space is closed by
the non-negative minima of the three complete component frontiers.

## Boundary

This is a mechanical cost-ledger audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
