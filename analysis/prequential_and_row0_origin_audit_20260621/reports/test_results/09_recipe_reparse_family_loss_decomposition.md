# Recipe Reparse Family Loss Decomposition

Classification: `family_reparse_losses_are_local_component_overheads`
Translation delta: `NONE`

## Purpose

Audit 08 found five public-bookcase families where deterministic reparse
beats raw digits but does not beat the active full-corpus recipe. This
audit decomposes those five local losses by charged component.

## Summary

- Loss families: `5`.
- All roundtrip: `True`.
- Component-failure loss families: `2`.
- Mean reparse minus active: `4.232` bits.
- Worst family: `hellgate_public_bookcase_33` at `8.986` bits.
- Largest-loss component counts: `{'copy_address_bits': 4, 'no_positive_component': 1}`.

## Loss Rows

| Family | Books | Reparse - active | Largest loss | Largest gain | Component failure | Raw gain |
|---|---|---:|---|---|---|---:|
| `hellgate_public_bookcase_13` | `[40, 41, 42]` | `8.534` | `copy_address_bits` | `copy_length_stream_bits` | `False` | `1359.567` |
| `hellgate_public_bookcase_21` | `[62, 63, 64]` | `0.515` | `copy_address_bits` | `None` | `False` | `1234.859` |
| `hellgate_public_bookcase_33` | `[18, 19]` | `8.986` | `copy_address_bits` | `None` | `True` | `631.797` |
| `hellgate_public_bookcase_7` | `[54, 55, 56]` | `3.124` | `copy_address_bits` | `copy_length_stream_bits` | `False` | `1158.863` |
| `hellgate_public_bookcase_8` | `[68, 69]` | `0.000` | `None` | `None` | `True` | `896.869` |

## Component Delta Bits

Values are deterministic reparse minus active full-corpus recipe. Positive values are local losses.

| Family | Literal length | Literal payload | Item type | Copy address | Copy length | Inventory delta |
|---|---:|---:|---:|---:|---:|---|
| `hellgate_public_bookcase_13` | `0.000` | `0.000` | `0.000` | `9.271` | `-0.737` | `{'literal_runs': 0, 'literal_digits': 0, 'copy_items': 0, 'copied_digits': 0}` |
| `hellgate_public_bookcase_21` | `0.000` | `0.000` | `0.000` | `0.515` | `0.000` | `{'literal_runs': 0, 'literal_digits': 0, 'copy_items': 0, 'copied_digits': 0}` |
| `hellgate_public_bookcase_33` | `0.000` | `0.000` | `0.000` | `8.986` | `-0.000` | `{'literal_runs': 0, 'literal_digits': 0, 'copy_items': 0, 'copied_digits': 0}` |
| `hellgate_public_bookcase_7` | `0.000` | `-0.000` | `0.000` | `4.565` | `-1.441` | `{'literal_runs': 0, 'literal_digits': 0, 'copy_items': 0, 'copied_digits': 0}` |
| `hellgate_public_bookcase_8` | `0.000` | `0.000` | `0.000` | `0.000` | `0.000` | `{'literal_runs': 0, 'literal_digits': 0, 'copy_items': 0, 'copied_digits': 0}` |

## Decision

- These are local active-recipe wins, not raw predictive failures.
- The five families still roundtrip and still beat raw digit coding.
- The generation explanation remains partial because the active full-corpus recipe can still be locally cheaper.
- No plaintext, translation, row0-origin change, or case reopening is introduced.
