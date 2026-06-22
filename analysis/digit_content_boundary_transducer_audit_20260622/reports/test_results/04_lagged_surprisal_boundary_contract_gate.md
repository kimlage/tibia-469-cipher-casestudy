# Lagged Surprisal Boundary Contract Gate

Classification: `LAGGED_SURPRISAL_BOUNDARY_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether the strong right-surprisal start-candidate signal can be reinterpreted as a one-digit-lag boundary annotation program after paying the first copied digit as external innovation.

## Summary

- Lagged bits after policy and copy lag tax: `2153.437`.
- Exact start composition baseline bits: `2063.661`.
- Delta after lag tax: `89.777` bits.
- Candidate bits before policy/tax: `1660.792`.
- Copy-hit lag tax: `488.323` bits (`147` copy starts at `3.322` bits each).
- Start hits: `171/343`.
- Copy misses still requiring exact correction: `148`.
- Cells beating random top-K p05 after lag tax: `0/5`.

## Prefix Holdouts

| Cutoff | Family | Rate | Hits | Copy hits | Copy misses | Lagged bits | Baseline bits | Delta | Random p05 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `20` | `right_ge4_diagnostic` | `0.160` | `71` | `61` | `52` | `828.691` | `775.501` | `53.190` | `False` |
| `30` | `right_ge4_diagnostic` | `0.080` | `42` | `37` | `48` | `596.630` | `598.810` | `-2.180` | `False` |
| `40` | `right_ge4_diagnostic` | `0.160` | `34` | `27` | `28` | `410.860` | `395.378` | `15.482` | `False` |
| `50` | `right_ge4_diagnostic` | `0.160` | `21` | `19` | `13` | `245.060` | `229.691` | `15.370` | `False` |
| `60` | `right_ge4_diagnostic` | `0.160` | `3` | `3` | `7` | `67.874` | `64.281` | `3.593` | `False` |

## Decision

A one-digit-lag annotation can keep the right-surprisal clue in play only as a weak segmentation annotation. It is not a promoted copy/literal decoder, because copy starts recognized late must externalize copied digits and missed copy starts still require exact correction.
