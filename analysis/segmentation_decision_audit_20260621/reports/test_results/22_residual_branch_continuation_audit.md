# Residual Branch Continuation Audit

Classification: `residual_branch_continuation_objectives_rejected`
Translation delta: `NONE`

## Purpose

Gate 22 tests the next path-state hypothesis after simple feature
flags failed: perhaps the stable residual operation is selected by
how the active parser continues after a forced first branch.
Stable projection is used only as the evaluation label; non-oracle
objectives may choose only observable local branches.

## Branch Availability

- Active classifier: `if_peak_len_le5_then_skip_to_next_peak_ge5`.
- Residual decisions: `10`.
- Clean controls: `224`.
- Residual stable operations available as observable candidates: `10/10`.
- Clean stable operations available as observable candidates: `224/224`.

## Objective Scoreboard

| Objective | Residual hits | Clean false changes | Total hits |
|---|---:|---:|---:|
| `oracle_max_stable_prefix` | `10/10` | `0` | `234/234` |
| `balanced_ops_literals` | `6/10` | `20` | `210/234` |
| `max_suffix_copy_digits` | `5/10` | `20` | `209/234` |
| `min_suffix_literals` | `5/10` | `20` | `209/234` |
| `max_suffix_copy_count` | `4/10` | `155` | `73/234` |
| `min_suffix_ops` | `0/10` | `174` | `50/234` |

## Prefix/Holdout

| Cutoff | Selected objective | Test residual hits | Test clean false changes | Oracle objective |
|---:|---|---:|---:|---|
| `20` | `min_suffix_literals` | `5/8` | `13` | `balanced_ops_literals` |
| `30` | `min_suffix_literals` | `4/5` | `11` | `balanced_ops_literals` |
| `40` | `min_suffix_literals` | `2/3` | `8` | `balanced_ops_literals` |
| `50` | `min_suffix_literals` | `1/2` | `4` | `balanced_ops_literals` |
| `60` | `balanced_ops_literals` | `0/0` | `1` | `min_suffix_literals` |

## Residual Branch Rows

| Book | Class | Target | Stable candidate? | Branches |
|---:|---|---:|---|---:|
| `14` | `literal_understop` | `0` | `True` | `19` |
| `16` | `copy_started_inside_stable_literal` | `164` | `True` | `9` |
| `20` | `internal_copy_missed_as_literal` | `21` | `True` | `24` |
| `21` | `book_start_copy_missed_as_literal` | `0` | `True` | `26` |
| `26` | `book_start_copy_missed_as_literal` | `0` | `True` | `22` |
| `34` | `internal_copy_missed_as_literal` | `105` | `True` | `13` |
| `39` | `book_start_copy_missed_as_literal` | `0` | `True` | `24` |
| `45` | `internal_copy_missed_as_literal` | `62` | `True` | `25` |
| `55` | `copy_length_drift_same_source` | `67` | `True` | `20` |
| `57` | `literal_understop` | `69` | `True` | `20` |

## Decision

- Promotes branch-continuation rule: `False`.
- Best non-oracle objective: `balanced_ops_literals`.
- Best non-oracle residual hits: `6/10`.
- Best non-oracle clean false changes: `20`.
- Oracle-prefix diagnostic residual hits: `10/10`.
- Prequential zero-clean-false-change cells: `0/5`.
- Prequential cover-all-test-residual cells: `1/5`.
- Gate 22 tests whether residual choices become mechanical when candidate first operations are scored by their active-parser continuation. Stable projection is used only as the scoring label; non-oracle objectives may select only observable branches.
- Observable continuation objectives do not recover the residual stable choices without damaging clean controls.
- The remaining blocker is not just first-branch consequence under these simple path metrics.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
