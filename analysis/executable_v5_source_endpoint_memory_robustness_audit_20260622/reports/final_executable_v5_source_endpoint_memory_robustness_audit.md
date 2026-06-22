# Final Executable v5 Source-Endpoint Memory Robustness Audit

Status: `analysis_only`
Classification: `PROMOTED_EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_ROBUST`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit checks whether the promoted v5 source-endpoint memory reduction survives prefix/suffix validation and shuffled source-mark controls.

Full-corpus delta is `-11.390` bits before declaration and `-9.805` after declaration under a conservative per-book comparator that does not recharge the v4 policy declaration. The reduction is not confined to one split: v5 improves `4/5` suffix splits with aggregate suffix delta `-31.764`.

The result is still partial. Per-book deltas are mixed, and one suffix split is worse; however the rule remains a controlled executable dependency reduction rather than a pure full-fit artifact.

## Decision

`PROMOTED_EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_ROBUST`.

Executable v5 remains the promoted frontier. Remaining external fields are fallback copy hints, literal payload, seed payload, and row0.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_executable_v5_source_endpoint_memory_robustness_gate.py](../scripts/01_executable_v5_source_endpoint_memory_robustness_gate.py)
- [01_executable_v5_source_endpoint_memory_robustness_gate.json](test_results/01_executable_v5_source_endpoint_memory_robustness_gate.json)
- [01_executable_v5_source_endpoint_memory_robustness_gate.md](test_results/01_executable_v5_source_endpoint_memory_robustness_gate.md)
