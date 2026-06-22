# Final Source-Boundary Candidate Program Audit

Status: `analysis_only`
Classification: `PROMOTED_SOURCE_BOUNDARY_PROGRAM`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tested whether the subchunks missed by the event-aligned chunk library can instead be generated as intervals between decoder-visible boundaries in previous material: event/book boundaries, source-side `prev2` surprisal boundaries, and their unions.

The best system is `event_plus_surprisal_top20` with policy `long_recent`. It derives `29/208` copy source intervals. The program costs `3280.192` bits versus `3423.183` for v2, a delta of `-142.991` bits. Prefix holdout improves v2 in `5/5` splits.

## Decision

`PROMOTED_SOURCE_BOUNDARY_PROGRAM`: this route reduces the external source/length ledger and passes controls.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_source_boundary_candidate_program_gate.py](../scripts/01_source_boundary_candidate_program_gate.py)
- [01_source_boundary_candidate_program_gate.json](test_results/01_source_boundary_candidate_program_gate.json)
- [01_source_boundary_candidate_program_gate.md](test_results/01_source_boundary_candidate_program_gate.md)
