# Target Digit Boundary Pruning Gate

Classification: `target_digit_boundary_pruning_clue_promoted_not_generator`
Translation delta: `NONE`

## Purpose

Test whether high `prev2_digits` right-surprisal bands reduce the
paid cutpoint dependency after charging misses and threshold choice.

## Summary

- Books/cutpoints/candidate positions: `60` / `201` / `9507`.
- Best q: `0.1`.
- Candidate fraction at best q: `0.102556`.
- Hits/misses: `86/201` / `115`.
- Baseline cutpoint bits: `1137.308`.
- Model bits after q charge: `1031.362`.
- Saving after q charge: `105.946` bits.
- Random saving p95 at best q: `-37.498` bits.
- Prefix-selected positive test-saving cells: `5/5` before q charge, `4/5` after q charge.

## Full-Fit Rows

| q | Candidates | Hits | Misses | Saving after q | Random saving p95 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `0.05` | `502` | `63/201` | `138` | `90.269` | `-53.634` |
| `0.1` | `975` | `86/201` | `115` | `105.946` | `-37.498` |
| `0.15` | `1454` | `103/201` | `98` | `104.657` | `-27.392` |
| `0.2` | `1923` | `113/201` | `88` | `92.792` | `-20.747` |
| `0.25` | `2398` | `124/201` | `77` | `87.696` | `-15.208` |
| `0.3` | `2875` | `134/201` | `67` | `74.997` | `-12.063` |
| `0.4` | `3824` | `145/201` | `56` | `52.214` | `-7.248` |
| `0.5` | `4767` | `156/201` | `45` | `30.216` | `-6.125` |

## Prefix/Suffix Rows

| Cutoff | Selected q | Test hits | Test saving before q | Test saving after q |
| ---: | ---: | ---: | ---: | ---: |
| `20` | `0.1` | `62/132` | `88.316` | `85.316` |
| `30` | `0.05` | `34/100` | `53.105` | `50.105` |
| `40` | `0.1` | `31/65` | `45.298` | `42.298` |
| `50` | `0.1` | `17/36` | `23.733` | `20.733` |
| `60` | `0.1` | `3/10` | `0.591` | `-2.409` |

## Decision

- Promotes boundary pruning clue: `True`.
- Promotes endpoint generator: `False`.
- The clue reduces the paid cutpoint dependency, but exact endpoints still require residual declarations.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
