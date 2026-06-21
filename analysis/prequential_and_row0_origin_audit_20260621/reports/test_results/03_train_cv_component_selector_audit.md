# Train-CV Component Selector Audit

Classification: `train_cv_component_selector_does_not_rescue_family_holdouts`
Translation delta: `NONE`

## Purpose

This audit tests whether the public-bookcase family failures can be fixed
by a component selector learned from training families only. It is not a
compression sweep: component choices are derived from inner family
cross-validation and then applied to the held-out family.

## Result

| Mode | Active failures | Train-CV selector failures | Oracle failures | Active gain | Train-CV gain | Oracle gain | Train-CV changed families | Oracle changed families |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `online` | `2` | `2` | `0` | `290.311` | `290.311` | `313.383` | `0` | `13` |
| `frozen` | `3` | `3` | `0` | `273.187` | `273.187` | `296.978` | `0` | `13` |

The train-CV selector keeps all active components for every family, because
the other training families show positive aggregate gains for all three
components. It therefore does not rescue `bookcase_33`, `bookcase_8`, or
the frozen `bookcase_6` failure. The oracle selector does improve the
ledger, but only by seeing the held-out family outcome.

## Failure Rows

| Family | Mode | Active gain | Train-CV gain | Oracle gain | Train-CV selectors | Oracle selectors |
|---|---|---:|---:|---:|---|---|
| `hellgate_public_bookcase_12` | `online` | `30.233` | `30.233` | `32.863` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': True, 'item_type': False}` |
| `hellgate_public_bookcase_12` | `frozen` | `28.583` | `28.583` | `32.407` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': True, 'item_type': False}` |
| `hellgate_public_bookcase_13` | `online` | `0.832` | `0.832` | `4.087` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': False, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_13` | `frozen` | `1.274` | `1.274` | `4.267` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_20` | `online` | `7.291` | `7.291` | `7.291` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_20` | `frozen` | `7.343` | `7.343` | `7.343` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_21` | `online` | `1.678` | `1.678` | `3.332` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': False, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_21` | `frozen` | `1.708` | `1.708` | `3.316` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': False, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_23` | `online` | `3.142` | `3.142` | `5.969` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': False, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_23` | `frozen` | `3.275` | `3.275` | `5.913` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': False, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_27` | `online` | `4.118` | `4.118` | `4.118` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_27` | `frozen` | `4.144` | `4.144` | `4.144` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_3` | `online` | `11.633` | `11.633` | `11.633` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_3` | `frozen` | `11.496` | `11.496` | `11.496` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_30` | `online` | `0.568` | `0.568` | `0.869` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': False, 'literal_payload': True, 'item_type': True}` |
| `hellgate_public_bookcase_30` | `frozen` | `0.593` | `0.593` | `0.879` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': False, 'literal_payload': True, 'item_type': True}` |
| `hellgate_public_bookcase_33` | `online` | `-2.966` | `-2.966` | `3.332` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': False, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_33` | `frozen` | `-2.940` | `-2.940` | `3.316` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': False, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_36` | `online` | `9.263` | `9.263` | `11.220` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': True, 'item_type': False}` |
| `hellgate_public_bookcase_36` | `frozen` | `9.469` | `9.469` | `11.467` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': True, 'item_type': False}` |
| `hellgate_public_bookcase_40` | `online` | `9.675` | `9.675` | `9.675` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_40` | `frozen` | `9.341` | `9.341` | `9.341` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_6` | `online` | `0.161` | `0.161` | `2.808` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': True, 'item_type': False}` |
| `hellgate_public_bookcase_6` | `frozen` | `-0.395` | `-0.395` | `2.289` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': True, 'literal_payload': True, 'item_type': False}` |
| `hellgate_public_bookcase_8` | `online` | `-0.166` | `-0.166` | `1.337` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': False, 'literal_payload': False, 'item_type': True}` |
| `hellgate_public_bookcase_8` | `frozen` | `-0.167` | `-0.167` | `1.336` | `{'copy_length': True, 'literal_payload': True, 'item_type': True}` | `{'copy_length': False, 'literal_payload': False, 'item_type': True}` |

## Decision

- No train-only component fallback is promoted.
- Family failures remain evidence that the learned-component model is partial, not a final authorial generation method.
- The oracle ceiling shows the failures are locally removable only with heldout information, so using that as a formula would be posthoc.
- `row0` origin and semantics are unchanged; `translation_delta: NONE`.
