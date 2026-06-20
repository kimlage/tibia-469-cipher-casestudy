# Expanded Negative Control Suite

Verdict: `partial_negative_control_suite`. Translation delta: `NONE`.

This expands the negative-control inventory and refuses to fabricate
numeric strings for lore-only controls.

| Control | Status | Coverage | p_ge |
|---|---|---:|---:|
| `avar_tar` | `tested` | 0.087 | 0.4850 |
| `your_true_colour` | `tested` | 0.000 | 1.0000 |
| `secret_library_74032_45331` | `tested` | 0.000 | 1.0000 |
| `honeminas_vectors` | `tested` | 0.000 | 1.0000 |
| `spirit_grounds_gate_keeper` | `blocked_missing_numeric_source` |  |  |
| `paradox_mirror` | `blocked_missing_numeric_source` |  |  |
| `evil_mastermind_dictionary` | `blocked_missing_numeric_source` |  |  |

Stop rule: control overlap never becomes positive semantic evidence.
