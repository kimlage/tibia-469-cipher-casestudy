# Contextual Mode Selector Audit

Classification: `contextual_mode_selector_rejected`
Translation delta: `NONE`

## Purpose

Gate 24 tests whether the missing path-state choice is a small
finite mode table: observable context chooses one non-oracle branch
objective. The table is learned from prefix/stable labels and
evaluated on future books.

## Full-Fit Scoreboard

- Decisions: `234`.
- Context families: `10`.

| Context family | Contexts | Total hits | Residual hits | Clean false changes |
|---|---:|---:|---:|---:|
| `context_combo` | `30` | `229/234` | `5/10` | `0` |
| `index_x_active_len` | `10` | `227/234` | `5/10` | `2` |
| `active_type_len` | `9` | `225/234` | `5/10` | `4` |
| `start_x_active_type` | `4` | `224/234` | `0/10` | `0` |
| `start_internal` | `2` | `224/234` | `0/10` | `0` |
| `op_index` | `2` | `224/234` | `0/10` | `0` |
| `global` | `1` | `224/234` | `0/10` | `0` |
| `branch_count` | `3` | `224/234` | `0/10` | `0` |
| `baseline_to_active` | `2` | `224/234` | `0/10` | `0` |
| `active_type` | `2` | `224/234` | `0/10` | `0` |

## Prefix/Holdout

| Cutoff | Selected context | Test hits | Test residual hits | Test clean false changes | Unseen contexts |
|---:|---|---:|---:|---:|---:|
| `20` | `start_x_active_type` | `154/163` | `0/8` | `1` | `0` |
| `30` | `index_x_active_len` | `125/130` | `2/5` | `2` | `0` |
| `40` | `context_combo` | `81/88` | `1/3` | `5` | `3` |
| `50` | `context_combo` | `48/50` | `1/2` | `1` | `0` |
| `60` | `context_combo` | `20/20` | `0/0` | `0` | `0` |

## Decision

- Promotes contextual mode selector: `False`.
- Active baseline total/residual hits: `224/234` and `0/10`.
- Best full-fit context: `context_combo`.
- Best full-fit residual hits: `5/10`.
- Best full-fit clean false changes: `0`.
- Prequential zero-clean-false-change cells: `1/5`.
- Prequential cover-all-test-residual cells: `1/5`.
- Gate 24 tests a finite observable state table: each context family learns which non-oracle branch objective to use from prefix stable labels, then is evaluated on suffix books.
- The finite context selector does not become a generative parser.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
