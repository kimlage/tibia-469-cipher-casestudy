# Beam Selector Stability Gate

Classification: `beam_selector_stability_weak_fullfit_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 60 stress-tests the gate-59 `beam_context_combo` selector.
It asks whether the full-fit selector survives support pruning,
leave-one-book retraining, leave-context-out retraining, and
prefix/holdout selection.

## Summary

- Context: `beam_context_combo`.
- Support thresholds: `[1, 2, 3, 5, 8, 10]`.
- Best min support: `1`.
- Best total hits: `230/234`.
- Best residual hits: `10/10`.
- Best clean false changes: `4`.
- Best context count: `73`.
- Best net vs lookup: `128.872` bits.
- Leave-one-book residual hits: `4/10`.
- Leave-context-out residual hits: `5/10`.
- Prefix/holdout cover-all cells: `0/5`.
- Prefix/holdout cover-all-residual cells: `1/5`.
- Prefix/holdout zero-clean-false-change cells: `0/5`.

## Support Thresholds

| Min support | Hits | Residual hits | Clean false changes | Contexts | Net vs lookup |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `1` | `230/234` | `10/10` | `4` | `73` | `128.872` |
| `2` | `215/234` | `5/10` | `14` | `34` | `137.985` |
| `3` | `210/234` | `5/10` | `19` | `22` | `138.122` |
| `10` | `209/234` | `5/10` | `20` | `5` | `104.042` |
| `8` | `209/234` | `5/10` | `20` | `7` | `108.686` |
| `5` | `209/234` | `5/10` | `20` | `9` | `113.329` |

## Residual Stability

| Book | Target | Class | Support | Stable rank | Full hit | Leave-book hit | Leave-context hit |
| ---: | ---: | --- | ---: | ---: | --- | --- | --- |
| `14` | `0` | `literal_understop` | `1` | `5` | `True` | `False` | `False` |
| `16` | `164` | `copy_started_inside_stable_literal` | `1` | `3` | `True` | `False` | `False` |
| `20` | `21` | `internal_copy_missed_as_literal` | `1` | `3` | `True` | `False` | `False` |
| `21` | `0` | `book_start_copy_missed_as_literal` | `1` | `2` | `True` | `False` | `False` |
| `26` | `0` | `book_start_copy_missed_as_literal` | `1` | `1` | `True` | `True` | `True` |
| `34` | `105` | `internal_copy_missed_as_literal` | `1` | `1` | `True` | `True` | `True` |
| `39` | `0` | `book_start_copy_missed_as_literal` | `1` | `1` | `True` | `True` | `True` |
| `45` | `62` | `internal_copy_missed_as_literal` | `1` | `1` | `True` | `True` | `True` |
| `55` | `67` | `copy_length_drift_same_source` | `2` | `1` | `True` | `False` | `True` |
| `57` | `69` | `literal_understop` | `1` | `5` | `True` | `False` | `False` |

## Prefix/Holdout

| Cutoff | Min support | Test hits | Test residual hits | Test clean false changes | Oracle min support |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `1` | `148/163` | `5/8` | `12` | `1` |
| `30` | `1` | `119/130` | `4/5` | `10` | `1` |
| `40` | `1` | `81/88` | `2/3` | `6` | `1` |
| `50` | `1` | `45/50` | `1/2` | `4` | `10` |
| `60` | `1` | `19/20` | `0/0` | `1` | `10` |

## Decision

- Promotes beam selector stability: `False`.
- Weak full-fit selector clue: `True`.
- The gate-59 full-fit selector does not become a stable parser:
  pruning does not remove the clean false changes, leave-context-out
  support collapses most residuals, and prefix/holdout has no
  cover-all test cell.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
