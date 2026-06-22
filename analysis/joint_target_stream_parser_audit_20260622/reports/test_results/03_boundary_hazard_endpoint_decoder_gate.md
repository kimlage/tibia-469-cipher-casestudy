# Boundary Hazard Endpoint Decoder Gate

Classification: `boundary_hazard_endpoint_decoder_rejected`
Translation delta: `NONE`

## Purpose

Test whether the promoted `age_bucket` boundary hazard can choose exact
cutpoint positions when the true number of internal cutpoints is granted.

## Summary

- Prefix cutoffs tested: `5`.
- Aggregate hazard hits: `9/343`.
- Aggregate random hit p95 sum: `24.000`.
- Cells beating random p95: `0/5`.
- Aggregate exact books: `43`.
- Aggregate nontrivial exact books: `0`.
- Promotes endpoint decoder: `False`.

The age hazard improves probabilistic boundary coding, but when it is forced to decode exact endpoint positions even with true op-count granted, it does not beat same-count random endpoint controls. The hazard is not an endpoint parser.

## Cutoff Rows

| Cutoff | Boundaries | Hazard hits | Random hit p95 | Exact books | Nontrivial exact |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `132` | `4` | `9.000` | `12` | `0` |
| `30` | `100` | `3` | `7.000` | `10` | `0` |
| `40` | `65` | `1` | `5.000` | `9` | `0` |
| `50` | `36` | `1` | `2.000` | `7` | `0` |
| `60` | `10` | `0` | `1.000` | `5` | `0` |

## Decision

- Hazard endpoint decoder is rejected.
- The `age_bucket` hazard remains only a probabilistic dependency reducer.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
