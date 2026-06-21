# Beam Markov State Selector Gate

Classification: `beam_markov_state_selector_weak_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 63 tests whether the missing downstream selector is a small
sequential state rule over beam ranks. It is stricter than a full-fit
context table: teacher-forced state is diagnostic only, and promotion
requires free-run state to hold under prefix/holdout.

## Summary

- Decisions: `234`.
- Residual decisions: `10`.
- Clean controls: `224`.
- Beam width: `5`.
- Context families: `8`.
- Best teacher-forced context: `prev_rank_x_beam_combo`.
- Best teacher-forced hits: `231/234` with `10/10` residual hits.
- Best free-run context: `prev_rank_x_beam_combo`.
- Best free-run hits: `230/234`.
- Best free-run residual hits: `9/10`.
- Best free-run clean false changes: `3`.
- Top-1 beam baseline hits: `209/234` with `5/10` residual hits.
- Prefix/holdout cover-all cells: `0/5`.
- Prefix/holdout cover-all-residual cells: `1/5`.
- Prefix/holdout zero-clean-false-change cells: `0/5`.
- Best free-run net vs lookup: `159.472` bits.

## Free-Run Scoreboard

| Context | Hits | Residual hits | Clean false changes | Contexts |
| --- | ---: | ---: | ---: | ---: |
| `prev_rank_x_beam_combo` | `230/234` | `9/10` | `3` | `86` |
| `prev_rank_x_top2_signature` | `229/234` | `9/10` | `4` | `58` |
| `prev_rank_x_top1_shape` | `222/234` | `6/10` | `8` | `41` |
| `prev_rank_x_active_shape` | `212/234` | `6/10` | `18` | `33` |
| `global` | `209/234` | `5/10` | `20` | `1` |
| `prev_rank` | `209/234` | `5/10` | `20` | `6` |
| `prev_rank_x_active_type` | `209/234` | `5/10` | `20` | `10` |
| `prev_rank_x_position` | `209/234` | `5/10` | `20` | `12` |

## Prefix/Holdout

| Cutoff | Context | Test hits | Test residual hits | Test clean false changes | Oracle context |
| ---: | --- | ---: | ---: | ---: | --- |
| `20` | `prev_rank_x_top2_signature` | `147/163` | `4/8` | `12` | `prev_rank_x_beam_combo` |
| `30` | `prev_rank_x_beam_combo` | `119/130` | `4/5` | `10` | `prev_rank_x_top1_shape` |
| `40` | `prev_rank_x_beam_combo` | `81/88` | `2/3` | `6` | `prev_rank_x_top1_shape` |
| `50` | `prev_rank_x_beam_combo` | `45/50` | `1/2` | `4` | `prev_rank_x_active_shape` |
| `60` | `prev_rank_x_beam_combo` | `19/20` | `0/0` | `1` | `prev_rank_x_active_shape` |

## Decision

- Promotes Markov state selector: `False`.
- Weak Markov state selector clue: `True`.
- The free-run state selector does not become a parser rule. If it
  cannot predict the next rank from its own previous rank under
  holdout, it is just another fitted label table.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
