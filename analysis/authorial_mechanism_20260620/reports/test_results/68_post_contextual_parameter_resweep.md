# Post-Contextual Parameter Resweep

Verdict: `post_contextual_parameter_resweep_retains_current`. Translation delta: `NONE`.

This audit retests declared parameters after the contextual copy-to-literal
repair changed the recipe. It keeps the recipe fixed and sweeps copy
length Rice `k`, literal-run length Rice `k`, literal-payload context
order/alpha, and item-type context order/alpha.

## Best By Family

| Family | Parameter | Total bits | Delta vs current | Component bits | Model bits |
|---|---|---:|---:|---:|---:|
| `copy_length_rice_k` | `4` | `8803.1` | `0.0` | `1860.0` | `5` |
| `item_type_context_order_alpha` | `{'order': 3, 'alpha': 2}` | `8803.1` | `0.0` | `239.2` | `9` |
| `literal_payload_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8803.1` | `0.0` | `2461.1` | `9` |
| `literal_run_length_rice_k` | `3` | `8803.1` | `0.0` | `370.0` | `5` |

## Top Candidates

| Rank | Family | Parameter | Total bits | Delta vs current |
|---:|---|---|---:|---:|
| `1` | `copy_length_rice_k` | `4` | `8803.1` | `0.0` |
| `2` | `literal_run_length_rice_k` | `3` | `8803.1` | `0.0` |
| `3` | `literal_payload_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8803.1` | `0.0` |
| `4` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 2}` | `8803.1` | `0.0` |
| `5` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 1}` | `8804.0` | `0.9` |
| `6` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 2}` | `8804.5` | `1.4` |
| `7` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 1}` | `8804.8` | `1.7` |
| `8` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 3}` | `8805.7` | `2.6` |
| `9` | `item_type_context_order_alpha` | `{'order': 2, 'alpha': 2}` | `8806.4` | `3.3` |
| `10` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 3}` | `8806.7` | `3.6` |
| `11` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 4}` | `8806.8` | `3.6` |
| `12` | `item_type_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8806.9` | `3.8` |
| `13` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 4}` | `8807.1` | `4.0` |
| `14` | `item_type_context_order_alpha` | `{'order': 4, 'alpha': 2}` | `8807.3` | `4.2` |
| `15` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 5}` | `8807.5` | `4.4` |
| `16` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 5}` | `8807.9` | `4.8` |
| `17` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 6}` | `8808.0` | `4.9` |
| `18` | `item_type_context_order_alpha` | `{'order': 2, 'alpha': 3}` | `8808.9` | `5.8` |
| `19` | `item_type_context_order_alpha` | `{'order': 5, 'alpha': 2}` | `8809.1` | `5.9` |
| `20` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 6}` | `8809.1` | `6.0` |

## Interpretation

The current parameters remain active if every family minimum is at or
above the current formula cost. This is a mechanical parameter audit
only; it does not introduce plaintext, row0 meaning, or authorial
intent.
