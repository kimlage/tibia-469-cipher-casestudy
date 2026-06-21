# Beam Rank Selector Gate

Classification: `beam_rank_selector_weak_clue_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 59 tests the selector that gate 58 left missing. Gate 58 showed
that a width-5 beam can preserve the stable branch; this gate asks
whether observable prefix-trained context mappings can choose the
right rank inside that beam.

## Summary

- Objective: `max_suffix_copy_digits`.
- Beam width: `5`.
- Decisions: `234`.
- Residual decisions: `10`.
- Clean controls: `224`.
- Context families: `12`.
- Best context: `beam_context_combo`.
- Best total hits: `230/234`.
- Best residual hits: `10/10`.
- Best clean false changes: `4`.
- Top-1 beam baseline: `209/234` with `5/10` residual hits.
- Prefix/holdout cover-all cells: `0/5`.
- Prefix/holdout cover-all-residual cells: `1/5`.
- Prefix/holdout zero-clean-false-change cells: `0/5`.
- Optimistic selector without table cost: `39.732` bits.
- Optimistic selector net vs residual lookup: `-39.629` bits.
- Full-fit context table cost: `169.501` bits.
- Full-fit selector with table/corrections: `209.233` bits.
- Full-fit selector net vs residual lookup: `129.872` bits.

## Full-Fit Scoreboard

| Context | Hits | Residual hits | Clean false changes | Contexts |
| --- | ---: | ---: | ---: | ---: |
| `beam_context_combo` | `230/234` | `10/10` | `4` | `73` |
| `top2_signature` | `228/234` | `8/10` | `4` | `30` |
| `top1_x_active_shape` | `224/234` | `8/10` | `8` | `24` |
| `top1_shape` | `217/234` | `4/10` | `11` | `17` |
| `position_x_active_shape` | `214/234` | `7/10` | `17` | `37` |
| `active_len_x_branch_count` | `213/234` | `5/10` | `16` | `19` |
| `active_shape` | `211/234` | `7/10` | `20` | `12` |
| `op_index_x_active_shape` | `211/234` | `7/10` | `20` | `27` |
| `global` | `209/234` | `5/10` | `20` | `1` |
| `active_type` | `209/234` | `5/10` | `20` | `2` |
| `position` | `209/234` | `5/10` | `20` | `4` |
| `position_x_active_type` | `209/234` | `5/10` | `20` | `8` |

## Prefix/Holdout

| Cutoff | Context | Test hits | Test residual hits | Test clean false changes | Oracle context |
| ---: | --- | ---: | ---: | ---: | --- |
| `20` | `beam_context_combo` | `148/163` | `5/8` | `12` | `beam_context_combo` |
| `30` | `beam_context_combo` | `119/130` | `4/5` | `10` | `position_x_active_shape` |
| `40` | `beam_context_combo` | `81/88` | `2/3` | `6` | `top2_signature` |
| `50` | `beam_context_combo` | `45/50` | `1/2` | `4` | `top2_signature` |
| `60` | `beam_context_combo` | `19/20` | `0/0` | `1` | `position_x_active_shape` |

## Decision

- Promotes beam rank selector: `False`.
- Weak beam rank selector clue: `True`.
- The selector improves neither into an exact parser nor into a
  stable replacement for residual lookup. The best full-fit context
  resolves all residuals but changes clean controls; after paying
  the context->rank table it is worse than lookup, and prefix/holdout
  never covers every held-out test decision.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
