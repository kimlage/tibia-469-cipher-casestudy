# Recipe Reparse Train-Set Multi-Cutoff Control

Classification: `recipe_reparse_numeric_prefix_not_unique_multicutoff`
Translation delta: `NONE`

## Purpose

Audit 128 tested random same-size train inventories only at cutoff `50`.
This audit expands the same train/test contract to cutoffs
`35/50/60`: train on a same-size inventory, reparse the complementary
test set in numeric order, and compare gain versus raw digit coding.

## Result

| Cutoff | Observed gain | Random mean | Random max | p(random >= observed) | Mean win | Max win |
|---:|---:|---:|---:|---:|---|---|
| `35` | `17163.556` | `16277.545` | `17009.367` | `0.2000` | `True` | `True` |
| `50` | `10441.679` | `9100.669` | `10241.584` | `0.2000` | `True` | `True` |
| `60` | `4467.255` | `4564.670` | `5094.518` | `0.6000` | `False` | `False` |

## Decision

- Numeric prefix beats random-train mean at `2/3` cutoffs.
- Numeric prefix beats random-train max at `2/3` cutoffs.
- Unique at control resolution: `2/3` cutoffs.
- The recipe-reparse signal remains predictive, but numeric order is not promoted as final authorial proof.
- No plaintext, translation, row0-origin change, or case reopening is introduced.
