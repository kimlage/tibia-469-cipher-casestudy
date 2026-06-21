# Residual Patch Program Gate

Classification: `residual_patch_program_weak_macro_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 62 tests whether the remaining residual branch choices compress
into a small mechanical patch program. This is not another bit sweep:
it separates patch-label compression from the harder question of where
the patches apply.

## Summary

- Decisions: `234`.
- Residual decisions: `10`.
- Clean controls: `224`.
- Best patch mode: `macro`.
- Best patch distinct labels: `5`.
- Best patch singletons: `2`.
- Best patch largest class: `3`.
- Site bits alone: `56.631`.
- Best patch program bits: `81.851`.
- Best patch net vs lookup: `2.490` bits.
- Best detector rule: `always`.
- Best detector TP/FP/FN: `10/224/0`.
- Best zero-FP detector: `top1_copy__and__active_copy_le8` with `1` residual hits.
- Clean-first detector: `top1_copy__and__active_copy_le8` with TP/FP/FN `1/0/9`.
- Detector+patch net vs lookup: `230.556` bits.
- Prefix/holdout exact detector cells: `0/5`.

## Patch Label Scoreboard

| Mode | Labels | Singletons | Largest class | Total bits | Net vs lookup |
| --- | ---: | ---: | ---: | ---: | ---: |
| `macro` | `5` | `2` | `3` | `81.851` | `2.490` |
| `delta_shape` | `8` | `6` | `2` | `88.631` | `9.270` |
| `coarse_shape` | `10` | `10` | `1` | `91.851` | `12.490` |
| `exact_patch` | `10` | `10` | `1` | `91.851` | `12.490` |

## Prefix/Holdout Detector

| Cutoff | Rule | Test TP | Test FP | Test FN |
| ---: | --- | ---: | ---: | ---: |
| `20` | `always` | `8` | `155` | `0` |
| `30` | `always` | `5` | `125` | `0` |
| `40` | `always` | `3` | `85` | `0` |
| `50` | `always` | `2` | `48` | `0` |
| `60` | `always` | `0` | `20` | `0` |

## Decision

- Promotes patch program: `False`.
- Weak macro-patch clue: `True`.
- The residuals do compress into a few macro patch classes, but
  the site-selection cost dominates. Even the cheapest paid patch
  program is worse than the residual lookup lower bound, and the
  best observable detector has false positives/false negatives.
- This is a useful decomposition of the blocker, not a parser rule.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
