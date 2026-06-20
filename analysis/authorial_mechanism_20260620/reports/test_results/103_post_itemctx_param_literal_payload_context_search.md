# Post-Itemctx Param Literal Payload Context Search

Verdict: `post_itemctx_param_literal_payload_context_not_promoted`. Translation delta: `NONE`.

This audit retests whether the adaptive literal payload model should be
split by a simple context after the itemctx_param promotion. The recipe,
literal-run length model, copy-address ledger, copy-length model,
item-type model, forced rules, and book-length ledger are fixed.

## Payload Context Models

| Rank | Model | Contexts | Payload bits | Model bits | Total bits | Delta vs current | Component delta |
|---:|---|---:|---:|---:|---:|---:|---:|
| `1` | `active_global_literal_payload_context` | `1` | `2434.095` | `9` | `8561.792` | `0.000` | `0.000` |
| `2` | `book_midpoint_35_literal_payload_context` | `2` | `2431.844` | `13` | `8563.541` | `1.749` | `-2.251` |
| `3` | `searched_single_book_split_literal_payload_context` | `2` | `2430.708` | `24` | `8573.405` | `11.613` | `-3.387` |
| `4` | `book_quartile_literal_payload_context` | `4` | `2444.670` | `15` | `8578.367` | `16.575` | `10.575` |
| `5` | `book_parity_literal_payload_context` | `2` | `2471.916` | `13` | `8603.614` | `41.822` | `37.822` |
| `6` | `book_decade_literal_payload_context` | `7` | `2489.186` | `17` | `8624.883` | `63.091` | `55.091` |
| `7` | `literal_offset_log_context` | `7` | `2525.500` | `17` | `8661.197` | `99.405` | `91.405` |
| `8` | `literal_run_length_log_context` | `7` | `2531.840` | `17` | `8667.537` | `105.745` | `97.745` |
| `9` | `copy_index_proxy_global_position_context` | `14` | `2542.436` | `17` | `8678.133` | `116.341` | `108.341` |

## Best Searched Split

- Split book: `39`
- Total bits: `8573.405`
- Delta vs current: `11.613`
- Component delta: `-3.387`
- Declaration delta: `15`

## Interpretation

A literal-payload context is promoted only if its component savings
survive the extra declaration cost. Otherwise the active global
previous-emitted-digit payload model remains the current formula.

## Boundary

This is a mechanical payload-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
