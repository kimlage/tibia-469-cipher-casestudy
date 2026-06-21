# Source Interval Cost Gate

Classification: `source_interval_cost_weak_clue_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 53 prices the observable source-interval weak clue against
the gate-41 residual lookup. A rule must pay for rule selection,
clean rollbacks, and remaining residual misses in the full decision
universe before it can
be credited as reducing ad hoc explanation.

## Summary

- Baseline residual lookup: `79.361` bits.
- Decision universe: `267`.
- Source-branch decision universe: `234`.
- Residual total: `10`.
- Rule count: `30504`.
- Rule ID bits: `14.897`.
- Best priced model: `best_observable_zero_fp_rule`.
- Best priced model bits: `79.230`.
- Best priced net vs lookup: `-0.131`.
- Weak cost reduction before holdout: `True`.

## Cost Rows

| Model | Residual hits | Residual misses | Clean false changes | Total bits | Net vs lookup |
|---|---:|---:|---:|---:|---:|
| `best_observable_full_fit_rule` | `5` | `5` | `4` | `82.771` | `3.410` |
| `best_observable_zero_fp_rule` | `2` | `8` | `0` | `79.230` | `-0.131` |

## Decision

- Promotes source-interval cost rule: `False`.
- Gate 53 prices the observable source-interval weak clue against the gate-41 residual lookup after charging for rule selection, clean rollbacks, and remaining residual misses in the full decision universe.
- The source-interval clue remains audit-only: any small priced saving is not a parser rule without clean holdout and broad residual coverage.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
