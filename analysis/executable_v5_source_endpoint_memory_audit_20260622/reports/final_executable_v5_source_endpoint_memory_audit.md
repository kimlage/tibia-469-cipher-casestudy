# Final Executable v5 Source-Endpoint Memory Audit

Status: `analysis_only`
Classification: `PROMOTED_EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_LEDGER`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit integrates the promoted source-endpoint memory representation into the executable decoder ledger. The decoder still roundtrips the same 70 books; the change is that paid or derived copy source endpoints become reusable online marks for future source-interval derivation.

Roundtrip remains `70/70`. External bits excluding seed fall from v4 `4109.138` to v5 `4097.333`, a reduction of `11.805` bits after charging `1.585` representation-declaration bits.

Copy classes shift to `{'both_endpoint_interval': 52, 'end_only': 55, 'fallback': 101}`: more intervals are fully derived, residual composition falls, but `101` copy events still fall back to copy hints.

## Decision

`PROMOTED_EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_LEDGER`.

This is real but small program progress: it reduces a declared external dependency inside the executable ledger. It is not a full generator; fallback copy hints, literal payload, seed payload, and row0 remain external.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_executable_v5_source_endpoint_memory_gate.py](../scripts/01_executable_v5_source_endpoint_memory_gate.py)
- [01_executable_v5_source_endpoint_memory_gate.json](test_results/01_executable_v5_source_endpoint_memory_gate.json)
- [01_executable_v5_source_endpoint_memory_gate.md](test_results/01_executable_v5_source_endpoint_memory_gate.md)
