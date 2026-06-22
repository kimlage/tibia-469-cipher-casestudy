# Final Skeleton Dependency After Boundary Pruning Audit

Status: `analysis_only`
Classification: `SKELETON_DEPENDENCY_REDUCED_NOT_GENERATED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

After promoting the `prev2` boundary-pruning clue, how much of the
operation skeleton dependency is actually reduced once op counts are
also charged?

## Result

- Books/internal cutpoints/candidates: `60` / `201` / `9507`.
- Op-count uniform bits: `432.765`.
- Exact conditional cutpoint bits: `1137.308`.
- Pruned conditional cutpoint bits: `1031.362`.
- Exact full cutpoint atlas bits: `1570.073`.
- Pruned full cutpoint atlas bits: `1464.127`.
- Full cutpoint atlas saving: `105.946` bits.
- Op-count share after pruning: `0.295579`.
- Pruning hits/misses: `86` / `115`.
- Type transfer: `rejected`.

The promoted boundary clue does reduce the skeleton cutpoint dependency
under a paid ledger. It does not generate the skeleton: op counts remain
external, `115` cutpoints are still outside the high-surprisal band, and
the copy/literal type transfer audit is rejected.

## Decision

- Dependency reduction is promoted.
- No skeleton generator is promoted.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Skeleton dependency after boundary pruning gate](test_results/01_skeleton_dependency_after_boundary_pruning_gate.md)
