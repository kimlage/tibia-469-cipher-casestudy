# Post-Midpoint Alpha1 Context Alpha Grid

Verdict: `post_midpoint_alpha_by_context_not_promoted`. Translation delta: `NONE`.

This audit tests whether the fixed book-midpoint copy-length context
needs separate smoothing parameters for `first_half` and `second_half`.
The recipe, source-address ledger, copy order, payload model, item-type
model, forced rules, book-length ledger, and midpoint context are fixed.

## Top Alpha Models

| Rank | Model | First alpha | Second alpha | Length bits | Model bits | Total bits | Delta vs current | Component delta |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `1` | `active_shared_alpha1_midpoint_context` | `1` | `1` | `1631.494` | `12` | `8572.267` | `0.000` | `0.000` |
| `2` | `midpoint_alpha_by_context_grid` | `1` | `2` | `1629.883` | `15` | `8573.656` | `1.389` | `-1.611` |
| `3` | `midpoint_alpha_by_context_grid` | `1` | `1` | `1631.494` | `15` | `8575.267` | `3.000` | `0.000` |
| `4` | `midpoint_alpha_by_context_grid` | `1` | `3` | `1630.405` | `17` | `8576.178` | `3.911` | `-1.089` |
| `5` | `midpoint_alpha_by_context_grid` | `1` | `4` | `1631.059` | `17` | `8576.832` | `4.565` | `-0.435` |
| `6` | `midpoint_alpha_by_context_grid` | `1` | `5` | `1631.630` | `17` | `8577.403` | `5.136` | `0.136` |
| `7` | `midpoint_alpha_by_context_grid` | `2` | `2` | `1633.634` | `15` | `8577.407` | `5.140` | `2.140` |
| `8` | `midpoint_alpha_by_context_grid` | `1` | `6` | `1632.104` | `17` | `8577.877` | `5.610` | `0.610` |
| `9` | `midpoint_alpha_by_context_grid` | `2` | `1` | `1635.245` | `15` | `8579.018` | `6.751` | `3.751` |
| `10` | `midpoint_alpha_by_context_grid` | `2` | `3` | `1634.156` | `17` | `8579.929` | `7.662` | `2.662` |
| `11` | `midpoint_alpha_by_context_grid` | `1` | `7` | `1632.495` | `19` | `8580.268` | `8.001` | `1.001` |
| `12` | `midpoint_alpha_by_context_grid` | `2` | `4` | `1634.811` | `17` | `8580.583` | `8.316` | `3.316` |
| `13` | `midpoint_alpha_by_context_grid` | `1` | `8` | `1632.821` | `19` | `8580.594` | `8.327` | `1.327` |
| `14` | `midpoint_alpha_by_context_grid` | `1` | `9` | `1633.096` | `19` | `8580.868` | `8.601` | `1.601` |
| `15` | `midpoint_alpha_by_context_grid` | `1` | `10` | `1633.329` | `19` | `8581.102` | `8.835` | `1.835` |
| `16` | `midpoint_alpha_by_context_grid` | `2` | `5` | `1635.382` | `17` | `8581.155` | `8.888` | `3.888` |
| `17` | `midpoint_alpha_by_context_grid` | `1` | `11` | `1633.531` | `19` | `8581.304` | `9.037` | `2.037` |
| `18` | `midpoint_alpha_by_context_grid` | `1` | `12` | `1633.706` | `19` | `8581.479` | `9.212` | `2.212` |
| `19` | `midpoint_alpha_by_context_grid` | `2` | `6` | `1635.855` | `17` | `8581.628` | `9.361` | `4.361` |
| `20` | `midpoint_alpha_by_context_grid` | `1` | `13` | `1633.859` | `19` | `8581.632` | `9.365` | `2.365` |

## Best Context-Specific Alpha Row

- First-half alpha: `1`
- Second-half alpha: `2`
- Total bits: `8573.656`
- Delta vs current: `1.389`
- Component delta: `-1.611`
- Declaration delta: `3`

## Interpretation

Context-specific alphas are promoted only if their component savings
survive the extra declaration cost. Otherwise the active shared
`alpha=1` midpoint context remains the current formula.

## Boundary

This is a mechanical smoothing-parameter audit only. It does not alter
row0, introduce plaintext, or make an authorial-intent claim.
