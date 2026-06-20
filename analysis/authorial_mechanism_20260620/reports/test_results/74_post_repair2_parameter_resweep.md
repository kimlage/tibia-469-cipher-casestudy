# Post-Repair2 Parameter Resweep

Verdict: `post_repair2_parameter_resweep_retains_current`. Translation delta: `NONE`.

This audit retests declared parameters after the two minaddr local repairs
changed the recipe. The recipe, copy lengths, and copy addresses are fixed;
the sweep covers literal-run Rice `k`, literal-payload context order/alpha,
and item-type context order/alpha.

## Best By Family

| Family | Parameter | Total bits | Delta vs current | Component bits | Model bits |
|---|---|---:|---:|---:|---:|
| `item_type_context_order_alpha` | `{'order': 3, 'alpha': 2}` | `8609.773` | `0.000` | `238.887` | `9` |
| `literal_payload_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8609.773` | `0.000` | `2434.095` | `9` |
| `literal_run_length_rice_k` | `3` | `8609.773` | `0.000` | `368.000` | `5` |

## Top Candidates

| Rank | Family | Parameter | Total bits | Delta vs current |
|---:|---|---|---:|---:|
| `1` | `literal_run_length_rice_k` | `3` | `8609.773` | `0.000` |
| `2` | `literal_payload_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8609.773` | `0.000` |
| `3` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 2}` | `8609.773` | `0.000` |
| `4` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 1}` | `8610.557` | `0.785` |
| `5` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 3}` | `8612.477` | `2.704` |
| `6` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 2}` | `8612.525` | `2.752` |
| `7` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 1}` | `8612.795` | `3.022` |
| `8` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 4}` | `8613.591` | `3.818` |
| `9` | `item_type_context_order_alpha` | `{'order': 2, 'alpha': 2}` | `8613.799` | `4.026` |
| `10` | `item_type_context_order_alpha` | `{'order': 2, 'alpha': 1}` | `8614.220` | `4.447` |
| `11` | `item_type_context_order_alpha` | `{'order': 4, 'alpha': 2}` | `8614.619` | `4.846` |
| `12` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 3}` | `8614.736` | `4.963` |
| `13` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 5}` | `8614.831` | `5.059` |
| `14` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 4}` | `8615.105` | `5.332` |
| `15` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 5}` | `8615.542` | `5.769` |
| `16` | `item_type_context_order_alpha` | `{'order': 1, 'alpha': 6}` | `8616.009` | `6.236` |
| `17` | `item_type_context_order_alpha` | `{'order': 3, 'alpha': 6}` | `8616.096` | `6.323` |
| `18` | `item_type_context_order_alpha` | `{'order': 2, 'alpha': 3}` | `8616.283` | `6.510` |
| `19` | `item_type_context_order_alpha` | `{'order': 4, 'alpha': 1}` | `8616.489` | `6.716` |
| `20` | `item_type_context_order_alpha` | `{'order': 5, 'alpha': 2}` | `8616.647` | `6.874` |

## Interpretation

No parameter is promoted unless the fully rescored total falls below the
active formula. This is a mechanical parameter audit only; it does not
introduce plaintext, row0 meaning, or authorial intent.
