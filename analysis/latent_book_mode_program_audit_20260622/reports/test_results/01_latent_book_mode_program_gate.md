# Latent Book Mode Program Gate

Classification: `LATENT_BOOK_MODE_PROGRAM_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether the promoted book residual mode can be predicted by a small decoder-visible book program instead of paid as a post-hoc joint symbol.

## Summary

- Mode alphabet size: `27`.
- Global mode bits: `891.772`.
- Program mode bits: `945.479`.
- Saving: `-53.707` bits.
- Positive splits: `2/20`.
- Top1 / Beam5 / Beam10 hits: `11` / `64` / `83` over `186` repeated held-out books.
- Shuffled p95: `-26.211`.
- Beats shuffled p95: `False`.

## Split Results

| Split | Type | Feature | Test books | Saving | Program bits | Global bits | Top1 | Beam5 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix_20` | `prefix` | `book_length_bucket` | `50` | `-4.353` | `256.723` | `252.370` | `0` | `5` |
| `prefix_30` | `prefix` | `book_length_x_phase` | `40` | `-2.585` | `196.539` | `193.954` | `4` | `12` |
| `prefix_40` | `prefix` | `book_length_x_phase` | `30` | `-2.585` | `143.867` | `141.282` | `4` | `17` |
| `prefix_50` | `prefix` | `book_phase` | `20` | `-2.585` | `98.667` | `96.082` | `1` | `11` |
| `prefix_60` | `prefix` | `book_length_x_phase` | `10` | `-2.585` | `45.015` | `42.430` | `0` | `6` |
| `family_hellgate_public_bookcase_1` | `family` | `book_phase` | `2` | `0.882` | `13.437` | `14.320` | `0` | `0` |
| `family_hellgate_public_bookcase_13` | `family` | `book_phase` | `3` | `-0.409` | `16.336` | `15.927` | `0` | `1` |
| `family_hellgate_public_bookcase_2` | `family` | `book_phase` | `2` | `0.882` | `13.437` | `14.320` | `0` | `0` |
| `family_hellgate_public_bookcase_20` | `family` | `book_phase` | `2` | `-0.703` | `11.116` | `10.413` | `0` | `1` |
| `family_hellgate_public_bookcase_21` | `family` | `book_phase` | `3` | `-3.235` | `13.166` | `9.930` | `1` | `3` |
| `family_hellgate_public_bookcase_23` | `family` | `book_phase` | `2` | `-0.703` | `11.116` | `10.413` | `0` | `1` |
| `family_hellgate_public_bookcase_27` | `family` | `book_phase` | `2` | `-3.205` | `9.531` | `6.325` | `1` | `2` |
| `family_hellgate_public_bookcase_3` | `family` | `book_phase` | `2` | `-3.510` | `11.116` | `7.605` | `0` | `1` |
| `family_hellgate_public_bookcase_30` | `family` | `book_length_x_phase` | `2` | `-5.579` | `13.004` | `7.425` | `0` | `0` |
| `family_hellgate_public_bookcase_33` | `family` | `book_phase` | `2` | `-6.932` | `13.437` | `6.506` | `0` | `0` |
| `family_hellgate_public_bookcase_4` | `family` | `book_phase` | `3` | `-2.731` | `16.336` | `13.605` | `0` | `1` |
| `family_hellgate_public_bookcase_40` | `family` | `book_phase` | `4` | `-6.304` | `22.142` | `15.838` | `0` | `1` |
| `family_hellgate_public_bookcase_6` | `family` | `book_phase` | `2` | `-0.340` | `11.853` | `11.512` | `0` | `0` |
| `family_hellgate_public_bookcase_7` | `family` | `book_phase` | `3` | `-3.468` | `17.073` | `13.605` | `0` | `1` |
| `family_hellgate_public_bookcase_8` | `family` | `book_length_x_phase` | `2` | `-3.660` | `11.571` | `7.910` | `0` | `1` |

## Decision

Promotion requires feature-conditioned book-mode coding to beat global mode coding and shuffled-mode controls. Even when promoted, this is a book-mode controller clue, not exact generation of the residual tapes.
