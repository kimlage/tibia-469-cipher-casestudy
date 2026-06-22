# Final Executable v9 Innovation Copy-Continuation Audit

Status: `analysis_only`
Classification: `PROMOTED_EXECUTABLE_V9_INNOVATION_COPY_CONTINUATION_LEDGER`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit integrates a small source-derivation rule into the executable innovation replay. When a copy immediately follows another copy and both target/source cursors advance together, v9 derives the current source as `previous_source + previous_length`. The continuation sites are paid by a combinatorial index over copy-after-copy opportunities.

There are `17` opportunities and `5` continuations. The rule saves `51.219` source bits and pays `13.595` pattern bits.

Integrated total content-included bits move from v8 `6954.909` to v9 `6917.285`, a reduction of `37.624` bits. Roundtrip remains `70/70`.

## Decision

`PROMOTED_EXECUTABLE_V9_INNOVATION_COPY_CONTINUATION_LEDGER`.

This is a real but narrow executable dependency reduction. It does not solve the innovation replay policy: event schedule, copy/literal decisions, and non-continuation copy source-length choices remain external.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_executable_v9_innovation_copy_continuation_gate.py](../scripts/01_executable_v9_innovation_copy_continuation_gate.py)
- [01_executable_v9_innovation_copy_continuation_gate.json](test_results/01_executable_v9_innovation_copy_continuation_gate.json)
- [01_executable_v9_innovation_copy_continuation_gate.md](test_results/01_executable_v9_innovation_copy_continuation_gate.md)
