# Final Residual Burden Cross-Prediction Audit

Status: `analysis_only`
Classification: `WEAK_RESIDUAL_BURDEN_CROSS_PREDICTION`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Do the other residual burden fields predict each held-out burden field well enough to reduce that field after paying a leave-one-field-out mode header?

## Result

Promoted targets: `[]`. Weak targets: `['literal_digit_class', 'copy_hint_bits_class', 'composition_bits_class']`.

| Target | Before-header saving | After-header saving | Shuffled p95 |
| --- | ---: | ---: | ---: |
| `literal_digit_class` | `68.293` | `-787.181` | `-856.500` |
| `copy_hint_bits_class` | `160.010` | `-639.919` | `-793.216` |
| `composition_bits_class` | `166.167` | `-703.874` | `-856.209` |

## Decision

This is not a generator and does not reduce exact executable tapes unless a target promotes after header cost. Row0, plaintext, translation, and compression_bound remain unchanged.

## Reproducible Artifacts

- [01_residual_burden_cross_prediction_gate.py](../scripts/01_residual_burden_cross_prediction_gate.py)
- [01_residual_burden_cross_prediction_gate.json](test_results/01_residual_burden_cross_prediction_gate.json)
- [01_residual_burden_cross_prediction_gate.md](test_results/01_residual_burden_cross_prediction_gate.md)
