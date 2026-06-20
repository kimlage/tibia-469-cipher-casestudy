# Post-Midpoint Alpha1 Copy-Length Context Resweep

Verdict: `post_midpoint_alpha1_copy_length_context_retains_midpoint`. Translation delta: `NONE`.

This audit retests copy-length contexts after `alpha=1` became active.
The recipe, source-address ledger, copy order, payload model, item-type
model, forced rules, book-length ledger, and alpha are fixed.

## Context Models

| Rank | Model | Contexts | Length bits | Model bits | Total bits | Delta vs current | Component delta |
|---:|---|---:|---:|---:|---:|---:|---:|
| `1` | `active_book_midpoint_35_context` | `2` | `1631.494` | `12` | `8572.267` | `0.000` | `0.000` |
| `2` | `book_quartile_context` | `4` | `1631.436` | `14` | `8574.208` | `1.941` | `-0.059` |
| `3` | `searched_single_book_split_context` | `2` | `1624.790` | `21` | `8574.563` | `2.296` | `-6.704` |
| `4` | `copy_index_midpoint_context` | `2` | `1635.195` | `12` | `8575.968` | `3.701` | `3.701` |
| `5` | `same_book_context` | `2` | `1647.833` | `12` | `8588.606` | `16.339` | `16.339` |
| `6` | `book_parity_context` | `2` | `1655.104` | `12` | `8595.877` | `23.610` | `23.610` |
| `7` | `legal_symbol_count_log_context` | `7` | `1656.731` | `16` | `8601.504` | `29.237` | `25.237` |
| `8` | `book_decade_context` | `7` | `1657.083` | `16` | `8601.856` | `29.589` | `25.589` |
| `9` | `remaining_log_context` | `7` | `1665.356` | `16` | `8610.129` | `37.862` | `33.862` |
| `10` | `previous_copy_length_log_context` | `8` | `1667.089` | `16` | `8611.862` | `39.595` | `35.595` |
| `11` | `distance_log_context` | `10` | `1678.547` | `16` | `8623.320` | `51.053` | `47.053` |

## Best Searched Split

- Split book: `18`
- Total bits: `8574.563`
- Delta vs current: `2.296`
- Component delta: `-6.704`

## Interpretation

The active fixed book-midpoint context remains promoted unless another
fully declared decodable context lowers total cost under the active
`alpha=1` scorer.

## Boundary

This is a mechanical copy-length context audit only. It does not alter
row0, introduce plaintext, or make an authorial-intent claim.
