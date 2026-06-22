# Combined Boundary Endpoint Decoder Gate

Classification: `combined_boundary_endpoint_decoder_rejected`
Translation delta: `NONE`

## Purpose

Test whether the promoted digit-surprisal boundary clue and the promoted
`age_bucket` hazard become an exact endpoint selector when combined under
prefix holdout and granted the true number of internal cutpoints.

## Summary

- Model families tested: `4`.
- Prefix cutoffs tested: `5`.
- Best family: `age_plus_surprisal_bin_additive`.
- Best aggregate hits: `74/343`.
- Best cells beating random p95: `5/5`.
- Best aggregate exact books: `43`.
- Best aggregate nontrivial exact books: `0`.
- Promotes endpoint decoder: `False`.

Combining the promoted digit-surprisal boundary clue with the promoted age hazard improves endpoint hit rate over age alone, but still does not yield a nontrivial exact endpoint decoder under prefix holdout. The combined features remain dependency clues, not a skeleton generator.

## Family Summary

| Family | Hits | Cells > random p95 | Exact books | Nontrivial exact |
| --- | ---: | ---: | ---: | ---: |
| `age_only` | `9/343` | `0/5` | `43` | `0` |
| `surprisal_bin_only` | `81/343` | `4/5` | `43` | `0` |
| `age_plus_surprisal_bin_additive` | `74/343` | `5/5` | `43` | `0` |
| `age_x_surprisal_bin_joint` | `78/343` | `4/5` | `43` | `0` |

## Cutoff Rows

| Cutoff | Family | Boundaries | Hits | Random hit p95 | Exact books | Nontrivial exact |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `20` | `age_only` | `132` | `4` | `9.000` | `12` | `0` |
| `20` | `surprisal_bin_only` | `132` | `35` | `9.000` | `12` | `0` |
| `20` | `age_plus_surprisal_bin_additive` | `132` | `29` | `9.000` | `12` | `0` |
| `20` | `age_x_surprisal_bin_joint` | `132` | `30` | `9.000` | `12` | `0` |
| `30` | `age_only` | `100` | `3` | `7.000` | `10` | `0` |
| `30` | `surprisal_bin_only` | `100` | `24` | `7.000` | `10` | `0` |
| `30` | `age_plus_surprisal_bin_additive` | `100` | `23` | `7.000` | `10` | `0` |
| `30` | `age_x_surprisal_bin_joint` | `100` | `26` | `7.000` | `10` | `0` |
| `40` | `age_only` | `65` | `1` | `5.000` | `9` | `0` |
| `40` | `surprisal_bin_only` | `65` | `15` | `5.000` | `9` | `0` |
| `40` | `age_plus_surprisal_bin_additive` | `65` | `14` | `5.000` | `9` | `0` |
| `40` | `age_x_surprisal_bin_joint` | `65` | `15` | `5.000` | `9` | `0` |
| `50` | `age_only` | `36` | `1` | `2.000` | `7` | `0` |
| `50` | `surprisal_bin_only` | `36` | `6` | `2.000` | `7` | `0` |
| `50` | `age_plus_surprisal_bin_additive` | `36` | `6` | `2.000` | `7` | `0` |
| `50` | `age_x_surprisal_bin_joint` | `36` | `6` | `2.000` | `7` | `0` |
| `60` | `age_only` | `10` | `0` | `1.000` | `5` | `0` |
| `60` | `surprisal_bin_only` | `10` | `1` | `1.000` | `5` | `0` |
| `60` | `age_plus_surprisal_bin_additive` | `10` | `2` | `1.000` | `5` | `0` |
| `60` | `age_x_surprisal_bin_joint` | `10` | `1` | `1.000` | `5` | `0` |

## Decision

- Combined boundary endpoint decoding is rejected as a generator.
- The tested features remain dependency clues only.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
