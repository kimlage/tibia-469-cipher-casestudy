# Beam Survival Budget Gate

Classification: `beam_survival_weak_path_state_clue_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 58 asks a narrower path-state question after direct branch
selection, rankers, context tables, observable signatures, and latent
lookup pricing failed: does the stable branch at least remain inside
a small observable beam? This is a survival test, not a promoted
selection rule.

## Summary

- Decisions: `234`.
- Residual decisions: `10`.
- Clean controls: `224`.
- Objectives tested: `5`.
- Best objective: `max_suffix_copy_digits`.
- Best all-decision beam width: `5`.
- Best residual beam width: `5`.
- Residual top-1 choices under best objective: `5/10`.
- Clean top-1 choices under best objective: `204/224`.
- Prefix/holdout all-survival cells at train width: `5/5`.
- Prefix/holdout residual-survival cells at train width: `5/5`.
- Fixed-width model bits after site/objective cost: `84.111`.
- Fixed-width net vs residual lookup: `4.750`.
- Rank lower bound bits after site/objective cost: `69.706`.
- Rank lower bound net vs residual lookup: `-9.655`.

## Objective Scoreboard

| Objective | All max rank | Residual max rank | Clean max rank | Residual top1 | Clean top1 | Fixed-width bits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `max_suffix_copy_digits` | `5` | `5` | `5` | `5/10` | `204/224` | `23.219` |
| `min_suffix_literals` | `5` | `5` | `5` | `5/10` | `204/224` | `23.219` |
| `max_suffix_copy_count` | `7` | `7` | `5` | `4/10` | `69/224` | `28.074` |
| `balanced_ops_literals` | `8` | `8` | `5` | `6/10` | `204/224` | `30.000` |
| `min_suffix_ops` | `18` | `18` | `17` | `0/10` | `50/224` | `41.699` |

## Prefix/Holdout

| Cutoff | Objective | Train beam | Test all max rank | Test residual max rank | Test all survives | Test residual survives |
| ---: | --- | ---: | ---: | ---: | --- | --- |
| `20` | `max_suffix_copy_digits` | `5` | `5` | `5` | `True` | `True` |
| `30` | `max_suffix_copy_digits` | `5` | `5` | `5` | `True` | `True` |
| `40` | `max_suffix_copy_digits` | `5` | `5` | `5` | `True` | `True` |
| `50` | `max_suffix_copy_digits` | `5` | `5` | `5` | `True` | `True` |
| `60` | `max_suffix_copy_digits` | `5` | `3` | `0` | `True` | `True` |

## Residual Rows Under Best Objective

| Book | Target | Class | Branches | Stable rank | Active | Stable |
| ---: | ---: | --- | ---: | ---: | --- | --- |
| `14` | `0` | `literal_understop` | `19` | `5` | `{'type': 'literal', 'target_start': 0, 'length': 27, 'source': None}` | `{'type': 'literal', 'target_start': 0, 'length': 39, 'source': None}` |
| `16` | `164` | `copy_started_inside_stable_literal` | `9` | `3` | `{'type': 'copy', 'target_start': 164, 'length': 8, 'source': 473}` | `{'type': 'literal', 'target_start': 164, 'length': 1, 'source': None}` |
| `20` | `21` | `internal_copy_missed_as_literal` | `24` | `3` | `{'type': 'literal', 'target_start': 21, 'length': 3, 'source': None}` | `{'type': 'copy', 'target_start': 21, 'length': 10, 'source': 180}` |
| `21` | `0` | `book_start_copy_missed_as_literal` | `26` | `2` | `{'type': 'literal', 'target_start': 0, 'length': 7, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 9, 'source': 197}` |
| `26` | `0` | `book_start_copy_missed_as_literal` | `22` | `1` | `{'type': 'literal', 'target_start': 0, 'length': 1, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 11, 'source': 3054}` |
| `34` | `105` | `internal_copy_missed_as_literal` | `13` | `1` | `{'type': 'literal', 'target_start': 105, 'length': 5, 'source': None}` | `{'type': 'copy', 'target_start': 105, 'length': 5, 'source': 183}` |
| `39` | `0` | `book_start_copy_missed_as_literal` | `24` | `1` | `{'type': 'literal', 'target_start': 0, 'length': 7, 'source': None}` | `{'type': 'copy', 'target_start': 0, 'length': 5, 'source': 2520}` |
| `45` | `62` | `internal_copy_missed_as_literal` | `25` | `1` | `{'type': 'literal', 'target_start': 62, 'length': 1, 'source': None}` | `{'type': 'copy', 'target_start': 62, 'length': 8, 'source': 2850}` |
| `55` | `67` | `copy_length_drift_same_source` | `20` | `1` | `{'type': 'copy', 'target_start': 67, 'length': 45, 'source': 2757}` | `{'type': 'copy', 'target_start': 67, 'length': 44, 'source': 2757}` |
| `57` | `69` | `literal_understop` | `20` | `5` | `{'type': 'literal', 'target_start': 69, 'length': 17, 'source': None}` | `{'type': 'literal', 'target_start': 69, 'length': 28, 'source': None}` |

## Decision

- Promotes beam parser: `False`.
- Weak beam-survival clue: `True`.
- Small-beam survival is real but weaker than generation: a width-5
  beam can keep the stable branch alive under the best objective,
  but the top-1 branch still fails residual choices and a fixed-width
  paid model is worse than the residual lookup.
- The rank lower bound is marked diagnostic only because it assumes
  site/rank knowledge rather than a downstream selector.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
