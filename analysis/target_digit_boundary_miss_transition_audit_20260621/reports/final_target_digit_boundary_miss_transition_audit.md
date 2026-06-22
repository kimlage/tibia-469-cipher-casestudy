# Final Target Digit Boundary Miss Transition Audit

Status: `analysis_only`
Classification: `TARGET_DIGIT_BOUNDARY_MISS_TRANSITION_CLASSES_REJECTED_CONTROL`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Are the cutpoints missed by `right_ge:4` explained by skeleton transition
classes, length buckets, ordinal position, or chunk recurrence?

## Result

- Cutpoints/hits/misses: `201` / `94` / `107`.
- Features tested: `15`.
- Baseline miss-label atlas: `196.243` bits.
- Best feature: `shape` with `20` categories.
- Best saving before/after feature charge: `39.806` / `35.900` bits.
- Random relabel p95 before feature charge: `44.763` bits.
- Beats random p95: `False`.
- Prefix-selected positive test cells: `5/5`.

The feature audit rejects this path as a promoted explanation. The best
skeleton-conditioned feature is not above random relabel p95, and chunk
recurrence features are too sparse to explain the missed cutpoints.

## Decision

- Miss transition/chunk feature is rejected as a promoted clue.
- Endpoint generator is not promoted.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Target digit boundary miss transition gate](test_results/01_target_digit_boundary_miss_transition_gate.md)
