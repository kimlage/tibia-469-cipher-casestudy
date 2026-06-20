# Post-Itemctx Parameter Resweep

Verdict: `controlled_post_itemctx_parameter_improvement`. Translation delta: `NONE`.

This audit retests declared parameters after the item-type split at
book `6` became active. The recipe, copy addresses, copy-order
contract, copy-length midpoint context, and item-type extra-context
family are fixed.

## Best By Family

| Family | Parameter | Total bits | Delta vs current | Component bits | Model bits |
|---|---|---:|---:|---:|---:|
| `item_type_extra_context_order_alpha` | `{'order': 1, 'alpha': 2}` | `8561.792` | `-7.860` | `223.412` | `14` |
| `literal_payload_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8569.652` | `0.000` | `2434.095` | `9` |
| `literal_run_length_rice_k` | `3` | `8569.652` | `0.000` | `368.000` | `5` |
| `midpoint_adaptive_copy_length_alpha` | `1` | `8569.652` | `0.000` | `1631.494` | `12` |

## Top Candidates

| Rank | Family | Parameter | Total bits | Delta vs current |
|---:|---|---|---:|---:|
| `1` | `item_type_extra_context_order_alpha` | `{'order': 1, 'alpha': 2}` | `8561.792` | `-7.860` |
| `2` | `item_type_extra_context_order_alpha` | `{'order': 1, 'alpha': 1}` | `8562.207` | `-7.445` |
| `3` | `item_type_extra_context_order_alpha` | `{'order': 1, 'alpha': 3}` | `8564.259` | `-5.393` |
| `4` | `item_type_extra_context_order_alpha` | `{'order': 1, 'alpha': 4}` | `8564.994` | `-4.658` |
| `5` | `item_type_extra_context_order_alpha` | `{'order': 1, 'alpha': 5}` | `8565.831` | `-3.821` |
| `6` | `item_type_extra_context_order_alpha` | `{'order': 1, 'alpha': 6}` | `8566.706` | `-2.946` |
| `7` | `item_type_extra_context_order_alpha` | `{'order': 2, 'alpha': 2}` | `8568.002` | `-1.650` |
| `8` | `item_type_extra_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8568.014` | `-1.638` |
| `9` | `item_type_extra_context_order_alpha` | `{'order': 1, 'alpha': 7}` | `8569.589` | `-0.063` |
| `10` | `literal_run_length_rice_k` | `3` | `8569.652` | `0.000` |
| `11` | `literal_payload_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8569.652` | `0.000` |
| `12` | `item_type_extra_context_order_alpha` | `{'order': 3, 'alpha': 2}` | `8569.652` | `0.000` |
| `13` | `midpoint_adaptive_copy_length_alpha` | `1` | `8569.652` | `0.000` |
| `14` | `item_type_extra_context_order_alpha` | `{'order': 3, 'alpha': 1}` | `8569.660` | `0.008` |
| `15` | `item_type_extra_context_order_alpha` | `{'order': 1, 'alpha': 8}` | `8570.465` | `0.813` |
| `16` | `item_type_extra_context_order_alpha` | `{'order': 2, 'alpha': 3}` | `8571.178` | `1.526` |
| `17` | `item_type_extra_context_order_alpha` | `{'order': 1, 'alpha': 9}` | `8571.327` | `1.675` |
| `18` | `midpoint_adaptive_copy_length_alpha` | `2` | `8571.792` | `2.140` |
| `19` | `item_type_extra_context_order_alpha` | `{'order': 1, 'alpha': 10}` | `8572.170` | `2.518` |
| `20` | `item_type_extra_context_order_alpha` | `{'order': 2, 'alpha': 4}` | `8572.628` | `2.976` |

## Interpretation

No parameter is promoted unless the fully rescored total falls below the
active itemctx formula. This is a mechanical parameter audit only; it
does not introduce plaintext, row0 meaning, or authorial intent.

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_formula_469.json)
