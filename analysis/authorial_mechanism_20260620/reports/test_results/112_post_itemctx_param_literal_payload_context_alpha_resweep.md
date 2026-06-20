# Post-Itemctx Param Literal Payload Context/Alpha Resweep

Verdict: `post_itemctx_param_literal_payload_context_alpha_not_promoted`. Translation delta: `NONE`.

This audit closes the gap between the post-itemctx_param literal-payload
context search and the payload alpha parameter. It retests the same
literal-payload context families as the context search, but sweeps a
shared `alpha=1..64` for each context. Family, order, alpha, context,
and searched-split declaration bits are charged. The recipe, literal-run
length model, copy-address ledger, copy-length model, item-type model,
forced rules, and book-length ledger are fixed.

## Coverage

- Literal-payload context candidates: `77`
- Shared alpha values per context: `64`
- Context/alpha candidates tested: `4928`

## Top Models

| Rank | Model | Family | Split | Alpha | Contexts | Payload bits | Model bits | Total bits | Delta |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| `1` | `active_global_literal_payload_context` | `active_global` | `` | `1` | `1` | `2434.095` | `9` | `8561.792` | `0.000` |
| `2` | `book_midpoint_35_literal_payload_context` | `fixed_book_midpoint` | `` | `1` | `2` | `2431.844` | `13` | `8563.541` | `1.749` |
| `3` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `39` | `1` | `2` | `2430.708` | `24` | `8573.405` | `11.613` |
| `4` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `40` | `1` | `2` | `2431.087` | `24` | `8573.784` | `11.992` |
| `5` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `35` | `1` | `2` | `2431.844` | `24` | `8574.541` | `12.749` |
| `6` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `36` | `1` | `2` | `2431.844` | `24` | `8574.541` | `12.749` |
| `7` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `37` | `1` | `2` | `2431.844` | `24` | `8574.541` | `12.749` |
| `8` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `38` | `1` | `2` | `2431.844` | `24` | `8574.541` | `12.749` |
| `9` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `26` | `1` | `2` | `2434.113` | `22` | `8574.811` | `13.019` |
| `10` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `27` | `1` | `2` | `2434.113` | `22` | `8574.811` | `13.019` |
| `11` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `28` | `1` | `2` | `2434.113` | `22` | `8574.811` | `13.019` |
| `12` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `29` | `1` | `2` | `2434.113` | `22` | `8574.811` | `13.019` |
| `13` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `30` | `1` | `2` | `2434.113` | `22` | `8574.811` | `13.019` |
| `14` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `41` | `1` | `2` | `2432.375` | `24` | `8575.072` | `13.280` |
| `15` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `42` | `1` | `2` | `2432.375` | `24` | `8575.072` | `13.280` |
| `16` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `33` | `1` | `2` | `2433.277` | `24` | `8575.974` | `14.182` |
| `17` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `34` | `1` | `2` | `2433.277` | `24` | `8575.974` | `14.182` |
| `18` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `31` | `1` | `2` | `2434.113` | `24` | `8576.811` | `15.019` |
| `19` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `32` | `1` | `2` | `2434.113` | `24` | `8576.811` | `15.019` |
| `20` | `searched_single_book_split_literal_payload_context` | `searched_single_book_split` | `43` | `1` | `2` | `2434.271` | `24` | `8576.968` | `15.176` |

## Best Changed Model

- Delta vs current: `1.749` bits
- Model: `book_midpoint_35_literal_payload_context`
- Family: `fixed_book_midpoint`
- Split: ``
- Alpha: `1`

## Best Context-Changed Model

- Delta vs current: `1.749` bits
- Model: `book_midpoint_35_literal_payload_context`
- Family: `fixed_book_midpoint`
- Split: ``
- Alpha: `1`

## Best Alpha Change On Active Context

- Delta vs current: `17.859` bits
- Alpha: `2`

## Interpretation

No literal-payload context/shared-alpha candidate beats the active
global previous-emitted-digit payload model with shared `alpha=1`.
The active payload model remains the complete minimum after declaration
costs.

## Boundary

This is a mechanical payload-cost ledger audit only. It does not alter
row0, introduce plaintext, or make an authorial-intent claim.
