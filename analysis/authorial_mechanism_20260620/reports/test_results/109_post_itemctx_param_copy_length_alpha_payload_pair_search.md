# Post-Itemctx Param Copy-Length Alpha/Payload Pair Search

Verdict: `post_itemctx_param_copy_length_alpha_payload_pair_not_promoted`. Translation delta: `NONE`.

This audit combines the post-itemctx_param midpoint copy-length
alpha-by-context grid with the post-itemctx_param literal-payload context
frontier. The two costs are independent MDL components here, so the full
pair space is proven by component minima and the top pairs are generated
with a sorted heap.

## Coverage

- Copy-length alpha candidates: `4097`
- Payload candidates: `77`
- Pair candidates proven by component minima: `315469`

## Top Pairs

| Rank | Copy alpha by context | Payload family | Payload split | Total bits | Delta |
|---:|---|---|---:|---:|---:|
| `1` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `` | `8561.792` | `0.000` |
| `2` | `{'first_half': 1, 'second_half': 2}` | `active_global` | `` | `8563.181` | `1.389` |
| `3` | `{'first_half': 1, 'second_half': 1}` | `fixed_book_midpoint` | `` | `8563.541` | `1.749` |
| `4` | `{'first_half': 1, 'second_half': 1}` | `active_global` | `` | `8564.792` | `3.000` |
| `5` | `{'first_half': 1, 'second_half': 2}` | `fixed_book_midpoint` | `` | `8564.930` | `3.138` |
| `6` | `{'first_half': 1, 'second_half': 3}` | `active_global` | `` | `8565.703` | `3.911` |
| `7` | `{'first_half': 1, 'second_half': 4}` | `active_global` | `` | `8566.357` | `4.565` |
| `8` | `{'first_half': 1, 'second_half': 1}` | `fixed_book_midpoint` | `` | `8566.541` | `4.749` |
| `9` | `{'first_half': 1, 'second_half': 5}` | `active_global` | `` | `8566.928` | `5.136` |
| `10` | `{'first_half': 2, 'second_half': 2}` | `active_global` | `` | `8566.932` | `5.140` |
| `11` | `{'first_half': 1, 'second_half': 6}` | `active_global` | `` | `8567.402` | `5.610` |
| `12` | `{'first_half': 1, 'second_half': 3}` | `fixed_book_midpoint` | `` | `8567.451` | `5.659` |
| `13` | `{'first_half': 1, 'second_half': 4}` | `fixed_book_midpoint` | `` | `8568.106` | `6.314` |
| `14` | `{'first_half': 2, 'second_half': 1}` | `active_global` | `` | `8568.543` | `6.751` |
| `15` | `{'first_half': 1, 'second_half': 5}` | `fixed_book_midpoint` | `` | `8568.677` | `6.885` |
| `16` | `{'first_half': 2, 'second_half': 2}` | `fixed_book_midpoint` | `` | `8568.681` | `6.889` |
| `17` | `{'first_half': 1, 'second_half': 6}` | `fixed_book_midpoint` | `` | `8569.151` | `7.359` |
| `18` | `{'first_half': 2, 'second_half': 3}` | `active_global` | `` | `8569.454` | `7.662` |
| `19` | `{'first_half': 1, 'second_half': 7}` | `active_global` | `` | `8569.793` | `8.001` |
| `20` | `{'first_half': 2, 'second_half': 4}` | `active_global` | `` | `8570.108` | `8.316` |

## Best Changed Pair

- Delta vs current: `1.389` bits
- Copy alpha: `{'first_half': 1, 'second_half': 2}`
- Payload: `active_global`

## Best Pair With Both Components Changed

- Delta vs current: `3.138` bits
- Copy alpha: `{'first_half': 1, 'second_half': 2}`
- Payload: `fixed_book_midpoint`

## Interpretation

No copy-length alpha/payload pair beats the active shared copy-length
alpha `1` and global literal-payload model. The full pair space is
closed by the non-negative minima of the two complete component
frontiers.

## Boundary

This is a mechanical cost-ledger audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
