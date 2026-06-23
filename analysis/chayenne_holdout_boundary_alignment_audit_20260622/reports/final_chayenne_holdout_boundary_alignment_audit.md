# Final Chayenne Holdout Boundary Alignment Audit

Classification: `PROMOTED_CHAYENNE_SUBSPAN_MODULE_HOLDOUT_CLUE_NOT_EVENT_POLICY`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

The promoted Chayenne holdout was localized inside the unified innovation tape.
Its `2` copy spans align with replay event boundaries in `0` cases and consumer boundaries in `0` cases.
Both spans are contained inside single consumer segments (`2/2`), so the result validates reusable subspans in the module bank rather than the replay event boundary policy.

## Decision

`PROMOTED_CHAYENNE_SUBSPAN_MODULE_HOLDOUT_CLUE_NOT_EVENT_POLICY`.

No event policy, origin source, v9 reduction, plaintext, or translation is promoted.

## Reproducible Artifacts

- [01_chayenne_holdout_boundary_alignment_gate.py](../scripts/01_chayenne_holdout_boundary_alignment_gate.py)
- [01_chayenne_holdout_boundary_alignment_gate.json](test_results/01_chayenne_holdout_boundary_alignment_gate.json)
- [01_chayenne_holdout_boundary_alignment_gate.md](test_results/01_chayenne_holdout_boundary_alignment_gate.md)
