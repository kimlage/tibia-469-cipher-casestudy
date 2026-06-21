# Beam Hierarchical Backoff Gate

Classification: `beam_hierarchical_backoff_weak_fullfit_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 61 tests whether hierarchical backoff over observable beam
contexts can stabilize the gate-59 selector without relying on
singleton `beam_context_combo` rows.

## Summary

- Families tested: `6`.
- Support thresholds: `[1, 2, 3, 5, 8, 10]`.
- Best family: `global_to_beam_combo`.
- Best min support: `1`.
- Best total hits: `230/234`.
- Best residual hits: `10/10`.
- Best clean false changes: `4`.
- Best context count: `88`.
- Best net vs lookup: `166.286` bits.
- Prefix/holdout cover-all cells: `0/5`.
- Prefix/holdout cover-all-residual cells: `1/5`.
- Prefix/holdout zero-clean-false-change cells: `0/5`.

## Scoreboard

| Family | Min support | Hits | Residual hits | Clean false changes | Contexts | Net vs lookup |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `global_to_beam_combo` | `1` | `230/234` | `10/10` | `4` | `88` | `166.286` |
| `active_branch_to_beam_combo` | `1` | `230/234` | `10/10` | `4` | `122` | `245.231` |
| `position_to_beam_combo` | `1` | `230/234` | `10/10` | `4` | `123` | `247.553` |
| `top_shape_to_beam_combo` | `1` | `230/234` | `10/10` | `4` | `145` | `298.636` |
| `compact_top_signature` | `1` | `228/234` | `8/10` | `4` | `48` | `88.830` |
| `compact_top_signature` | `2` | `223/234` | `3/10` | `4` | `40` | `105.207` |
| `top_shape_to_beam_combo` | `2` | `222/234` | `4/10` | `6` | `89` | `225.519` |
| `compact_top_signature` | `3` | `220/234` | `2/10` | `6` | `31` | `103.566` |
| `top_shape_to_beam_combo` | `3` | `217/234` | `2/10` | `9` | `67` | `205.451` |
| `position_to_beam_combo` | `2` | `216/234` | `5/10` | `13` | `76` | `232.262` |
| `compact_top_signature` | `5` | `216/234` | `3/10` | `11` | `23` | `109.199` |
| `global_to_beam_combo` | `2` | `215/234` | `5/10` | `14` | `47` | `170.755` |
| `active_branch_to_beam_combo` | `2` | `215/234` | `5/10` | `14` | `78` | `242.734` |
| `compact_position_active` | `1` | `214/234` | `7/10` | `17` | `46` | `174.181` |
| `top_shape_to_beam_combo` | `5` | `214/234` | `3/10` | `13` | `41` | `162.571` |

## Prefix/Holdout

| Cutoff | Family | Min support | Test hits | Test residual hits | Test clean false changes | Oracle family |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| `20` | `global_to_beam_combo` | `1` | `148/163` | `5/8` | `12` | `compact_top_signature` |
| `30` | `global_to_beam_combo` | `1` | `119/130` | `4/5` | `10` | `compact_position_active` |
| `40` | `global_to_beam_combo` | `1` | `81/88` | `2/3` | `6` | `global_to_beam_combo` |
| `50` | `global_to_beam_combo` | `1` | `45/50` | `1/2` | `4` | `compact_top_signature` |
| `60` | `global_to_beam_combo` | `1` | `19/20` | `0/0` | `1` | `compact_position_active` |

## Decision

- Promotes hierarchical backoff: `False`.
- Weak hierarchical backoff clue: `True`.
- Hierarchical backoff does not turn the beam selector into a
  promoted parser. Its best row ties the unstable full-fit table
  and still needs support `1`; prefix/holdout does not cover all
  held-out decisions.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
