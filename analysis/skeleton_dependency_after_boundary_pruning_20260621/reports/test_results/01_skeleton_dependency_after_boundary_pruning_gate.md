# Skeleton Dependency After Boundary Pruning Gate

Classification: `skeleton_dependency_reduced_not_generated`
Translation delta: `NONE`

## Purpose

Consolidate how much the promoted `prev2` boundary-pruning clue
reduces skeleton dependency once the number of cutpoints per book is
also charged.

## Summary

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

## Decision

- Promotes dependency reduction: `True`.
- Promotes skeleton generator: `False`.
- The `prev2` boundary clue reduces the cutpoint atlas but still grants op counts and residual endpoint selection.
- Operation type is not explained by the boundary clue.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
