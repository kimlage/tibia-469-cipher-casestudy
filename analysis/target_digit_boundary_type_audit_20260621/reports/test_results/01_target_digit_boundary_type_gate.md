# Target Digit Boundary Type Gate

Classification: `target_digit_boundary_type_rule_rejected`
Translation delta: `NONE`

## Purpose

Test whether the `prev2_digits` boundary surprisal clue predicts the
next operation type after an internal cutpoint.

## Summary

- Boundaries tested: `201`.
- Next-type counts: `{'copy': 161, 'literal': 40}`.
- Majority baseline: `copy` with `161/201` hits.
- Best predicate: `delta_negative` / literal_when_true `True`.
- Best predicate hits: `131/201`.
- Best predicate delta vs majority: `-30`.
- Prequential positive-delta cells: `0/20`.

## Best Predicate Rows

| Predicate | literal_when_true | Hits | Delta vs majority |
| --- | --- | ---: | ---: |
| `delta_negative` | `True` | `131/201` | `-30` |
| `rank_bottom70` | `True` | `123/201` | `-38` |
| `right_surprisal_lt3` | `True` | `112/201` | `-49` |
| `rank_top10` | `True` | `110/201` | `-51` |
| `rank_top20` | `False` | `110/201` | `-51` |
| `delta_lt1` | `True` | `106/201` | `-55` |
| `right_surprisal_ge4` | `False` | `102/201` | `-59` |
| `right_surprisal_ge4` | `True` | `99/201` | `-62` |

## Decision

- Promotes boundary type rule: `False`.
- The boundary surprisal clue localizes cutpoints, but does not explain next operation type.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
