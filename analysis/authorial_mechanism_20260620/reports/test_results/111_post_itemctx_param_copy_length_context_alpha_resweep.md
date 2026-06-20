# Post-Itemctx Param Copy-Length Context/Alpha Resweep

Verdict: `post_itemctx_param_copy_length_context_alpha_not_promoted`. Translation delta: `NONE`.

This audit closes the gap between the post-itemctx_param copy-length
context resweep and the midpoint alpha grid. It retests the same
copy-length context families as the context resweep, but sweeps a shared
`alpha=1..64` for each context. Context, alpha, and searched split
declaration bits are charged. The recipe, source-address ledger, payload
model, item-type model, forced rules, and book-length ledger are fixed.

## Coverage

- Copy-length context candidates: `79`
- Shared alpha values per context: `64`
- Context/alpha candidates tested: `5056`

## Top Models

| Rank | Model | Family | Split | Alpha | Contexts | Length bits | Model bits | Total bits | Delta |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| `1` | `active_book_midpoint_35_context` | `fixed_book_midpoint` | `` | `1` | `2` | `1631.494` | `12` | `8561.792` | `0.000` |
| `2` | `book_quartile_context` | `fixed_book_quartile` | `` | `1` | `4` | `1631.436` | `14` | `8563.733` | `1.941` |
| `3` | `active_book_midpoint_35_context` | `fixed_book_midpoint` | `` | `2` | `2` | `1633.634` | `12` | `8563.932` | `2.140` |
| `4` | `searched_single_book_split_context` | `searched_single_book_split` | `18` | `1` | `2` | `1624.790` | `21` | `8564.087` | `2.296` |
| `5` | `searched_single_book_split_context` | `searched_single_book_split` | `16` | `1` | `2` | `1626.075` | `21` | `8565.373` | `3.581` |
| `6` | `copy_index_midpoint_context` | `copy_index_midpoint` | `` | `1` | `2` | `1635.195` | `12` | `8565.493` | `3.701` |
| `7` | `searched_single_book_split_context` | `searched_single_book_split` | `19` | `1` | `2` | `1626.613` | `21` | `8565.911` | `4.119` |
| `8` | `searched_single_book_split_context` | `searched_single_book_split` | `15` | `1` | `2` | `1627.741` | `21` | `8567.038` | `5.247` |
| `9` | `searched_single_book_split_context` | `searched_single_book_split` | `17` | `1` | `2` | `1627.778` | `21` | `8567.076` | `5.284` |
| `10` | `copy_index_midpoint_context` | `copy_index_midpoint` | `` | `2` | `2` | `1637.376` | `12` | `8567.673` | `5.881` |
| `11` | `searched_single_book_split_context` | `searched_single_book_split` | `37` | `1` | `2` | `1626.541` | `23` | `8567.839` | `6.047` |
| `12` | `searched_single_book_split_context` | `searched_single_book_split` | `38` | `1` | `2` | `1627.972` | `23` | `8569.270` | `7.478` |
| `13` | `searched_single_book_split_context` | `searched_single_book_split` | `40` | `1` | `2` | `1628.064` | `23` | `8569.362` | `7.570` |
| `14` | `searched_single_book_split_context` | `searched_single_book_split` | `18` | `2` | `2` | `1630.327` | `21` | `8569.625` | `7.833` |
| `15` | `searched_single_book_split_context` | `searched_single_book_split` | `21` | `1` | `2` | `1630.557` | `21` | `8569.855` | `8.063` |
| `16` | `searched_single_book_split_context` | `searched_single_book_split` | `41` | `1` | `2` | `1628.610` | `23` | `8569.908` | `8.116` |
| `17` | `searched_single_book_split_context` | `searched_single_book_split` | `16` | `2` | `2` | `1630.921` | `21` | `8570.219` | `8.427` |
| `18` | `searched_single_book_split_context` | `searched_single_book_split` | `37` | `2` | `2` | `1629.071` | `23` | `8570.369` | `8.577` |
| `19` | `searched_single_book_split_context` | `searched_single_book_split` | `61` | `2` | `2` | `1629.412` | `23` | `8570.710` | `8.918` |
| `20` | `searched_single_book_split_context` | `searched_single_book_split` | `19` | `2` | `2` | `1631.475` | `21` | `8570.773` | `8.981` |

## Best Changed Model

- Delta vs current: `1.941` bits
- Model: `book_quartile_context`
- Family: `fixed_book_quartile`
- Split: ``
- Alpha: `1`

## Best Context-Changed Model

- Delta vs current: `1.941` bits
- Model: `book_quartile_context`
- Family: `fixed_book_quartile`
- Split: ``
- Alpha: `1`

## Best Alpha Change On Active Context

- Delta vs current: `2.140` bits
- Alpha: `2`

## Interpretation

No copy-length context/shared-alpha candidate beats the active fixed
book-midpoint context with shared `alpha=1`. The active context remains
the complete minimum after declaration costs.

## Boundary

This is a mechanical copy-length cost-ledger audit only. It does not
alter row0, introduce plaintext, or make an authorial-intent claim.
