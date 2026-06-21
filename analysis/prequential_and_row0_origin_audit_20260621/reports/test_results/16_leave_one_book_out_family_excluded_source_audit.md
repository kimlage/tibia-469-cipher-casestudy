# Leave-One-Book-Out Family-Excluded Source Audit

Classification: `family_excluded_singleton_holdout_predictive`
Translation delta: `NONE`

## Purpose

Audit 15 showed that singleton reparsing does not depend on copy sources
crossing artificial source-book boundaries. This audit asks a harder
source question: when a target book belongs to a known public-bookcase
family, remove that entire family from both frozen train counts and copy
sources before reparsing the target book.

Current-prefix copies remain legal if they stay inside the already-emitted
target prefix; the tested leakage is same-family source inventory.

## Summary

- Books checked: `70`.
- Family-labeled books: `46`.
- Roundtrip books: `70/70`.
- Beats raw digits: `70/70`.
- Family-labeled beats raw: `46/46`.
- Mean family-excluded gain vs raw: `460.251` bits.
- Min family-excluded gain vs raw: `56.053` bits.
- Mean family-excluded minus book-bounded: `4.646` bits.
- Max family-excluded minus book-bounded: `119.076` bits.
- Failure books: `[]`.

## Weakest Books

| Book | Families | Excluded peers | Length | Family-excluded gain vs raw |
|---:|---|---|---:|---:|
| `7` | `['hellgate_public_bookcase_22']` | `[5, 6]` | `106` | `56.053` |
| `25` | `['hellgate_public_bookcase_4']` | `[24, 26]` | `35` | `96.116` |
| `49` | `[]` | `[]` | `115` | `124.657` |
| `39` | `['hellgate_public_bookcase_6']` | `[38]` | `59` | `154.076` |
| `54` | `['hellgate_public_bookcase_7']` | `[55, 56]` | `57` | `154.668` |
| `20` | `['hellgate_public_bookcase_3']` | `[21]` | `63` | `169.701` |
| `34` | `[]` | `[]` | `123` | `231.581` |
| `18` | `['hellgate_public_bookcase_33']` | `[19]` | `93` | `262.956` |
| `4` | `['hellgate_public_bookcase_12']` | `[3]` | `140` | `264.443` |
| `67` | `[]` | `[]` | `98` | `283.568` |

## Highest Family-Exclusion Penalties

| Book | Families | Excluded peers | Penalty vs book-bounded | Family-excluded gain vs raw |
|---:|---|---|---:|---:|
| `7` | `['hellgate_public_bookcase_22']` | `[5, 6]` | `119.076` | `56.053` |
| `16` | `['hellgate_public_bookcase_2']` | `[15]` | `75.688` | `407.311` |
| `15` | `['hellgate_public_bookcase_2']` | `[16]` | `73.308` | `359.959` |
| `6` | `['hellgate_public_bookcase_22']` | `[5, 7]` | `60.935` | `291.729` |
| `3` | `['hellgate_public_bookcase_12']` | `[4]` | `0.960` | `422.406` |
| `4` | `['hellgate_public_bookcase_12']` | `[3]` | `0.858` | `264.443` |
| `38` | `['hellgate_public_bookcase_6']` | `[39]` | `0.229` | `368.017` |
| `52` | `['hellgate_public_bookcase_40']` | `[50, 51, 53]` | `0.072` | `415.032` |
| `10` | `[]` | `[]` | `0.000` | `906.090` |
| `11` | `[]` | `[]` | `0.000` | `416.606` |

## Decision

- The singleton holdout is retested after removing same-family books from train counts and copy sources.
- The result is evidence about source dependency only; it does not derive row0 or promote a final authorial method.
- No plaintext, translation, row0-origin change, or case reopening is introduced.
