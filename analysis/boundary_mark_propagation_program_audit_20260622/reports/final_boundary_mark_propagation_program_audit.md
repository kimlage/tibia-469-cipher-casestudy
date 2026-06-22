# Final Boundary-Mark Propagation Program Audit

Status: `analysis_only`
Classification: `boundary_mark_propagation_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tested whether source-boundary marks are a persistent online state. When a copy is emitted, source-side marks inside the copied span are mapped into the target span and can support future source-interval derivations.

With propagated marks, derived copy intervals are `34/208` and the residual is `3280.551` bits versus v3 at `3280.192`, a delta of `0.359` bits.

## Decision

`boundary_mark_propagation_not_promoted`. Boundary marks as implemented here do not open a stronger generator than v3; the remaining source intervals still require another origin mechanism.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_boundary_mark_propagation_program_gate.py](../scripts/01_boundary_mark_propagation_program_gate.py)
- [01_boundary_mark_propagation_program_gate.json](test_results/01_boundary_mark_propagation_program_gate.json)
- [01_boundary_mark_propagation_program_gate.md](test_results/01_boundary_mark_propagation_program_gate.md)
