# Residual Burden Cross-Prediction Gate

Classification: `WEAK_RESIDUAL_BURDEN_CROSS_PREDICTION`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether leave-one-field-out residual modes predict each held-out burden field after paying the mode header.

## Summary

| Target | Conditional saving before header | Header bits | Saving after header | Shuffled p95 | Beats p95 |
| --- | ---: | ---: | ---: | ---: | --- |
| `literal_digit_class` | `68.293` | `855.474` | `-787.181` | `-856.500` | `True` |
| `copy_hint_bits_class` | `160.010` | `799.929` | `-639.919` | `-793.216` | `True` |
| `composition_bits_class` | `166.167` | `870.041` | `-703.874` | `-856.209` | `True` |

## Decision

Promotion requires positive saving after header and shuffled-target p95. Conditional savings before header are retained only as weak coupling diagnostics.
