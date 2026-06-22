# Closed Loop Digit Survival Gate

Classification: `closed_loop_digit_survival_rejected`
Translation delta: `NONE`

## Purpose

Remove within-book target teacher forcing from the latent transducer route.
The decoder knows the target book length and true prior material, then
generates candidate digit prefixes by literal digit emissions or copied
chunks. The test asks whether the real book is top-1 or survives in the
beam.

## Summary

- Prefix cutoffs tested: `5`.
- Beam width: `250`.
- Copy candidate limit: `80`.
- Tested book instances: `150`.
- Top-1 exact books: `0`.
- Exact books surviving finished beam: `0`.
- True-prefix survival books: `0`.
- Mean true-prefix max fraction: `0.007754`.
- Mean top prefix-match fraction: `0.001326`.
- Promotes closed-loop digit generator: `False`.

The gate removes within-book target teacher forcing and asks whether the real digit stream survives a closed-loop beam when book length and true prior material are granted. This is a generous survival test, not a complete corpus generator.

## Cutoff Rows

| Cutoff | Top-1 exact | Exact in beam | True-prefix survival | Mean true-prefix max | Mean top prefix-match |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `0/50` | `0/50` | `0/50` | `0.008551` | `0.000925` |
| `30` | `0/40` | `0/40` | `0/40` | `0.008216` | `0.001156` |
| `40` | `0/30` | `0/30` | `0/30` | `0.006712` | `0.001541` |
| `50` | `0/20` | `0/20` | `0/20` | `0.006724` | `0.001720` |
| `60` | `0/10` | `0/10` | `0/10` | `0.007103` | `0.002578` |

## Decision

- Closed-loop digit generation is rejected unless the JSON summary says otherwise.
- The result does not touch row0, plaintext, or translation.
- Compression bound is unchanged.
