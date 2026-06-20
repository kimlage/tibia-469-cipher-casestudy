# Post-Itemctx Param Item-Type Context Family Search

Verdict: `post_itemctx_param_item_type_context_family_not_promoted`. Translation delta: `NONE`.

This audit retests item-type extra-context families after the itemctx_param
promotion. For each decodable family it sweeps item-type context order
`1..7` and alpha `1..32`, charging family, searched-split, order, alpha,
and forced-rule declaration bits. The recipe, payload model, copy-address
ledger, copy-length model, forced rules, and book-length ledger are fixed.

## Top Models

| Rank | Family | Split | Order | Alpha | Total bits | Delta | Stream bits | Model bits |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `1` | `searched_single_book_split` | `6` | `1` | `2` | `8561.792` | `0.000` | `223.412` | `14` |
| `2` | `searched_single_book_split` | `6` | `1` | `1` | `8562.207` | `0.415` | `223.827` | `14` |
| `3` | `searched_single_book_split` | `9` | `1` | `2` | `8563.127` | `1.335` | `222.747` | `16` |
| `4` | `searched_single_book_split` | `4` | `1` | `2` | `8563.526` | `1.734` | `225.146` | `14` |
| `5` | `searched_single_book_split` | `4` | `1` | `1` | `8563.674` | `1.882` | `225.294` | `14` |
| `6` | `searched_single_book_split` | `9` | `1` | `1` | `8563.698` | `1.906` | `223.318` | `16` |
| `7` | `searched_single_book_split` | `6` | `1` | `3` | `8564.259` | `2.467` | `223.879` | `16` |
| `8` | `searched_single_book_split` | `18` | `1` | `1` | `8564.735` | `2.943` | `222.355` | `18` |
| `9` | `searched_single_book_split` | `18` | `1` | `2` | `8564.768` | `2.976` | `222.388` | `18` |
| `10` | `fixed_book_quartile` | `` | `1` | `1` | `8564.959` | `3.167` | `229.579` | `11` |
| `11` | `searched_single_book_split` | `6` | `1` | `4` | `8564.994` | `3.202` | `224.614` | `16` |
| `12` | `searched_single_book_split` | `14` | `1` | `2` | `8565.304` | `3.512` | `224.924` | `16` |
| `13` | `searched_single_book_split` | `9` | `1` | `3` | `8565.496` | `3.704` | `223.116` | `18` |
| `14` | `searched_single_book_split` | `5` | `1` | `2` | `8565.626` | `3.834` | `227.246` | `14` |
| `15` | `searched_single_book_split` | `14` | `1` | `1` | `8565.715` | `3.923` | `225.335` | `16` |
| `16` | `searched_single_book_split` | `10` | `1` | `2` | `8565.733` | `3.941` | `225.353` | `16` |
| `17` | `searched_single_book_split` | `6` | `1` | `5` | `8565.831` | `4.039` | `225.451` | `16` |
| `18` | `searched_single_book_split` | `19` | `1` | `1` | `8566.098` | `4.306` | `223.718` | `18` |
| `19` | `searched_single_book_split` | `19` | `1` | `2` | `8566.111` | `4.320` | `223.731` | `18` |
| `20` | `searched_single_book_split` | `4` | `1` | `3` | `8566.153` | `4.361` | `225.773` | `16` |

## Best By Family

| Family | Split | Order | Alpha | Total bits | Delta |
|---|---:|---:|---:|---:|---:|
| `searched_single_book_split` | `6` | `1` | `2` | `8561.792` | `0.000` |
| `searched_single_book_split` | `9` | `1` | `2` | `8563.127` | `1.335` |
| `searched_single_book_split` | `4` | `1` | `2` | `8563.526` | `1.734` |
| `searched_single_book_split` | `18` | `1` | `1` | `8564.735` | `2.943` |
| `fixed_book_quartile` | `` | `1` | `1` | `8564.959` | `3.167` |
| `searched_single_book_split` | `14` | `1` | `2` | `8565.304` | `3.512` |
| `searched_single_book_split` | `5` | `1` | `2` | `8565.626` | `3.834` |
| `searched_single_book_split` | `10` | `1` | `2` | `8565.733` | `3.941` |
| `searched_single_book_split` | `19` | `1` | `1` | `8566.098` | `4.306` |
| `searched_single_book_split` | `13` | `1` | `2` | `8566.935` | `5.143` |
| `searched_single_book_split` | `3` | `1` | `1` | `8567.565` | `5.773` |
| `searched_single_book_split` | `8` | `1` | `2` | `8567.729` | `5.937` |
| `searched_single_book_split` | `12` | `1` | `2` | `8568.014` | `6.222` |
| `searched_single_book_split` | `20` | `1` | `2` | `8568.054` | `6.262` |
| `searched_single_book_split` | `7` | `1` | `2` | `8568.858` | `7.066` |
| `searched_single_book_split` | `11` | `1` | `2` | `8568.982` | `7.190` |
| `searched_single_book_split` | `17` | `1` | `2` | `8569.157` | `7.365` |
| `searched_single_book_split` | `15` | `1` | `2` | `8569.444` | `7.652` |
| `searched_single_book_split` | `26` | `1` | `1` | `8570.353` | `8.561` |
| `searched_single_book_split` | `24` | `1` | `1` | `8570.437` | `8.645` |

## Interpretation

An item-type context family is promoted only if its stream savings survive
the charged family/order/alpha declaration bits and the authoritative
scorer validates 70/70 roundtrip. Otherwise the active searched split at
book `6`, order `1`, alpha `2` remains the current formula.

## Boundary

This is a mechanical item-type ledger audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
