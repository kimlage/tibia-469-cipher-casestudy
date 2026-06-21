# Structural Vote Residual Decomposition

Classification: `structural_vote_residual_decomposition_audit_only`
Translation delta: `NONE`

## Purpose

Gate 35 decomposes the rejected weak-signal consensus front. Instead of
proposing another policy, it asks whether the residual decisions share a hidden
vote pattern across the structural families already tested:

- local/global source-state continuity;
- phase/grid alignment;
- future-copy opportunity;
- recurrent target boundary.

## Summary

- Decisions: `234`.
- Residual first-drift decisions: `10`.
- Clean controls: `224`.
- Structural votes per decision: `8`.
- Residual stable-support histogram:
  `{0: 2, 2: 6, 3: 1, 4: 1}`.
- Clean top-nonactive-support histogram:
  `{0: 3, 1: 82, 2: 121, 3: 17, 4: 1}`.
- Residuals with stable support `>=1/2/3`:
  `8/`
  `8/`
  `2`.
- Clean rows with non-active support `>=2/3`:
  `139/`
  `18`.

## Threshold Diagnostic

| threshold | triggered total | triggered residual | stable residual | false clean | stable residual books |
| --- | --- | --- | --- | --- | --- |
| 1 | 231 | 10 | 5 | 221 | [16, 21, 34, 39, 57] |
| 2 | 149 | 10 | 5 | 139 | [16, 21, 34, 39, 57] |
| 3 | 20 | 2 | 2 | 18 | [16, 39] |
| 4 | 2 | 1 | 1 | 1 | [39] |

## Residual Rows

| book | target_start | drift_class | stable support | active support | top nonactive support | top nonactive stable | stable support by family |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | 0 | literal_understop | 0 | 4 | 2 | False | {'boundary': 0, 'future': 0, 'phase': 0, 'source': 0} |
| 16 | 164 | copy_started_inside_stable_literal | 3 | 4 | 3 | True | {'boundary': 1, 'future': 2, 'phase': 0, 'source': 0} |
| 20 | 21 | internal_copy_missed_as_literal | 2 | 1 | 2 | False | {'boundary': 0, 'future': 0, 'phase': 0, 'source': 2} |
| 21 | 0 | book_start_copy_missed_as_literal | 2 | 4 | 2 | True | {'boundary': 0, 'future': 0, 'phase': 0, 'source': 2} |
| 26 | 0 | book_start_copy_missed_as_literal | 2 | 2 | 2 | False | {'boundary': 0, 'future': 0, 'phase': 0, 'source': 2} |
| 34 | 105 | internal_copy_missed_as_literal | 2 | 4 | 2 | True | {'boundary': 0, 'future': 0, 'phase': 0, 'source': 2} |
| 39 | 0 | book_start_copy_missed_as_literal | 4 | 2 | 4 | True | {'boundary': 0, 'future': 0, 'phase': 2, 'source': 2} |
| 45 | 62 | internal_copy_missed_as_literal | 2 | 2 | 2 | False | {'boundary': 0, 'future': 0, 'phase': 0, 'source': 2} |
| 55 | 67 | copy_length_drift_same_source | 0 | 4 | 2 | False | {'boundary': 0, 'future': 0, 'phase': 0, 'source': 0} |
| 57 | 69 | literal_understop | 2 | 4 | 2 | True | {'boundary': 0, 'future': 2, 'phase': 0, 'source': 0} |

## Decision

- Promotes structural vote rule: `False`.
- The weak-signal front has no hidden clean threshold: residual support and
  clean-control risk overlap.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
