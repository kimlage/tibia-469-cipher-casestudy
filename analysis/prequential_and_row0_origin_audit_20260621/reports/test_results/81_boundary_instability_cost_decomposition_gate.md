# Boundary Instability Cost Decomposition Gate

Classification: `boundary_instability_driven_by_learned_cost_components`
Translation delta: `NONE`

## Purpose

Gate 80 rejected simple invariant boundary policies. This gate asks
which learned cost components actually separate each per-cutoff parser
winner from the other observed variants of the same unstable book.

## Summary

- Unstable books tested: `12`.
- Variant-vs-winner comparisons: `47`.
- Total regret bits across comparisons: `40.698223`.
- Mean regret bits: `0.865920`.
- Dominant component counts: `{'copy_length': 30, 'literal_payload': 4, 'copy_source_exception': 12, 'copy_source_flag': 1}`.

## Positive Delta Totals

| Component | Positive delta bits | Signed delta bits |
|---|---:|---:|
| item_type | 1.320799 | -0.768505 |
| copy_source_flag | 5.903485 | -5.237935 |
| copy_source_exception | 40.867886 | 11.056559 |
| copy_length | 41.521526 | 19.054955 |
| literal_payload | 54.203064 | 16.593149 |
| literal_length | 5.000000 | 0.000000 |

## Largest Regret Comparisons

| Book | Cutoff | Regret bits | Dominant component |
|---:|---:|---:|---|
| 61 | 60 | 3.831839 | `copy_length` |
| 61 | 50 | 2.856456 | `copy_source_exception` |
| 30 | 20 | 2.777311 | `copy_source_exception` |
| 56 | 50 | 2.238461 | `copy_length` |
| 65 | 50 | 2.211789 | `copy_length` |
| 35 | 20 | 1.966829 | `copy_source_exception` |
| 51 | 50 | 1.936007 | `copy_length` |
| 39 | 10 | 1.384835 | `literal_payload` |
| 65 | 60 | 1.222118 | `copy_length` |
| 65 | 35 | 1.110496 | `copy_source_exception` |

## Decision

- The remaining boundary choices are being selected by the learned coding streams rather than by a simple invariant boundary rule. Component deltas localize which streams most often make the losing observed variants more expensive than the per-cutoff parser winner.
- No compression-bound change is introduced.
- No corpus-wide formula promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
