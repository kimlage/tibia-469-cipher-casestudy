# Final Executable v4 One-Sided Boundary Program Audit

Status: `analysis_only`
Classification: `PROMOTED_EXECUTABLE_V4_ONE_SIDED_BOUNDARY_LEDGER`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

The one-sided source-boundary program is integrated into the executable decoder ledger. Two-ended intervals remain v3-derived; end-anchored one-sided intervals use the `end_first` policy; the remaining intervals fall back to copy-hint rank, with exact lengths still handled by the book-level residual composition.

Roundtrip remains `70/70`. External bits excluding seed fall from `4156.604` to `4109.138`, a reduction of `47.465` bits after policy declaration.

## Decision

`PROMOTED_EXECUTABLE_V4_ONE_SIDED_BOUNDARY_LEDGER`.

This is still partial: intervals with neither endpoint in the promoted boundary set, literal payload, seed payload, and row0 remain external.

## Reproducible Artifacts

- [01_executable_v4_one_sided_boundary_program_gate.py](../scripts/01_executable_v4_one_sided_boundary_program_gate.py)
- [01_executable_v4_one_sided_boundary_program_gate.json](test_results/01_executable_v4_one_sided_boundary_program_gate.json)
- [01_executable_v4_one_sided_boundary_program_gate.md](test_results/01_executable_v4_one_sided_boundary_program_gate.md)
