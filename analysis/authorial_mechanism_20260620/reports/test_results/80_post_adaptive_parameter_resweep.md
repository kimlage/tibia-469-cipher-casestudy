# Post-Adaptive Parameter Resweep

Verdict: `post_adaptive_parameter_resweep_retains_current`. Translation delta: `NONE`.

This audit retests declared parameters after adaptive bounded copy-length
coding became active. The recipe, copy addresses, and copy-order contract
are fixed; the sweep covers literal-run Rice `k`, literal-payload
context order/alpha, item-type context order/alpha, and adaptive
copy-length alpha.

## Best By Family

| Family | Parameter | Total bits | Delta vs current | Component bits | Model bits |
|---|---|---:|---:|---:|---:|
| `adaptive_copy_length_alpha` | `2` | `8575.986` | `0.000` | `1639.213` | `8` |
| `item_type_context_order_alpha` | `{'order': 3, 'alpha': 2}` | `8575.986` | `0.000` | `238.887` | `9` |
| `literal_payload_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8575.986` | `0.000` | `2434.095` | `9` |
| `literal_run_length_rice_k` | `3` | `8575.986` | `0.000` | `368.000` | `5` |

## Top Candidates

| Rank | Family | Parameter | Total bits | Delta vs current |
|---:|---|---|---:|---:|
| `1` | `literal_run_length_rice_k` | `3` | `8575.986` | `0.000` |
| `2` | `literal_payload_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8575.986` | `0.000` |
| `3` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 2}` | `8575.986` | `0.000` |
| `4` | `adaptive_copy_length_alpha` | `2` | `8575.986` | `0.000` |
| `5` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 1}` | `8576.770` | `0.785` |
| `6` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 3}` | `8578.690` | `2.704` |
| `7` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 2}` | `8578.738` | `2.752` |
| `8` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 1}` | `8579.008` | `3.022` |
| `9` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 4}` | `8579.804` | `3.818` |
| `10` | `item_type_context_order_alpha` | `{'order': 2, 'alpha': 2}` | `8580.012` | `4.026` |
| `11` | `adaptive_copy_length_alpha` | `3` | `8580.112` | `4.126` |
| `12` | `item_type_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8580.433` | `4.447` |
| `13` | `item_type_context_order_alpha` | `{'order': 4, 'alpha': 2}` | `8580.832` | `4.846` |
| `14` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 3}` | `8580.949` | `4.963` |
| `15` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 5}` | `8581.044` | `5.059` |
| `16` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 4}` | `8581.318` | `5.332` |
| `17` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 5}` | `8581.755` | `5.769` |
| `18` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 6}` | `8582.222` | `6.236` |
| `19` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 6}` | `8582.309` | `6.323` |
| `20` | `item_type_context_order_alpha` | `{'order': 2, 'alpha': 3}` | `8582.496` | `6.510` |

## Interpretation

No parameter is promoted unless the fully rescored total falls below the
active adaptive formula. This is a mechanical parameter audit only; it
does not introduce plaintext, row0 meaning, or authorial intent.
