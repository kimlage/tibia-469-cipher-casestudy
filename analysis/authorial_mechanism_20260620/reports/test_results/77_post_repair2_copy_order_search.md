# Post-Repair2 Copy Order Search

Verdict: `post_repair2_copy_order_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit retests the within-copy coding order after the active
post-repair2 formula. The recipe, payload model, item-type model, forced
rules, and book-length ledger are fixed. It compares the active
source-address-then-length order against length-then-source alternatives.

## Copy Order Models

| Model | Copy bits | Total bits | Delta vs current | Decodable | Length-first copies |
|---|---:|---:|---:|---:|---:|
| `best_copy_order_optimistic_no_mode` | `4957.252` | `8606.234` | `-3.539` | `False` | `258` |
| `source_first_then_length_active` | `4960.791` | `8609.773` | `-0.000` | `True` | `0` |
| `copy_order_sparse_run_list_length_first_required` | `4969.770` | `8618.752` | `8.979` | `True` | `2` |
| `length_first_then_source` | `4979.087` | `8628.068` | `18.295` | `True` | `283` |
| `copy_order_mode_per_copy` | `5240.252` | `8889.234` | `279.461` | `True` | `258` |

## Length-First Shape

- Copy items: `283`
- Pure length-first delta: `18.295` bits
- Optimistic no-mode savings: `3.539` bits across `258` copies
- Best sparse decodable net delta: `8.979` bits
- Best sparse length-first copies: `2`

## Best Length-First Savings

| Rank | Book | Op | Length | Source-first bits | Length-first bits | Delta |
|---:|---:|---:|---:|---:|---:|---:|
| `1` | `5` | `2` | `126` | `17.453` | `17.180` | `-0.273` |
| `2` | `9` | `0` | `204` | `18.449` | `18.228` | `-0.222` |
| `3` | `5` | `9` | `73` | `16.796` | `16.681` | `-0.115` |
| `4` | `10` | `1` | `132` | `18.739` | `18.628` | `-0.111` |
| `5` | `4` | `2` | `40` | `16.157` | `16.066` | `-0.091` |
| `6` | `35` | `1` | `276` | `21.408` | `21.334` | `-0.074` |
| `7` | `9` | `1` | `84` | `17.646` | `17.573` | `-0.073` |
| `8` | `10` | `2` | `92` | `17.846` | `17.776` | `-0.070` |
| `9` | `17` | `2` | `133` | `19.479` | `19.413` | `-0.066` |
| `10` | `8` | `0` | `53` | `17.280` | `17.223` | `-0.057` |

## Interpretation

Pure length-first coding is worse overall. Selecting the cheaper order per
copy would be cheaper only if mode bits were free, so it is an optimistic
lower bound. The tested decodable mode ledgers do not beat the active
source-first order.

## Boundary

This is a mechanical copy-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
