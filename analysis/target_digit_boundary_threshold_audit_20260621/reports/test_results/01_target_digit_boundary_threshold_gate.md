# Target Digit Boundary Threshold Gate

Classification: `target_digit_boundary_threshold_dependency_reduced_not_generator`
Translation delta: `NONE`

## Purpose

Test whether an absolute `prev2` surprisal/rank threshold can generate
a boundary set without granting op-count, paying only FP/FN corrections.

## Summary

- Books/candidates/actual cutpoints: `60` / `9507` / `201`.
- Best policy: `right_ge:4`.
- Baseline full cutpoint atlas bits: `1570.073`.
- Correction bits after policy charge: `924.379`.
- Saving after policy charge: `645.694` bits.
- Random saving p95 before policy charge: `494.352` bits.
- TP/FP/FN: `94` / `841` / `107`.
- Predicted boundaries/correction events: `935` / `948`.
- Precision/recall: `0.100535` / `0.467662`.
- Exact books: `0/60`.
- Prefix-selected positive test-saving cells: `5/5`.

## Top Full-Fit Policies

| Policy | Saving | TP | FP | FN | Exact books |
| --- | ---: | ---: | ---: | ---: | ---: |
| `right_ge:4` | `645.694` | `94` | `841` | `107` | `0` |
| `rank_top:0.15` | `639.465` | `102` | `1296` | `99` | `0` |
| `rank_top:0.1` | `638.141` | `85` | `838` | `116` | `0` |
| `right_ge:3.5` | `631.498` | `106` | `1314` | `95` | `0` |
| `right_ge:4.5` | `630.863` | `74` | `451` | `127` | `0` |
| `rank_top:0.2` | `626.165` | `112` | `1769` | `89` | `0` |
| `rank_top:0.08` | `625.942` | `74` | `657` | `127` | `0` |
| `rank_top:0.05` | `621.967` | `61` | `385` | `140` | `0` |

## Decision

- Promotes dependency reduction: `True`.
- Promotes endpoint generator: `False`.
- The threshold set removes the need to grant op-count, but only by paying a large FP/FN correction list.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
