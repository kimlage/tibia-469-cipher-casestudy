# Post-Midpoint Parameter Resweep

Verdict: `controlled_post_midpoint_copy_length_alpha_improvement`. Translation delta: `NONE`.

This audit retests declared parameters after the fixed book-midpoint
copy-length context became active. The recipe, copy addresses, copy-order
contract, and midpoint context family are fixed; the sweep covers
literal-run Rice `k`, literal-payload context order/alpha, item-type
context order/alpha, and midpoint adaptive copy-length alpha.

## Best By Family

| Family | Parameter | Total bits | Delta vs current | Component bits | Model bits |
|---|---|---:|---:|---:|---:|
| `item_type_context_order_alpha` | `{'order': 3, 'alpha': 2}` | `8574.407` | `0.000` | `238.887` | `9` |
| `literal_payload_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8574.407` | `0.000` | `2434.095` | `9` |
| `literal_run_length_rice_k` | `3` | `8574.407` | `0.000` | `368.000` | `5` |
| `midpoint_adaptive_copy_length_alpha` | `1` | `8572.267` | `-2.140` | `1631.494` | `12` |

## Top Candidates

| Rank | Family | Parameter | Total bits | Delta vs current |
|---:|---|---|---:|---:|
| `1` | `midpoint_adaptive_copy_length_alpha` | `1` | `8572.267` | `-2.140` |
| `2` | `literal_run_length_rice_k` | `3` | `8574.407` | `0.000` |
| `3` | `literal_payload_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8574.407` | `0.000` |
| `4` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 2}` | `8574.407` | `0.000` |
| `5` | `midpoint_adaptive_copy_length_alpha` | `2` | `8574.407` | `0.000` |
| `6` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 1}` | `8575.192` | `0.785` |
| `7` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 3}` | `8577.111` | `2.704` |
| `8` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 2}` | `8577.159` | `2.752` |
| `9` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 1}` | `8577.429` | `3.022` |
| `10` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 4}` | `8578.225` | `3.818` |
| `11` | `item_type_context_order_alpha` | `{'order': 2, 'alpha': 2}` | `8578.433` | `4.026` |
| `12` | `item_type_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8578.854` | `4.447` |
| `13` | `item_type_context_order_alpha` | `{'order': 4, 'alpha': 2}` | `8579.253` | `4.846` |
| `14` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 3}` | `8579.370` | `4.963` |
| `15` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 5}` | `8579.466` | `5.059` |
| `16` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 4}` | `8579.739` | `5.332` |
| `17` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 5}` | `8580.176` | `5.769` |
| `18` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 6}` | `8580.643` | `6.236` |
| `19` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 6}` | `8580.730` | `6.323` |
| `20` | `item_type_context_order_alpha` | `{'order': 2, 'alpha': 3}` | `8580.917` | `6.510` |

## Interpretation

No parameter is promoted unless the fully rescored total falls below the
active midpoint formula. This is a mechanical parameter audit only; it
does not introduce plaintext, row0 meaning, or authorial intent.

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_formula_469.json)
