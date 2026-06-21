# Hierarchical Context Backoff Audit

Classification: `hierarchical_context_backoff_rejected`
Translation delta: `NONE`

## Purpose

Gate 26 tests whether the gate-25 instability is only a sparsity
problem. It trains observable context hierarchies and backs off to
coarser contexts when support is low.

## Full-Fit Scoreboard

- Families tested: `4`.
- Support thresholds: `5`.

| Family | Min support | Total hits | Residual hits | Clean false changes |
|---|---:|---:|---:|---:|
| `start_active_to_combo` | `1` | `229/234` | `5/10` | `0` |
| `length_to_combo` | `1` | `229/234` | `5/10` | `0` |
| `coarse_to_combo` | `1` | `229/234` | `5/10` | `0` |
| `branch_to_combo` | `1` | `229/234` | `5/10` | `0` |
| `length_to_combo` | `2` | `229/234` | `5/10` | `0` |
| `length_to_combo` | `3` | `229/234` | `5/10` | `0` |
| `length_to_combo` | `5` | `229/234` | `5/10` | `0` |
| `start_active_to_combo` | `2` | `228/234` | `5/10` | `1` |
| `coarse_to_combo` | `2` | `228/234` | `5/10` | `1` |
| `branch_to_combo` | `2` | `228/234` | `5/10` | `1` |
| `start_active_to_combo` | `3` | `228/234` | `5/10` | `1` |
| `coarse_to_combo` | `3` | `228/234` | `5/10` | `1` |

## Prefix/Holdout

| Cutoff | Family | Support | Test hits | Test residual hits | Test clean false changes |
|---:|---|---:|---:|---:|---:|
| `20` | `start_active_to_combo` | `1` | `151/163` | `3/8` | `7` |
| `30` | `start_active_to_combo` | `1` | `122/130` | `3/5` | `6` |
| `40` | `start_active_to_combo` | `1` | `82/88` | `2/3` | `5` |
| `50` | `start_active_to_combo` | `1` | `48/50` | `1/2` | `1` |
| `60` | `start_active_to_combo` | `1` | `20/20` | `0/0` | `0` |

## Decision

- Promotes hierarchical context backoff: `False`.
- Best full-fit family/support: `start_active_to_combo` / `1`.
- Best full-fit residual hits: `5/10`.
- Best full-fit clean false changes: `0`.
- Prequential zero-clean-false-change cells: `1/5`.
- Prequential cover-all-test-residual cells: `1/5`.
- Gate 26 tests whether gate25 failed only because context_combo was too sparse. It trains a hierarchy of observable contexts and backs off to coarser contexts when support is low.
- Hierarchical backoff does not turn the contextual clue into a stable parser rule.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
