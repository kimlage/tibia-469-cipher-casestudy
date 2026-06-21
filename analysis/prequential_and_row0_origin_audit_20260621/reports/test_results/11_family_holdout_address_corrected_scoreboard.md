# Family Holdout Address-Corrected Scoreboard

Classification: `family_holdout_reparse_beats_or_ties_active_after_address_correction`
Translation delta: `NONE`

## Purpose

Audit 10 showed that the five family losses against the active recipe were
copy-address coordinate artifacts. This audit applies that address-space
correction to all public-bookcase family holdouts.

## Summary

- Families checked: `19`.
- Active recipes roundtrip after address rebase: `True`.
- Reparse beats raw digits: `19/19`.
- Reparse beats/ties active before correction: `15/19`.
- Reparse beats/ties active after address correction: `19/19`.
- Mean reparse minus active before correction: `-139.959` bits.
- Mean reparse minus active after correction: `-161.381` bits.
- Address-corrected worse labels: `[]`.

## Rows

| Family | Books | Original delta | Address-corrected delta | Address shift | Beats/ties corrected |
|---|---|---:|---:|---:|---|
| `hellgate_public_bookcase_1` | `[12, 14]` | `-296.246` | `-332.819` | `36.573` | `True` |
| `hellgate_public_bookcase_10` | `[0, 1, 2]` | `-1191.899` | `-1266.550` | `74.650` | `True` |
| `hellgate_public_bookcase_12` | `[3, 4]` | `-333.686` | `-412.696` | `79.010` | `True` |
| `hellgate_public_bookcase_13` | `[40, 41, 42]` | `8.534` | `-0.737` | `9.271` | `True` |
| `hellgate_public_bookcase_2` | `[15, 16]` | `-123.225` | `-156.101` | `32.876` | `True` |
| `hellgate_public_bookcase_20` | `[44, 45]` | `-35.874` | `-39.258` | `3.385` | `True` |
| `hellgate_public_bookcase_21` | `[62, 63, 64]` | `0.515` | `0.000` | `0.515` | `True` |
| `hellgate_public_bookcase_22` | `[5, 6, 7]` | `-176.580` | `-253.028` | `76.448` | `True` |
| `hellgate_public_bookcase_23` | `[28, 29]` | `-97.839` | `-109.614` | `11.775` | `True` |
| `hellgate_public_bookcase_27` | `[46, 47]` | `-36.174` | `-38.597` | `2.423` | `True` |
| `hellgate_public_bookcase_3` | `[20, 21]` | `-87.979` | `-105.072` | `17.093` | `True` |
| `hellgate_public_bookcase_30` | `[32, 33]` | `-31.226` | `-34.585` | `3.359` | `True` |
| `hellgate_public_bookcase_33` | `[18, 19]` | `8.986` | `0.000` | `8.986` | `True` |
| `hellgate_public_bookcase_36` | `[8, 9]` | `-222.472` | `-249.183` | `26.711` | `True` |
| `hellgate_public_bookcase_4` | `[24, 25, 26]` | `-2.019` | `-13.738` | `11.719` | `True` |
| `hellgate_public_bookcase_40` | `[50, 51, 52, 53]` | `-42.822` | `-46.115` | `3.292` | `True` |
| `hellgate_public_bookcase_6` | `[38, 39]` | `-2.347` | `-6.698` | `4.351` | `True` |
| `hellgate_public_bookcase_7` | `[54, 55, 56]` | `3.124` | `-1.440` | `4.564` | `True` |
| `hellgate_public_bookcase_8` | `[68, 69]` | `0.000` | `0.000` | `0.000` | `True` |

## Decision

- Public-bookcase family holdout reparsing beats raw digits in every family.
- The apparent active-recipe local wins disappear after address-space correction.
- This strengthens predictive recipe validation, but it does not derive row0 or promote a final authorial method.
- No plaintext, translation, row0-origin change, or case reopening is introduced.
