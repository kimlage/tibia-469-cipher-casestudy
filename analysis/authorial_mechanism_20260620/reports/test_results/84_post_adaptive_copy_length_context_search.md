# Post-Adaptive Copy-Length Context Search

Verdict: `controlled_post_adaptive_copy_length_midpoint_context_improvement`. Translation delta: `NONE`.

This audit retests the active adaptive bounded copy-length ledger with
simple contexts available before the copy length is decoded. The recipe,
source-address ledger, copy order, payload model, item-type model, forced
rules, and book-length ledger are fixed.

## Context Models

| Rank | Model | Contexts | Length bits | Model bits | Total bits | Delta vs current | Component delta |
|---:|---|---:|---:|---:|---:|---:|---:|
| `1` | `book_midpoint_35_context` | `2` | `1633.634` | `12` | `8574.407` | `-1.579` | `-5.579` |
| `2` | `active_global_copy_length_context` | `1` | `1639.213` | `8` | `8575.986` | `0.000` | `0.000` |
| `3` | `copy_index_midpoint_context` | `2` | `1637.376` | `12` | `8578.149` | `2.163` | `-1.837` |
| `4` | `searched_single_book_split_context` | `2` | `1630.327` | `21` | `8580.100` | `4.114` | `-8.886` |
| `5` | `book_quartile_context` | `4` | `1639.299` | `14` | `8582.072` | `6.087` | `0.087` |
| `6` | `same_book_context` | `2` | `1641.628` | `12` | `8582.401` | `6.415` | `2.415` |
| `7` | `book_parity_context` | `2` | `1653.102` | `12` | `8593.874` | `17.889` | `13.889` |
| `8` | `legal_symbol_count_log_context` | `7` | `1656.757` | `16` | `8601.530` | `25.544` | `17.544` |
| `9` | `book_decade_context` | `7` | `1661.897` | `16` | `8606.670` | `30.684` | `22.684` |
| `10` | `remaining_log_context` | `7` | `1666.632` | `16` | `8611.405` | `35.419` | `27.419` |
| `11` | `previous_copy_length_log_context` | `8` | `1671.374` | `16` | `8616.147` | `40.161` | `32.161` |
| `12` | `distance_log_context` | `10` | `1677.662` | `16` | `8622.434` | `46.449` | `38.449` |

## Best Searched Split

- Split book: `18`
- Component delta: `-8.886` bits
- Charged total delta: `4.114` bits

## Interpretation

The fixed midpoint context is decodable because book ids and book order are
already declared. It is charged one context-family bit plus a context-count
declaration. Exhaustive single-split search has a lower component cost at
some split points, but the charged split index prevents promotion.

## Boundary

This is a mechanical copy-length cost refinement only. It does not alter
row0, introduce plaintext, or make an authorial-intent claim.

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_minaddr_repair2_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_minaddr_repair2_formula_469.json)
