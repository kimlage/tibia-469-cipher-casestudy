# Operation Cutpoint Lattice Gate

Classification: `operation_cutpoint_lattice_generator_rejected`
Translation delta: `NONE`

## Purpose

Test whether operation boundaries are aligned to a small normalized
lattice after granting book length and operation count. This is
source-free and target-text-free: it checks proportional grid
placement, not source choice or plaintext.

## Summary

- Books/operations: `60` / `261`.
- Internal cutpoints tested: `201`.
- Denominators tested: `68`.
- Best denominator: `128`.
- Best exact books: `41/60`.
- Best cutpoint hits: `159/201`.
- Best random mean/p95/max hits: `161.357` / `169` / `174`.
- Best hit lift vs random mean: `-2.357`.
- Prefix/holdout cover-all cells: `0/5`.
- Prefix/holdout beats-random-p95 cells: `0/5`.

## Top Denominators

| Denominator | Exact books | Hits | Random mean hits | Random p95 | Random max | Lift |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `128` | `41/60` | `159/201` | `161.357` | `169` | `174` | `-2.357` |
| `100` | `34/60` | `144/201` | `129.673` | `140` | `147` | `14.327` |
| `90` | `30/60` | `129/201` | `117.368` | `128` | `138` | `11.632` |
| `80` | `27/60` | `105/201` | `105.728` | `117` | `126` | `-0.728` |
| `62` | `26/60` | `87/201` | `84.043` | `95` | `102` | `2.957` |
| `70` | `25/60` | `99/201` | `93.330` | `105` | `109` | `5.670` |
| `64` | `25/60` | `90/201` | `86.058` | `98` | `106` | `3.942` |
| `51` | `24/60` | `76/201` | `68.665` | `80` | `89` | `7.335` |
| `56` | `24/60` | `70/201` | `75.627` | `86` | `92` | `-5.627` |
| `54` | `23/60` | `78/201` | `72.957` | `83` | `92` | `5.043` |

## Prefix/Holdout

| Cutoff | Selected d | Test exact books | Test hits | Random mean | Random p95 | Beats p95 | Cover all |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `20` | `128` | `36/50` | `104/132` | `104.797` | `112` | `False` | `False` |
| `30` | `128` | `30/40` | `77/100` | `78.073` | `84` | `False` | `False` |
| `40` | `128` | `23/30` | `48/65` | `48.855` | `53` | `False` | `False` |
| `50` | `128` | `15/20` | `22/36` | `23.812` | `28` | `False` | `False` |
| `60` | `128` | `9/10` | `8/10` | `8.430` | `10` | `False` | `False` |

## Decision

- Promotes cutpoint-lattice generator: `False`.
- Small proportional lattices do not generate the operation cutpoint atlas.
- The best denominator is scored as an alignment clue only if it exceeds random controls; it still does not choose the exact cutpoint sequence.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
