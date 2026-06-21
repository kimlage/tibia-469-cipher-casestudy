# 138. Literal Payload Default Decodability Audit

Classification: `literal_payload_default_exception_not_promoted`
Translation delta: `NONE`

## Purpose

The active formula still pays a large literal-payload stream. This audit
tests a small, decodable alternative family: predict a modal digit from
prior emitted-digit context, then encode only default/exception plus an
adaptive exception digit. It also rechecks categorical context orders `0`,
`1`, and `2` under the same alpha.

## Result

- Active total bits: `8177.317`
- Active literal-payload bits: `2613.661`
- Literal digits: `857`
- Best candidate family: `adaptive_categorical_previous_digit_context`
- Best candidate bits: `2613.661`
- Delta vs active literal payload: `0.000` bits

## Top Candidates

| Rank | Family | Parameters | Bits | Delta vs active |
|---:|---|---|---:|---:|
| `1` | `adaptive_categorical_previous_digit_context` | order=2 | `2613.661` | `0.000` |
| `2` | `adaptive_modal_default_with_exception_digit` | default_order=2; exception_order=2; flag_context=global; default_count=240 | `2651.710` | `38.049` |
| `3` | `adaptive_modal_default_with_exception_digit` | default_order=0; exception_order=2; flag_context=global; default_count=118 | `2654.163` | `40.502` |
| `4` | `adaptive_modal_default_with_exception_digit` | default_order=0; exception_order=2; flag_context=same_context; default_count=118 | `2654.163` | `40.502` |
| `5` | `adaptive_modal_default_with_exception_digit` | default_order=2; exception_order=1; flag_context=global; default_count=240 | `2660.473` | `46.812` |
| `6` | `adaptive_modal_default_with_exception_digit` | default_order=1; exception_order=2; flag_context=global; default_count=153 | `2665.456` | `51.795` |
| `7` | `adaptive_modal_default_with_exception_digit` | default_order=1; exception_order=2; flag_context=same_context; default_count=153 | `2672.302` | `58.642` |
| `8` | `adaptive_modal_default_with_exception_digit` | default_order=2; exception_order=2; flag_context=same_context; default_count=240 | `2699.060` | `85.399` |

## Decision

- No literal-payload default/exception model is promoted.
- The active categorical previous-emitted-digit context order `2` remains best among this bounded family.
- This is a falsification of a natural default/exception route, not a translation or row0 claim.
