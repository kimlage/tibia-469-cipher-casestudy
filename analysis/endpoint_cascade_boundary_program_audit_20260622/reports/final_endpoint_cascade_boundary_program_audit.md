# Final Endpoint-Cascade Boundary Program Audit

Status: `analysis_only`
Classification: `WEAK_ENDPOINT_CASCADE_BOUNDARY_CANDIDATE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tested deterministic endpoint cascades after executable v4. The promoted v4 `end_first` policy uses end-only source-boundary anchors but leaves start-only anchors in fallback. The cascade policies try to use both classes through fixed precedence, so no per-copy mode bit is paid.

The best policy is `end_then_start`. After charging `2.585` bits to declare one of `6` tested policies, residual cost changes versus v4 by `-16.137` bits. Prefix-only selection improves `3/5` suffix splits with aggregate delta `-18.836` bits.

## Decision

`WEAK_ENDPOINT_CASCADE_BOUNDARY_CANDIDATE`. Full-fit cost falls, but prefix holdout is not stable enough to replace executable v4.

The executable v4 ledger remains the current promoted endpoint-boundary program.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_endpoint_cascade_boundary_program_gate.py](../scripts/01_endpoint_cascade_boundary_program_gate.py)
- [01_endpoint_cascade_boundary_program_gate.json](test_results/01_endpoint_cascade_boundary_program_gate.json)
- [01_endpoint_cascade_boundary_program_gate.md](test_results/01_endpoint_cascade_boundary_program_gate.md)
