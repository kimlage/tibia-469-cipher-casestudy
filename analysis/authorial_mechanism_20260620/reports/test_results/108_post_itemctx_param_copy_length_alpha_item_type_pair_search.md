# Post-Itemctx Param Copy-Length Alpha/Item-Type Pair Search

Verdict: `post_itemctx_param_copy_length_alpha_item_type_pair_not_promoted`. Translation delta: `NONE`.

This audit combines the post-itemctx_param midpoint copy-length
alpha-by-context grid with the post-itemctx_param item-type context-family
frontier. The two costs are independent MDL components here, so the full
pair space is proven by component minima and the top pairs are generated
with a sorted heap. The top pairs are then checked by authoritative
item-type rescoring plus copy-length alpha delta.

## Coverage

- Copy-length alpha candidates: `4097`
- Item-type candidates: `17024`
- Pair candidates proven by component minima: `69747328`

## Top Pairs

| Rank | Copy alpha by context | Item family | Item split | Order | Alpha | Total bits | Delta |
|---:|---|---|---:|---:|---:|---:|---:|
| `1` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `6` | `1` | `2` | `8561.792` | `0.000` |
| `2` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `6` | `1` | `1` | `8562.207` | `0.415` |
| `3` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `9` | `1` | `2` | `8563.127` | `1.335` |
| `4` | `{'first_half': 1, 'second_half': 2}` | `searched_single_book_split` | `6` | `1` | `2` | `8563.181` | `1.389` |
| `5` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `4` | `1` | `2` | `8563.526` | `1.734` |
| `6` | `{'first_half': 1, 'second_half': 2}` | `searched_single_book_split` | `6` | `1` | `1` | `8563.596` | `1.804` |
| `7` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `4` | `1` | `1` | `8563.674` | `1.882` |
| `8` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `9` | `1` | `1` | `8563.698` | `1.906` |
| `9` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `6` | `1` | `3` | `8564.259` | `2.467` |
| `10` | `{'first_half': 1, 'second_half': 2}` | `searched_single_book_split` | `9` | `1` | `2` | `8564.516` | `2.724` |
| `11` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `18` | `1` | `1` | `8564.735` | `2.943` |
| `12` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `18` | `1` | `2` | `8564.768` | `2.976` |
| `13` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `6` | `1` | `2` | `8564.792` | `3.000` |
| `14` | `{'first_half': 1, 'second_half': 2}` | `searched_single_book_split` | `4` | `1` | `2` | `8564.915` | `3.123` |
| `15` | `{'first_half': 1, 'second_half': 1}` | `fixed_book_quartile` | `` | `1` | `1` | `8564.959` | `3.167` |
| `16` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `6` | `1` | `4` | `8564.994` | `3.202` |
| `17` | `{'first_half': 1, 'second_half': 2}` | `searched_single_book_split` | `4` | `1` | `1` | `8565.063` | `3.271` |
| `18` | `{'first_half': 1, 'second_half': 2}` | `searched_single_book_split` | `9` | `1` | `1` | `8565.086` | `3.294` |
| `19` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `6` | `1` | `1` | `8565.207` | `3.415` |
| `20` | `{'first_half': 1, 'second_half': 1}` | `searched_single_book_split` | `14` | `1` | `2` | `8565.304` | `3.512` |

## Best Changed Pair

- Delta vs current: `0.415` bits
- Copy alpha: `{'first_half': 1, 'second_half': 1}`
- Item-type: `searched_single_book_split` split `6`, order `1`, alpha `1`

## Best Pair With Both Components Changed

- Delta vs current: `1.804` bits
- Copy alpha: `{'first_half': 1, 'second_half': 2}`
- Item-type: `searched_single_book_split` split `6`, order `1`, alpha `1`

## Interpretation

No copy-length alpha/item-type pair beats the active shared copy-length
alpha `1` and searched item-type split at book `6`, order `1`, alpha
`2`. The full pair space is closed by the non-negative minima of the
two complete component frontiers.

## Boundary

This is a mechanical cost-ledger audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
