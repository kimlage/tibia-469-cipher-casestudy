# Target Digit Boundary Rank-Code Gate

Classification: `target_digit_boundary_rankcode_weak_not_promoted`
Translation delta: `NONE`

## Purpose

Test whether the full rank distribution of internal cutpoints under
`prev2_digits` right-surprisal reduces the paid cutpoint atlas.

## Summary

- Books/cutpoints/candidate positions: `60` / `201` / `9507`.
- Best scheme: `top5_10_20_50`.
- Best bin totals: `[63, 23, 27, 43, 45]`.
- Baseline cutpoint bits: `1137.308`.
- Model bits after scheme charge: `1018.908`.
- Saving after scheme charge: `118.400` bits.
- Random saving p95 for best scheme: `-57.822` bits.
- Prefix-selected positive test-saving cells after scheme charge: `4/5`.

## Full-Fit Rows

| Scheme | Bin totals | Saving after scheme | Random saving p95 |
| --- | --- | ---: | ---: |
| `top10_rest` | `[86, 115]` | `106.361` | `-37.965` |
| `top10_20_50` | `[86, 27, 43, 45]` | `109.810` | `-33.002` |
| `top5_10_20_50` | `[63, 23, 27, 43, 45]` | `118.400` | `-57.822` |
| `top5_10_15_20_30_50` | `[63, 23, 17, 10, 21, 22, 45]` | `104.801` | `-69.656` |
| `deciles` | `[86, 27, 21, 11, 11, 10, 8, 11, 10, 6]` | `51.073` | `-7.140` |
| `ventiles` | `[63, 23, 17, 10, 11, 10, 6, 5, 5, 6, 7, 3, 1, 7, 6, 5, 6, 4, 5, 1]` | `34.925` | `-4.797` |

## Prefix/Suffix Rows

| Cutoff | Selected scheme | Test cutpoints | Test saving after scheme |
| ---: | --- | ---: | ---: |
| `20` | `top10_rest` | `132` | `85.731` |
| `30` | `top5_10_20_50` | `100` | `77.044` |
| `40` | `top5_10_20_50` | `65` | `48.215` |
| `50` | `top5_10_20_50` | `36` | `25.831` |
| `60` | `top5_10_20_50` | `10` | `-2.915` |

## Decision

- Promotes boundary rank-code clue: `False`.
- Promotes endpoint generator: `False`.
- The rank distribution improves full-fit cutpoint coding, but prefix-selected suffix validation fails in one cell.
- The prior boundary-pruning clue remains the stronger promoted result.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
