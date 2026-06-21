# Observable Decision Tree Policy Audit

Classification: `observable_decision_tree_policy_rejected`
Translation delta: `NONE`

## Purpose

Gate 27 tests whether the post-repair residual branch choice can be generated
by a small observable decision tree rather than by a flat context table, single
feature flag, or learned linear ranker. Each leaf chooses one non-oracle
branch-continuation objective. Stable projection labels are used for training
and evaluation only, not as tree features.

## Summary

- Decisions: `234`.
- Residual first-drift decisions: `10`.
- Clean controls: `224`.
- Observable predicates: `45`.
- Tree grid size: `9`.
- Active baseline: `224/234`, residual
  `0/10`, clean false changes
  `0`.
- Best tree: `228/234`, residual
  `4/10`, clean false changes
  `0`, depth `3`, nodes
  `9`.

## Full-Fit Grid

| max depth | min leaf | actual depth | nodes | total hits | residual hits | clean false changes | residual misses |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 1 | 3 | 9 | 228/234 | 4/10 | 0 | [14, 16, 20, 21, 34, 39] |
| 3 | 2 | 3 | 9 | 228/234 | 4/10 | 0 | [14, 16, 20, 21, 34, 39] |
| 2 | 1 | 2 | 7 | 227/234 | 4/10 | 1 | [14, 16, 20, 21, 34, 39] |
| 2 | 2 | 2 | 7 | 227/234 | 4/10 | 1 | [14, 16, 20, 21, 34, 39] |
| 2 | 5 | 2 | 7 | 227/234 | 4/10 | 1 | [14, 16, 20, 21, 34, 39] |
| 3 | 5 | 2 | 7 | 227/234 | 4/10 | 1 | [14, 16, 20, 21, 34, 39] |
| 1 | 1 | 1 | 3 | 225/234 | 2/10 | 1 | [14, 16, 20, 21, 26, 34, 39, 45] |
| 1 | 2 | 1 | 3 | 225/234 | 2/10 | 1 | [14, 16, 20, 21, 26, 34, 39, 45] |

Best tree:

```json
{
  "else": {
    "else": {
      "leaf": "active_branch"
    },
    "if": "later_op",
    "then": {
      "leaf": "balanced_ops_literals"
    }
  },
  "if": "active_len_le13",
  "then": {
    "else": {
      "leaf": "active_branch"
    },
    "if": "active_len_le1",
    "then": {
      "else": {
        "leaf": "min_suffix_literals"
      },
      "if": "branch_count_mid_or_less",
      "then": {
        "leaf": "active_branch"
      }
    }
  }
}
```

## Prefix/Holdout

| cutoff | depth | min leaf | train hits | test hits | test residual hits | test clean false changes | matches oracle |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | 1 | 1 | 69/71 | 155/163 | 0/8 | 0 | False |
| 30 | 2 | 1 | 100/104 | 125/130 | 0/5 | 0 | False |
| 40 | 2 | 1 | 140/146 | 85/88 | 0/3 | 0 | False |
| 50 | 2 | 1 | 178/184 | 48/50 | 0/2 | 0 | False |
| 60 | 3 | 1 | 208/214 | 20/20 | 0/0 | 0 | True |

## Permutation Control

- Controls: `30`.
- Total-hit range under random stable-branch labels:
  `19..31`.
- Median total hits under controls: `24`.
- Max residual hits under controls: `4`.
- Minimum clean false changes under controls: `195`.
- `p(total_hits >= real_best)`: `0.032258`.
- `p(residual_hits >= real_best)`: `0.129032`.

## Decision

- Promotes observable decision-tree parser policy:
  `False`.
- Prequential zero-clean-false-change cells:
  `5/5`.
- Prequential cover-all-test-residual cells:
  `1/5`.
- Gate 27 is stronger than the previous single-feature/context checks, but it
  still fails the promotion gate if residual recovery requires false clean-control
  changes or does not survive prefix/holdout selection.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
