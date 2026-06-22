# Executable v3 Source-Boundary Program Gate

Classification: `PROMOTED_EXECUTABLE_V3_SOURCE_BOUNDARY_LEDGER`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Does the promoted partial source-boundary program reduce the executable decoder ledger after preserving roundtrip and paying fallbacks?

## Summary

- Roundtrip: `70/70`.
- Copy intervals derived by source-boundary program: `29/208`.
- Copy intervals still on fallback copy-hint tape: `179/208`.
- V2 residual bits replaced: `3423.183`.
- V3 source-boundary residual bits: `3280.192`.
- V2 external bits excluding seed: `4299.595`.
- V3 external bits excluding seed: `4156.604`.
- Delta excluding seed vs v2: `-142.991` bits.
- V3 external bits including seed: `9790.594`.

## V3 Tape Breakdown

- Online x64 coarse-control rank/corrections: `876.412`.
- Source-boundary interval ranks: `275.077`.
- Fallback copy-hint ranks: `1609.521`.
- Residual length composition: `511.961`.
- Literal payload: `883.633`.
- Seed payload: `5633.990`.

## Decision

`PROMOTED_EXECUTABLE_V3_SOURCE_BOUNDARY_LEDGER`: the promoted source-boundary program becomes an executable ledger reduction.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
