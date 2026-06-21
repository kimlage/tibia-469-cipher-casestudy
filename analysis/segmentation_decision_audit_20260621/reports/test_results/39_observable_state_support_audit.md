# Observable State Support Audit

Classification: `observable_state_support_boundary_audit_only`
Translation delta: `NONE`

## Purpose

Gate 39 diagnoses why the residual first-drift decisions are not solved by
nearest trajectory reuse. It asks whether each residual state is outside the
observed exact-book support, deterministically contradicted by exact examples,
or ambiguously supported.

This is not a new parser and not a compression sweep.

## Summary

- Exact parser books: `50`.
- Residual parser books: `10`.
- Families tested: `['trajectory', 'context', 'combined']`.
- Best exact-label family: `trajectory`.
- Deterministic exact-label matches:
  `0/10`.
- Supported residual states at best family:
  `4/10`.
- Contradictory residual states at best family:
  `2`.
- Prequential cells with deterministic match:
  `0/4`.
- Promotes parser rule: `False`.

## Exact Label Full Fit

| family | queries | supported | deterministic matches | contradictions | ambiguous with stable | status counts |
| --- | --- | --- | --- | --- | --- | --- |
| trajectory | 10 | 4 | 0 | 2 | 2 | {'ambiguous_excludes_stable': 2, 'ambiguous_includes_stable': 2, 'out_of_support': 6} |
| context | 10 | 2 | 0 | 1 | 1 | {'ambiguous_includes_stable': 1, 'deterministic_contradiction': 1, 'out_of_support': 8} |
| combined | 10 | 0 | 0 | 0 | 0 | {'out_of_support': 10} |

## Type-Only Label Full Fit

| family | supported | deterministic matches | contradictions | status counts |
| --- | --- | --- | --- | --- |
| trajectory | 4 | 0 | 0 | {'ambiguous_includes_stable': 4, 'out_of_support': 6} |
| context | 2 | 1 | 1 | {'deterministic_contradiction': 1, 'deterministic_match': 1, 'out_of_support': 8} |
| combined | 0 | 0 | 0 | {'out_of_support': 10} |

## Prequential Rows For Best Exact Family

| cutoff | queries | supported | deterministic matches | status counts |
| --- | --- | --- | --- | --- |
| 20 | 8 | 3 | 0 | {'ambiguous_excludes_stable': 3, 'out_of_support': 5} |
| 30 | 5 | 1 | 0 | {'ambiguous_excludes_stable': 1, 'out_of_support': 4} |
| 40 | 3 | 0 | 0 | {'out_of_support': 3} |
| 50 | 2 | 0 | 0 | {'out_of_support': 2} |
| 60 | 0 | 0 | 0 | {} |

## Residual Rows For Best Exact Family

| book | op | drift class | active label | stable label | support | label count | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | 0 | literal_understop | ('literal', 27) | ('literal', 39) | 50 | 39 | ambiguous_excludes_stable |
| 16 | 9 | copy_started_inside_stable_literal | ('copy', 8) | ('literal', 1) | 0 | 0 | out_of_support |
| 20 | 2 | internal_copy_missed_as_literal | ('literal', 3) | ('copy', 10) | 0 | 0 | out_of_support |
| 21 | 0 | book_start_copy_missed_as_literal | ('literal', 7) | ('copy', 9) | 50 | 39 | ambiguous_includes_stable |
| 26 | 0 | book_start_copy_missed_as_literal | ('literal', 1) | ('copy', 11) | 50 | 39 | ambiguous_includes_stable |
| 34 | 7 | internal_copy_missed_as_literal | ('literal', 5) | ('copy', 5) | 0 | 0 | out_of_support |
| 39 | 0 | book_start_copy_missed_as_literal | ('literal', 7) | ('copy', 5) | 50 | 39 | ambiguous_excludes_stable |
| 45 | 1 | internal_copy_missed_as_literal | ('literal', 1) | ('copy', 8) | 0 | 0 | out_of_support |
| 55 | 2 | copy_length_drift_same_source | ('copy', 45) | ('copy', 44) | 0 | 0 | out_of_support |
| 57 | 2 | literal_understop | ('literal', 17) | ('literal', 28) | 0 | 0 | out_of_support |

## Decision

Observable-state support does not promote a parser. No tested observable state
family gives deterministic exact-label matches for the residual first-drift
choices. The residuals are either outside the exact-book state support or land
in states whose exact-book labels do not determine the needed stable operation.

The next blocker is a real latent state or a source-free target digit account,
not another nearest-state reuse rule over the currently exposed features.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
