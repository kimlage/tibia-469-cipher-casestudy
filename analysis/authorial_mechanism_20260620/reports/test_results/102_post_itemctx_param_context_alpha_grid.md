# Post-Itemctx Param Context Alpha Grid

Verdict: `post_itemctx_param_alpha_by_context_not_promoted`. Translation delta: `NONE`.

This audit tests whether the fixed book-midpoint copy-length context
needs separate smoothing parameters after the itemctx_param promotion.
The recipe, source-address ledger, copy order, payload model, item-type
model, forced rules, book-length ledger, and midpoint context are fixed.

## Top Alpha Models

| Rank | Model | Alpha by context | Total bits | Delta | Component delta | Declaration delta |
|---:|---|---|---:|---:|---:|---:|
| `1` | `active_shared_alpha1_midpoint_context` | `{'first_half': 1, 'second_half': 1}` | `8561.792` | `0.000` | `0.000` | `0` |
| `2` | `midpoint_alpha_by_context_grid` | `{'first_half': 1, 'second_half': 2}` | `8563.181` | `1.389` | `-1.611` | `3` |
| `3` | `midpoint_alpha_by_context_grid` | `{'first_half': 1, 'second_half': 1}` | `8564.792` | `3.000` | `0.000` | `3` |
| `4` | `midpoint_alpha_by_context_grid` | `{'first_half': 1, 'second_half': 3}` | `8565.703` | `3.911` | `-1.089` | `5` |
| `5` | `midpoint_alpha_by_context_grid` | `{'first_half': 1, 'second_half': 4}` | `8566.357` | `4.565` | `-0.435` | `5` |
| `6` | `midpoint_alpha_by_context_grid` | `{'first_half': 1, 'second_half': 5}` | `8566.928` | `5.136` | `0.136` | `5` |
| `7` | `midpoint_alpha_by_context_grid` | `{'first_half': 2, 'second_half': 2}` | `8566.932` | `5.140` | `2.140` | `3` |
| `8` | `midpoint_alpha_by_context_grid` | `{'first_half': 1, 'second_half': 6}` | `8567.402` | `5.610` | `0.610` | `5` |
| `9` | `midpoint_alpha_by_context_grid` | `{'first_half': 2, 'second_half': 1}` | `8568.543` | `6.751` | `3.751` | `3` |
| `10` | `midpoint_alpha_by_context_grid` | `{'first_half': 2, 'second_half': 3}` | `8569.454` | `7.662` | `2.662` | `5` |
| `11` | `midpoint_alpha_by_context_grid` | `{'first_half': 1, 'second_half': 7}` | `8569.793` | `8.001` | `1.001` | `7` |
| `12` | `midpoint_alpha_by_context_grid` | `{'first_half': 2, 'second_half': 4}` | `8570.108` | `8.316` | `3.316` | `5` |

## Interpretation

A context-specific alpha row is promoted only if component savings exceed
the extra declaration cost. The shared `alpha=1` midpoint context remains
the current formula when no declared row beats it.

## Boundary

This is a mechanical smoothing-parameter audit only. It does not alter
row0, introduce plaintext, or make an authorial-intent claim.
