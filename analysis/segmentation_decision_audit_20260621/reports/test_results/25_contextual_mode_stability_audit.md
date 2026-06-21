# Contextual Mode Stability Audit

Classification: `contextual_mode_stability_rejected`
Translation delta: `NONE`

## Purpose

Gate 25 stress-tests the gate-24 `context_combo` clue. It asks
whether the full-fit `5/10` residual gain survives support pruning,
leave-one-book retraining, and leave-context-out retraining.

## Support Thresholds

| Min support | Mapped contexts | Total hits | Residual hits | Clean false changes |
|---:|---:|---:|---:|---:|
| `1` | `30` | `229/234` | `5/10` | `0` |
| `2` | `24` | `227/234` | `3/10` | `0` |
| `3` | `18` | `225/234` | `1/10` | `0` |
| `5` | `11` | `225/234` | `1/10` | `0` |
| `10` | `5` | `225/234` | `1/10` | `0` |

## Residual Stability

| Book | Class | Context support | Full hit | Leave-book hit | Leave-context hit |
|---:|---|---:|---|---|---|
| `14` | `literal_understop` | `1` | `False` | `False` | `False` |
| `16` | `copy_started_inside_stable_literal` | `4` | `False` | `False` | `False` |
| `20` | `internal_copy_missed_as_literal` | `6` | `False` | `False` | `False` |
| `21` | `book_start_copy_missed_as_literal` | `2` | `False` | `False` | `False` |
| `26` | `book_start_copy_missed_as_literal` | `1` | `True` | `False` | `False` |
| `34` | `internal_copy_missed_as_literal` | `11` | `False` | `False` | `False` |
| `39` | `book_start_copy_missed_as_literal` | `2` | `True` | `False` | `False` |
| `45` | `internal_copy_missed_as_literal` | `1` | `True` | `False` | `False` |
| `55` | `copy_length_drift_same_source` | `63` | `True` | `True` | `False` |
| `57` | `literal_understop` | `2` | `True` | `False` | `False` |

## Decision

- Promotes contextual mode stability: `False`.
- Full-fit residual hits: `5/10`.
- Leave-one-book residual hits: `1/10`.
- Leave-context-out residual hits: `0/10`.
- Full-fit clean false changes: `0`.
- Gate 25 stress-tests the gate24 context_combo clue by pruning low-support contexts and by leave-one-book / leave-context-out retraining. Stable labels are used only to train/evaluate the mode table.
- The context signal remains a weak full-fit clue, not a stable parser rule.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
