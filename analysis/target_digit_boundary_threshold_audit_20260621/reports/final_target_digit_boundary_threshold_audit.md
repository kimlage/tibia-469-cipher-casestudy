# Final Target Digit Boundary Threshold Audit

Status: `analysis_only`
Classification: `TARGET_DIGIT_BOUNDARY_THRESHOLD_DEPENDENCY_REDUCED_NOT_GENERATOR`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Can a `prev2` surprisal/rank threshold generate a boundary set directly,
without granting op-count, if FP/FN corrections are paid?

## Result

- Books/candidates/actual cutpoints: `60` / `9507` / `201`.
- Best policy: `right_ge:4`.
- Baseline full cutpoint atlas bits: `1570.073`.
- Correction bits after policy charge: `924.379`.
- Saving after policy charge: `645.694` bits.
- Random saving p95 before policy charge: `494.352` bits.
- TP/FP/FN: `94` / `841` / `107`.
- Predicted boundaries/correction events: `935` / `948`.
- Precision/recall: `0.100535` / `0.467662`.
- Exact books: `0/60`.
- Prefix-selected positive test-saving cells: `5/5`.

This is a stronger dependency reduction than the op-count-conditioned
pruning ledger because the policy generates a candidate boundary set
without first declaring op-count. It is not a generator: the best policy
requires a large correction list and produces no exact full book skeletons.

## Decision

- Dependency reduction is promoted.
- No endpoint or skeleton generator is promoted.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Target digit boundary threshold gate](test_results/01_target_digit_boundary_threshold_gate.md)
