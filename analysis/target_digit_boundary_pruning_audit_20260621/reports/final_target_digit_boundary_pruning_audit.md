# Final Target Digit Boundary Pruning Audit

Status: `analysis_only`
Classification: `TARGET_DIGIT_BOUNDARY_PRUNING_CLUE_PROMOTED_NOT_GENERATOR`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Does the `prev2_digits` boundary surprisal clue reduce the declared
cutpoint dependency after paying for misses and threshold choice?

## Result

- Books/cutpoints/candidate positions: `60` / `201` / `9507`.
- Best q: `0.1` with candidate fraction `0.102556`.
- Hits/misses: `86/201` / `115`.
- Baseline cutpoint bits: `1137.308`.
- Model bits after q charge: `1031.362`.
- Saving after q charge: `105.946` bits.
- Random saving p95 at best q: `-37.498` bits.
- Prefix-selected positive test-saving cells: `5/5` before q charge and `4/5` after q charge.

This promotes a cutpoint-pruning clue: high `prev2` right-surprisal
bands reduce the paid cutpoint atlas and the best full-fit result
beats random same-size candidate bands. It is still not an endpoint
generator because exact cutpoints outside the band remain declared.

## Decision

- A boundary-pruning clue is promoted.
- No endpoint generator is promoted.
- The skeleton dependency is reduced diagnostically, not eliminated.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Target digit boundary pruning gate](test_results/01_target_digit_boundary_pruning_gate.md)
