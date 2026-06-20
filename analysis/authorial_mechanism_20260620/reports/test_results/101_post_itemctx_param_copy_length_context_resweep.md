# Post-Itemctx Param Copy-Length Context Resweep

Verdict: `post_itemctx_param_copy_length_context_retains_midpoint`. Translation delta: `NONE`.

This audit retests copy-length contexts after the itemctx_param
promotion. The recipe, source-address ledger, copy order, payload model,
item-type model, forced rules, book-length ledger, and alpha=1 are fixed.

## Top Context Models

| Rank | Model | Family | Total bits | Delta | Component delta | Declaration delta | Contexts |
|---:|---|---|---:|---:|---:|---:|---:|
| `1` | `active_book_midpoint_35_context` | `fixed_book_midpoint` | `8561.792` | `0.000` | `0.000` | `0` | `2` |
| `2` | `book_quartile_context` | `fixed_book_quartile` | `8563.733` | `1.941` | `-0.059` | `2` | `4` |
| `3` | `searched_single_book_split_context@18` | `searched_single_book_split` | `8564.087` | `2.296` | `-6.704` | `9` | `2` |
| `4` | `searched_single_book_split_context@16` | `searched_single_book_split` | `8565.373` | `3.581` | `-5.419` | `9` | `2` |
| `5` | `copy_index_midpoint_context` | `copy_index_midpoint` | `8565.493` | `3.701` | `3.701` | `0` | `2` |
| `6` | `searched_single_book_split_context@19` | `searched_single_book_split` | `8565.911` | `4.119` | `-4.881` | `9` | `2` |
| `7` | `searched_single_book_split_context@15` | `searched_single_book_split` | `8567.038` | `5.247` | `-3.753` | `9` | `2` |
| `8` | `searched_single_book_split_context@17` | `searched_single_book_split` | `8567.076` | `5.284` | `-3.716` | `9` | `2` |
| `9` | `searched_single_book_split_context@37` | `searched_single_book_split` | `8567.839` | `6.047` | `-4.953` | `11` | `2` |
| `10` | `searched_single_book_split_context@38` | `searched_single_book_split` | `8569.270` | `7.478` | `-3.522` | `11` | `2` |
| `11` | `searched_single_book_split_context@40` | `searched_single_book_split` | `8569.362` | `7.570` | `-3.430` | `11` | `2` |
| `12` | `searched_single_book_split_context@21` | `searched_single_book_split` | `8569.855` | `8.063` | `-0.937` | `9` | `2` |

## Interpretation

The active fixed book-midpoint context remains promoted unless another
declared, decodable context beats it after declaration bits. This is a
mechanical copy-length context audit only; it does not alter row0,
introduce plaintext, or make an authorial-intent claim.
