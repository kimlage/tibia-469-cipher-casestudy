# Joint Boundary Digit Gate

Classification: `joint_boundary_digit_pair_model_rejected`
Translation delta: `NONE`

## Purpose

Test the simplest joint target-stream/parser route: emit a boundary flag
and the next digit together under prefix-trained contexts, instead of
choosing boundaries after the target text is known.

## Summary

- Prefix cutoffs tested: `5`.
- Context orders tested: `[0, 1, 2, 3]`.
- Models tested per order: `2`.
- Best nontrivial model: `joint_pair_context_order0`.
- Best aggregate gain vs factorized global-boundary baseline: `-29.950` bits.
- Positive cells for best model: `2/5`.
- Promotes joint parser: `False`.

A simple joint emission of boundary flag and digit does not beat a factorized prevN digit model plus global boundary-rate baseline under prefix holdout. This falsifies the simplest joint target-stream parser route; a future latent-state parser must add real state, not just pair the current boundary flag with the current digit.

## Aggregate Scoreboard

| Model | Order | Aggregate gain | Positive cells |
| --- | ---: | ---: | ---: |
| `separate_context_boundary` | `0` | `0.000` | `0/5` |
| `joint_pair_context` | `0` | `-29.950` | `2/5` |
| `separate_context_boundary` | `1` | `-60.777` | `0/5` |
| `separate_context_boundary` | `2` | `-258.311` | `0/5` |
| `joint_pair_context` | `1` | `-292.213` | `0/5` |
| `separate_context_boundary` | `3` | `-1146.775` | `0/5` |
| `joint_pair_context` | `2` | `-2229.613` | `0/5` |
| `joint_pair_context` | `3` | `-6724.370` | `0/5` |

## Decision

- Simple joint boundary+digit pair emission is rejected.
- No parser/generator is promoted.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
