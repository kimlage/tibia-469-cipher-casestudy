# Residual Mode Header Codec Gate

Classification: `RESIDUAL_MODE_HEADER_CODEC_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether paying the promoted residual book mode as a header reduces exact executable-decoder streams after charging the header.

## Summary

- Baseline exact-stream bits: `10161.703`.
- Header codec bits: `10950.680`.
- Saving: `-788.977` bits.
- Header bits paid: `891.772`.
- Coarse stream saving before header: `110.682`.
- Literal payload saving before header: `-7.887`.
- Positive splits: `0/20`.
- Shuffled p95: `-919.305`.
- Beats shuffled p95: `True`.

## Split Results

| Split | Type | Test books | Saving | Header | Coarse saving | Literal saving |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `prefix_20` | `prefix` | `50` | `-226.829` | `252.370` | `25.750` | `-0.209` |
| `prefix_30` | `prefix` | `40` | `-174.887` | `193.954` | `20.132` | `-1.066` |
| `prefix_40` | `prefix` | `30` | `-114.458` | `141.282` | `28.196` | `-1.372` |
| `prefix_50` | `prefix` | `20` | `-81.012` | `96.082` | `16.223` | `-1.153` |
| `prefix_60` | `prefix` | `10` | `-30.525` | `42.430` | `12.813` | `-0.907` |
| `family_hellgate_public_bookcase_1` | `family` | `2` | `-14.320` | `14.320` | `0.000` | `0.000` |
| `family_hellgate_public_bookcase_13` | `family` | `3` | `-18.425` | `15.927` | `-1.990` | `-0.508` |
| `family_hellgate_public_bookcase_2` | `family` | `2` | `-14.320` | `14.320` | `0.000` | `0.000` |
| `family_hellgate_public_bookcase_20` | `family` | `2` | `-9.261` | `10.413` | `1.152` | `0.000` |
| `family_hellgate_public_bookcase_21` | `family` | `3` | `-4.014` | `9.930` | `5.916` | `0.000` |
| `family_hellgate_public_bookcase_23` | `family` | `2` | `-10.149` | `10.413` | `0.264` | `0.000` |
| `family_hellgate_public_bookcase_27` | `family` | `2` | `-3.448` | `6.325` | `2.877` | `0.000` |
| `family_hellgate_public_bookcase_3` | `family` | `2` | `-10.905` | `7.605` | `-3.299` | `0.000` |
| `family_hellgate_public_bookcase_30` | `family` | `2` | `-8.765` | `7.425` | `-0.801` | `-0.539` |
| `family_hellgate_public_bookcase_33` | `family` | `2` | `-4.052` | `6.506` | `2.454` | `0.000` |
| `family_hellgate_public_bookcase_4` | `family` | `3` | `-16.925` | `13.605` | `-3.719` | `0.399` |
| `family_hellgate_public_bookcase_40` | `family` | `4` | `-11.708` | `15.838` | `4.913` | `-0.783` |
| `family_hellgate_public_bookcase_6` | `family` | `2` | `-16.704` | `11.512` | `-3.443` | `-1.749` |
| `family_hellgate_public_bookcase_7` | `family` | `3` | `-14.726` | `13.605` | `-1.121` | `0.000` |
| `family_hellgate_public_bookcase_8` | `family` | `2` | `-3.544` | `7.910` | `4.367` | `0.000` |

## Decision

Promotion requires the paid mode header to reduce exact executable streams and beat shuffled-mode controls. Composition-index and copy-hint rank costs are carried through unchanged here.
