# Post-Adaptive Copy Order Search

Verdict: `post_adaptive_copy_order_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit retests the within-copy coding order after adaptive bounded
copy-length coding became active. The recipe, payload model, item-type
model, forced rules, book-length ledger, and minaddr source address
contract are fixed.

## Copy Order Models

| Model | Copy bits | Total bits | Delta vs current | Decodable | Length-first copies |
|---|---:|---:|---:|---:|---:|
| `best_adaptive_copy_order_optimistic_no_mode` | `4920.465` | `8572.447` | `-3.539` | `False` | `258` |
| `source_first_then_adaptive_length_active` | `4924.004` | `8575.986` | `-0.000` | `True` | `0` |
| `adaptive_copy_order_sparse_run_list_length_first_required` | `4932.983` | `8584.965` | `8.979` | `True` | `2` |
| `adaptive_length_first_then_source` | `4937.668` | `8589.650` | `13.664` | `True` | `283` |
| `adaptive_copy_order_mode_per_copy` | `5203.465` | `8855.447` | `279.461` | `True` | `258` |

## Length-First Shape

- Copy items: `283`
- Pure length-first delta: `13.664` bits
- Optimistic no-mode savings: `3.539` bits across `258` copies
- Best sparse decodable net delta: `8.979` bits
- Best sparse length-first copies: `2`

## Best Length-First Savings

| Rank | Book | Op | Length | Source-first bits | Length-first bits | Delta |
|---:|---:|---:|---:|---:|---:|---:|
| `1` | `5` | `2` | `126` | `17.546` | `17.273` | `-0.273` |
| `2` | `9` | `0` | `204` | `18.769` | `18.547` | `-0.222` |
| `3` | `5` | `9` | `73` | `16.231` | `16.116` | `-0.115` |
| `4` | `10` | `1` | `132` | `18.926` | `18.815` | `-0.111` |
| `5` | `4` | `2` | `40` | `16.140` | `16.049` | `-0.091` |
| `6` | `35` | `1` | `276` | `20.914` | `20.840` | `-0.074` |
| `7` | `9` | `1` | `84` | `17.491` | `17.418` | `-0.073` |
| `8` | `10` | `2` | `92` | `18.164` | `18.094` | `-0.070` |
| `9` | `17` | `2` | `133` | `19.750` | `19.684` | `-0.066` |
| `10` | `8` | `0` | `53` | `17.751` | `17.694` | `-0.057` |

## Interpretation

Pure length-first coding is worse overall. Selecting the cheaper order per
copy would be cheaper only if mode bits were free, so it is an optimistic
lower bound. The tested decodable mode ledgers do not beat the active
source-first order.

## Boundary

This is a mechanical copy-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
