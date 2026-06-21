# Family Holdout No-Test-Carryover Audit

Classification: `family_holdout_no_test_carryover_predictive`
Translation delta: `NONE`

## Purpose

Family reparse holdouts normally emit the held-out family sequentially.
This audit removes cross-book carryover inside the held-out family:
each held-out book starts from the training-complement inventory only.

## Summary

- Families checked: `19`.
- Roundtrip families: `19/19`.
- No-test-carryover beats raw: `19/19`.
- Standard family reparse beats raw: `19/19`.
- Mean no-test-carryover gain vs raw: `1054.570` bits.
- Mean standard gain vs raw: `1064.819` bits.
- Mean no-carryover minus standard: `10.249` bits.
- Failure labels: `[]`.

## Rows

| Family | Books | No-carry gain vs raw | Standard gain vs raw | No-carry - standard | Beats raw |
|---|---|---:|---:|---:|---|
| `hellgate_public_bookcase_1` | `[12, 14]` | `746.534` | `745.600` | `-0.934` | `True` |
| `hellgate_public_bookcase_10` | `[0, 1, 2]` | `1284.943` | `1284.862` | `-0.081` | `True` |
| `hellgate_public_bookcase_12` | `[3, 4]` | `705.755` | `705.610` | `-0.145` | `True` |
| `hellgate_public_bookcase_13` | `[40, 41, 42]` | `1359.856` | `1359.567` | `-0.288` | `True` |
| `hellgate_public_bookcase_2` | `[15, 16]` | `767.271` | `843.449` | `76.178` | `True` |
| `hellgate_public_bookcase_20` | `[44, 45]` | `854.442` | `854.409` | `-0.033` | `True` |
| `hellgate_public_bookcase_21` | `[62, 63, 64]` | `1234.958` | `1234.859` | `-0.099` | `True` |
| `hellgate_public_bookcase_22` | `[5, 6, 7]` | `1230.952` | `1348.016` | `117.063` | `True` |
| `hellgate_public_bookcase_23` | `[28, 29]` | `923.697` | `923.659` | `-0.038` | `True` |
| `hellgate_public_bookcase_27` | `[46, 47]` | `1216.391` | `1216.358` | `-0.033` | `True` |
| `hellgate_public_bookcase_3` | `[20, 21]` | `713.647` | `713.630` | `-0.016` | `True` |
| `hellgate_public_bookcase_30` | `[32, 33]` | `857.209` | `857.191` | `-0.018` | `True` |
| `hellgate_public_bookcase_33` | `[18, 19]` | `631.833` | `631.797` | `-0.036` | `True` |
| `hellgate_public_bookcase_36` | `[8, 9]` | `1419.960` | `1419.920` | `-0.041` | `True` |
| `hellgate_public_bookcase_4` | `[24, 25, 26]` | `918.657` | `918.560` | `-0.096` | `True` |
| `hellgate_public_bookcase_40` | `[50, 51, 52, 53]` | `2592.655` | `2595.114` | `2.459` | `True` |
| `hellgate_public_bookcase_6` | `[38, 39]` | `522.093` | `523.227` | `1.134` | `True` |
| `hellgate_public_bookcase_7` | `[54, 55, 56]` | `1159.089` | `1158.863` | `-0.226` | `True` |
| `hellgate_public_bookcase_8` | `[68, 69]` | `896.888` | `896.869` | `-0.019` | `True` |

## Decision

- Public-bookcase family prediction does not depend on cross-book carryover inside the held-out family to beat raw digits.
- Cross-book carryover still improves compression and remains valid for sequential generation, but it is not required for the positive family-holdout signal.
- This strengthens predictive validation without deriving row0 or promoting a final authorial method.
- No plaintext, translation, row0-origin change, or case reopening is introduced.
