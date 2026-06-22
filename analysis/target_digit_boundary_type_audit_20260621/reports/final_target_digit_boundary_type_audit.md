# Final Target Digit Boundary Type Audit

Status: `analysis_only`
Classification: `TARGET_DIGIT_BOUNDARY_TYPE_RULE_REJECTED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Does the `prev2_digits` boundary clue also explain whether the next
operation after a cutpoint is copy or literal?

## Result

- Boundaries tested: `201`.
- Next-type counts: `{'copy': 161, 'literal': 40}`.
- Majority baseline: `copy` with `161/201` hits.
- Best predicate: `delta_negative` / literal_when_true `True`.
- Best predicate hits: `131/201`.
- Best predicate delta vs majority: `-30`.
- Prequential positive-delta cells: `0/20`.

The cutpoint surprisal clue does not transfer to operation type. The
best tested predicates are all below the copy-majority baseline, and
prefix/suffix context tables do not produce a positive delta. This
keeps the boundary clue scoped to candidate cutpoint reduction.

## Decision

- No boundary type rule is promoted.
- The boundary-pruning clue remains useful for endpoints only.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Target digit boundary type gate](test_results/01_target_digit_boundary_type_gate.md)
