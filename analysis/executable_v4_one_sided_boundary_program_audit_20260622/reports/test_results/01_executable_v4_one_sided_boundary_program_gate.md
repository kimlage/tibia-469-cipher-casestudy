# Executable v4 One-Sided Boundary Program Gate

Classification: `PROMOTED_EXECUTABLE_V4_ONE_SIDED_BOUNDARY_LEDGER`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- Roundtrip: `70/70`.
- Policy: `end_first` with declaration bits `2.000`.
- Class counts: `{'fallback': 123, 'one_sided_end': 56, 'both': 29}`.
- V3 external bits excluding seed: `4156.604`.
- V4 external bits excluding seed: `4109.138`.
- Delta excluding seed vs v3: `-47.465` bits.
- V4 external bits including seed: `9743.129`.

## V4 Tape Breakdown

- Online x64 coarse-control: `876.412`.
- Copy/endpoint boundary tape: `1835.132`.
- Residual length composition: `511.961`.
- Literal payload: `883.633`.
- Seed payload: `5633.990`.

## Decision

`PROMOTED_EXECUTABLE_V4_ONE_SIDED_BOUNDARY_LEDGER`: one-sided boundary anchors reduce the executable v3 ledger.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
