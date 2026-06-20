# Post-Itemctx Param Copy/Payload Context-Alpha Pair Search

Verdict: `post_itemctx_param_copy_payload_context_alpha_pair_not_promoted`. Translation delta: `NONE`.

This audit combines the post-itemctx_param copy-length context/shared-alpha
frontier with the literal-payload context/shared-alpha frontier. These
are independent MDL components in the current ledger, so the full pair
space is proven by component minima and the top pairs are generated with
a sorted heap.

## Coverage

- Copy-length context/alpha candidates: `5056`
- Literal-payload context/alpha candidates: `4928`
- Pair candidates proven by component minima: `24915968`

## Top Pairs

| Rank | Copy family | Copy split | Copy alpha | Payload family | Payload split | Payload alpha | Total bits | Delta |
|---:|---|---:|---:|---|---:|---:|---:|---:|
| `1` | `fixed_book_midpoint` | `` | `1` | `active_global` | `` | `1` | `8561.792` | `0.000` |
| `2` | `fixed_book_midpoint` | `` | `1` | `fixed_book_midpoint` | `` | `1` | `8563.541` | `1.749` |
| `3` | `fixed_book_quartile` | `` | `1` | `active_global` | `` | `1` | `8563.733` | `1.941` |
| `4` | `fixed_book_midpoint` | `` | `2` | `active_global` | `` | `1` | `8563.932` | `2.140` |
| `5` | `searched_single_book_split` | `18` | `1` | `active_global` | `` | `1` | `8564.087` | `2.296` |
| `6` | `searched_single_book_split` | `16` | `1` | `active_global` | `` | `1` | `8565.373` | `3.581` |
| `7` | `fixed_book_quartile` | `` | `1` | `fixed_book_midpoint` | `` | `1` | `8565.482` | `3.690` |
| `8` | `copy_index_midpoint` | `` | `1` | `active_global` | `` | `1` | `8565.493` | `3.701` |
| `9` | `fixed_book_midpoint` | `` | `2` | `fixed_book_midpoint` | `` | `1` | `8565.681` | `3.889` |
| `10` | `searched_single_book_split` | `18` | `1` | `fixed_book_midpoint` | `` | `1` | `8565.836` | `4.044` |
| `11` | `searched_single_book_split` | `19` | `1` | `active_global` | `` | `1` | `8565.911` | `4.119` |
| `12` | `searched_single_book_split` | `15` | `1` | `active_global` | `` | `1` | `8567.038` | `5.247` |
| `13` | `searched_single_book_split` | `17` | `1` | `active_global` | `` | `1` | `8567.076` | `5.284` |
| `14` | `searched_single_book_split` | `16` | `1` | `fixed_book_midpoint` | `` | `1` | `8567.122` | `5.330` |
| `15` | `copy_index_midpoint` | `` | `1` | `fixed_book_midpoint` | `` | `1` | `8567.242` | `5.450` |
| `16` | `searched_single_book_split` | `19` | `1` | `fixed_book_midpoint` | `` | `1` | `8567.660` | `5.868` |
| `17` | `copy_index_midpoint` | `` | `2` | `active_global` | `` | `1` | `8567.673` | `5.881` |
| `18` | `searched_single_book_split` | `37` | `1` | `active_global` | `` | `1` | `8567.839` | `6.047` |
| `19` | `searched_single_book_split` | `15` | `1` | `fixed_book_midpoint` | `` | `1` | `8568.787` | `6.995` |
| `20` | `searched_single_book_split` | `17` | `1` | `fixed_book_midpoint` | `` | `1` | `8568.825` | `7.033` |

## Best Changed Pair

- Delta vs current: `1.749` bits
- Copy: `fixed_book_midpoint`, alpha `1`
- Payload: `fixed_book_midpoint`, alpha `1`

## Best Pair With Both Components Changed

- Delta vs current: `3.690` bits
- Copy: `fixed_book_quartile`, alpha `1`
- Payload: `fixed_book_midpoint`, alpha `1`

## Interpretation

No copy-length context-alpha / literal-payload context-alpha pair beats
the active book-midpoint copy-length `alpha=1` model and global
literal-payload `alpha=1` model. The full pair space is closed by the
non-negative minima of the two complete component frontiers.

## Boundary

This is a mechanical cost-ledger audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
