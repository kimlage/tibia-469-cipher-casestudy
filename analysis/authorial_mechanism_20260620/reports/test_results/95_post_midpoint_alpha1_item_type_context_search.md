# Post-Midpoint Alpha1 Item-Type Context Search

Verdict: `controlled_post_midpoint_item_type_context_improvement`. Translation delta: `NONE`.

This audit retests whether the adaptive literal/copy item-type model
should be split by a simple context after the midpoint alpha=1 formula
became active. The recipe, literal models, copy-address ledger,
copy-length model, forced rules, and book-length ledger are fixed.

## Item-Type Context Models

| Rank | Model | Contexts | Item bits | Model bits | Total bits | Delta vs current | Component delta | Decodable |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `1` | `item_length_log_context` | `9` | `217.959` | `17` | `8559.339` | `-12.928` | `-20.928` | `False` |
| `2` | `searched_single_book_split_item_type_context` | `2` | `227.272` | `18` | `8569.652` | `-2.615` | `-11.615` | `True` |
| `3` | `active_global_item_type_context` | `1` | `238.887` | `9` | `8572.267` | `0.000` | `0.000` | `True` |
| `4` | `book_midpoint_35_item_type_context` | `2` | `239.886` | `13` | `8577.266` | `4.999` | `0.999` | `True` |
| `5` | `op_index_log_item_type_context` | `5` | `241.133` | `15` | `8580.513` | `8.246` | `2.246` | `True` |
| `6` | `book_quartile_item_type_context` | `4` | `244.221` | `15` | `8583.601` | `11.334` | `5.334` | `True` |
| `7` | `book_parity_item_type_context` | `2` | `246.884` | `13` | `8584.265` | `11.997` | `7.997` | `True` |
| `8` | `book_decade_item_type_context` | `7` | `246.724` | `17` | `8588.104` | `15.837` | `7.837` | `True` |
| `9` | `remaining_log_item_type_context` | `7` | `250.572` | `17` | `8591.952` | `19.685` | `11.685` | `True` |

## Best Searched Split

- Split book: `6`
- Total bits: `8569.652`
- Delta vs current: `-2.615`
- Component delta: `-11.615`
- Declaration delta: `9`

## Interpretation

An item-type context is promoted only if its component savings survive
the extra declaration cost and the forced literal/copy rules remain
valid. Otherwise the active global previous-item model remains the
current formula.

## Boundary

This is a mechanical item-type-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_minaddr_repair2_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_minaddr_repair2_formula_469.json)
