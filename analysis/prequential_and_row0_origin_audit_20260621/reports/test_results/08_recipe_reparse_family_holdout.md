# Recipe Reparse Family Holdout

Classification: `recipe_reparse_family_holdouts_predictive_with_active_recipe_ties`
Translation delta: `NONE`

## Purpose

Component-only prequential scoring had public-bookcase family failures.
This audit asks whether deterministic recipe discovery also fails on those
families. Each split trains on every book outside one public bookcase family,
then reparses that held-out family under frozen counts.

## Summary

- Families: `19`.
- Reparse beats raw digits: `19/19`.
- Reparse beats active frozen recipe: `14/19`.
- Component-failure families reparse beats raw: `3/3`.
- Mean reparse minus active: `-139.959` bits.

## Rows

| Family | Books | Raw gain | Reparse - active | Beats raw | Beats active | Component failure |
|---|---|---:|---:|---|---|---|
| `hellgate_public_bookcase_1` | `[12, 14]` | `745.600` | `-296.246` | `True` | `True` | `False` |
| `hellgate_public_bookcase_10` | `[0, 1, 2]` | `1284.862` | `-1191.899` | `True` | `True` | `False` |
| `hellgate_public_bookcase_12` | `[3, 4]` | `705.610` | `-333.686` | `True` | `True` | `False` |
| `hellgate_public_bookcase_13` | `[40, 41, 42]` | `1359.567` | `8.534` | `True` | `False` | `False` |
| `hellgate_public_bookcase_2` | `[15, 16]` | `843.449` | `-123.225` | `True` | `True` | `False` |
| `hellgate_public_bookcase_20` | `[44, 45]` | `854.409` | `-35.874` | `True` | `True` | `False` |
| `hellgate_public_bookcase_21` | `[62, 63, 64]` | `1234.859` | `0.515` | `True` | `False` | `False` |
| `hellgate_public_bookcase_22` | `[5, 6, 7]` | `1348.016` | `-176.580` | `True` | `True` | `False` |
| `hellgate_public_bookcase_23` | `[28, 29]` | `923.659` | `-97.839` | `True` | `True` | `False` |
| `hellgate_public_bookcase_27` | `[46, 47]` | `1216.358` | `-36.174` | `True` | `True` | `False` |
| `hellgate_public_bookcase_3` | `[20, 21]` | `713.630` | `-87.979` | `True` | `True` | `False` |
| `hellgate_public_bookcase_30` | `[32, 33]` | `857.191` | `-31.226` | `True` | `True` | `False` |
| `hellgate_public_bookcase_33` | `[18, 19]` | `631.797` | `8.986` | `True` | `False` | `True` |
| `hellgate_public_bookcase_36` | `[8, 9]` | `1419.920` | `-222.472` | `True` | `True` | `False` |
| `hellgate_public_bookcase_4` | `[24, 25, 26]` | `918.560` | `-2.019` | `True` | `True` | `False` |
| `hellgate_public_bookcase_40` | `[50, 51, 52, 53]` | `2595.114` | `-42.822` | `True` | `True` | `False` |
| `hellgate_public_bookcase_6` | `[38, 39]` | `523.227` | `-2.347` | `True` | `True` | `True` |
| `hellgate_public_bookcase_7` | `[54, 55, 56]` | `1158.863` | `3.124` | `True` | `False` | `False` |
| `hellgate_public_bookcase_8` | `[68, 69]` | `896.869` | `0.000` | `True` | `False` | `True` |

## Decision

- Recipe reparsing remains predictive under public-bookcase family holdout.
- The prior component-only family failures are not recipe-discovery failures.
- The active full-corpus recipe is still sometimes cheaper, so the generation explanation remains partial.
- No plaintext, translation, row0-origin change, or case reopening is introduced.
