# Final Target Digit Boundary Miss Residual Audit

Status: `analysis_only`
Classification: `TARGET_DIGIT_BOUNDARY_MISS_RESIDUAL_WEAK_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Can the cutpoints missed by the promoted `right_ge:4` boundary threshold
be captured by a second-stage source-free residual candidate rule?

## Result

- Primary policy: `right_ge:4`.
- Residual policies tested: `93`.
- Best residual policy: `near_primary:1`.
- Threshold gate saving after policy charge: `645.694` bits.
- Residual saving after primary+residual policy charge: `715.155` bits.
- Delta vs threshold: `69.462` bits.
- Random residual delta p95: `49.103` bits.
- Outside actual cutpoints: `107`.
- Residual selected/TP/FP/FN: `1452` / `38` / `1414` / `69`.
- Residual precision/recall: `0.026171` / `0.355140`.
- Prefix-selected positive delta cells: `4/5`.

The result is a weak full-fit dependency clue, not a promotion. The best
residual policy beats random p95 in full fit, but prefix-selected
validation is positive in only `4/5` cells and the policy remains broad
and low precision.

## Decision

- Dependency reduction is promoted: `False`.
- Endpoint generator is not promoted.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Target digit boundary miss residual gate](test_results/01_target_digit_boundary_miss_residual_gate.md)
