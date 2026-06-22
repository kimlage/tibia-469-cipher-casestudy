# Book Residual Mode Coupling Gate

Classification: `PROMOTED_BOOK_RESIDUAL_MODE_COUPLING`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether the remaining external fields form a compact book-level residual mode rather than independent tapes.

## Summary

- Books: `60`.
- Fields: `op_count_class, literal_digit_class, literal_op_class, copy_hint_bits_class, composition_bits_class`.
- Independent field bits: `2055.480`.
- Joint-mode bits: `938.211`.
- Saving: `1117.269` bits.
- Positive splits: `20/20`.
- Exact joint hits: `108/186` repeated test-book evaluations.
- Shuffled p95: `755.429`.
- Beats shuffled p95: `True`.
- Promoted variants: `['all_fields', 'no_derived_shape', 'external_burden_only']`.

## Variant Summary

| Variant | Fields | Saving | Shuffled p95 | Beats p95 | Positive splits |
| --- | --- | ---: | ---: | --- | ---: |
| `all_fields` | `6` | `1388.895` | `1102.876` | `True` | `20/20` |
| `no_derived_shape` | `5` | `1117.269` | `755.429` | `True` | `20/20` |
| `external_burden_only` | `3` | `357.235` | `132.102` | `True` | `19/20` |

## Primary Split Results

| Split | Type | Test books | Saving | Joint bits | Independent bits | Exact hits |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `prefix_20` | `prefix` | `50` | `389.337` | `254.692` | `644.029` | `16` |
| `prefix_30` | `prefix` | `40` | `246.728` | `196.276` | `443.004` | `23` |
| `prefix_40` | `prefix` | `30` | `168.849` | `143.604` | `312.453` | `20` |
| `prefix_50` | `prefix` | `20` | `104.934` | `98.404` | `203.339` | `13` |
| `prefix_60` | `prefix` | `10` | `50.823` | `44.752` | `95.575` | `9` |
| `family_hellgate_public_bookcase_1` | `family` | `2` | `15.738` | `16.642` | `32.380` | `0` |
| `family_hellgate_public_bookcase_13` | `family` | `3` | `12.610` | `18.249` | `30.858` | `2` |
| `family_hellgate_public_bookcase_2` | `family` | `2` | `15.345` | `16.642` | `31.987` | `0` |
| `family_hellgate_public_bookcase_20` | `family` | `2` | `5.513` | `12.735` | `18.248` | `1` |
| `family_hellgate_public_bookcase_21` | `family` | `3` | `13.508` | `12.252` | `25.760` | `3` |
| `family_hellgate_public_bookcase_23` | `family` | `2` | `2.941` | `12.735` | `15.676` | `1` |
| `family_hellgate_public_bookcase_27` | `family` | `2` | `7.661` | `8.647` | `16.308` | `2` |
| `family_hellgate_public_bookcase_3` | `family` | `2` | `6.412` | `9.927` | `16.339` | `2` |
| `family_hellgate_public_bookcase_30` | `family` | `2` | `9.052` | `9.747` | `18.799` | `2` |
| `family_hellgate_public_bookcase_33` | `family` | `2` | `6.754` | `8.828` | `15.582` | `2` |
| `family_hellgate_public_bookcase_4` | `family` | `3` | `13.772` | `15.927` | `29.699` | `3` |
| `family_hellgate_public_bookcase_40` | `family` | `4` | `19.408` | `18.159` | `37.568` | `4` |
| `family_hellgate_public_bookcase_6` | `family` | `2` | `8.245` | `13.834` | `22.080` | `1` |
| `family_hellgate_public_bookcase_7` | `family` | `3` | `12.193` | `15.927` | `28.120` | `2` |
| `family_hellgate_public_bookcase_8` | `family` | `2` | `7.446` | `10.232` | `17.678` | `2` |

## Decision

Promotion requires joint-mode coding to reduce the external ledger and beat shuffled-within-stream controls. This gate promotes a book-level residual coupling clue when the primary no-derived-shape variant passes; it still does not generate exact operation streams, literal payload, or copy hints.
