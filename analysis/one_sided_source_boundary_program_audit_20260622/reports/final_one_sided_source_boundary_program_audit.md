# Final One-Sided Source-Boundary Program Audit

Status: `analysis_only`
Classification: `PROMOTED_ONE_SIDED_SOURCE_BOUNDARY_PROGRAM`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tested a decodable partial-anchor extension to v3. If one source endpoint is in the promoted boundary set, that endpoint can be rank-coded while exact length remains in the residual composition.

Endpoint coverage is `29` both-endpoint hits, `40` start-only hits, `56` end-only hits, and `83` intervals with neither endpoint in the boundary set.

The best policy is `end_first` at `3230.726` bits, delta `-49.465` versus v3. After charging `2.000` bits to declare one of `4` policies, the delta remains `-47.465`. Prefix-only policy selection improves `5/5` splits with aggregate delta `-62.507`.

## Decision

`PROMOTED_ONE_SIDED_SOURCE_BOUNDARY_PROGRAM`.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_one_sided_source_boundary_program_gate.py](../scripts/01_one_sided_source_boundary_program_gate.py)
- [01_one_sided_source_boundary_program_gate.json](test_results/01_one_sided_source_boundary_program_gate.json)
- [01_one_sided_source_boundary_program_gate.md](test_results/01_one_sided_source_boundary_program_gate.md)
