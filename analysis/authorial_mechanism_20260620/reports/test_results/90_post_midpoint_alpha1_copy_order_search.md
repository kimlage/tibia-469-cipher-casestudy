# Post-Midpoint Alpha1 Copy Order Search

Verdict: `post_midpoint_alpha1_copy_order_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit retests the within-copy coding order after midpoint-context
`alpha=1` copy-length coding became active. The recipe, payload model,
item-type model, forced rules, book-length ledger, minaddr source
address contract, and fixed midpoint context are held constant.

## Copy Order Models

| Model | Copy bits | Total bits | Delta vs current | Decodable | Length-first copies |
|---|---:|---:|---:|---:|---:|
| `best_midpoint_alpha1_copy_order_optimistic_no_mode` | `4912.746` | `8568.728` | `-3.539` | `False` | `258` |
| `source_first_then_midpoint_alpha1_length_active` | `4916.285` | `8572.267` | `-0.000` | `True` | `0` |
| `midpoint_alpha1_copy_order_sparse_run_list_length_first_required` | `4925.264` | `8581.246` | `8.979` | `True` | `2` |
| `midpoint_alpha1_length_first_then_source` | `4928.480` | `8584.461` | `12.194` | `True` | `283` |
| `midpoint_alpha1_copy_order_mode_per_copy` | `5195.746` | `8851.728` | `279.461` | `True` | `258` |

## Length-First Shape

- Copy items: `283`
- Pure length-first delta: `12.194` bits
- Optimistic no-mode savings: `3.539` bits across `258` copies
- Best sparse decodable net delta: `8.979` bits
- Best sparse length-first copies: `2`

## Best Length-First Savings

| Rank | Book | Op | Length | Source-first bits | Length-first bits | Delta |
|---:|---:|---:|---:|---:|---:|---:|
| `1` | `5` | `2` | `126` | `17.628` | `17.355` | `-0.273` |
| `2` | `9` | `0` | `204` | `18.896` | `18.675` | `-0.222` |
| `3` | `5` | `9` | `73` | `16.496` | `16.382` | `-0.115` |
| `4` | `10` | `1` | `132` | `19.074` | `18.963` | `-0.111` |
| `5` | `4` | `2` | `40` | `16.276` | `16.185` | `-0.091` |
| `6` | `35` | `1` | `276` | `20.501` | `20.427` | `-0.074` |
| `7` | `9` | `1` | `84` | `17.816` | `17.743` | `-0.073` |
| `8` | `10` | `2` | `92` | `18.424` | `18.354` | `-0.070` |
| `9` | `17` | `2` | `133` | `19.987` | `19.920` | `-0.066` |
| `10` | `8` | `0` | `53` | `17.952` | `17.895` | `-0.057` |

## Interpretation

Pure length-first coding is worse overall. Selecting the cheaper order per
copy is cheaper only when source/length order mode bits are free, so that
row is retained as an optimistic lower bound. The tested decodable mode
ledgers do not beat the active source-first order.

## Boundary

This is a mechanical copy-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
