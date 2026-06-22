# Final Executable v6 Literal-Span Origin Audit

Status: `analysis_only`
Classification: `PROMOTED_EXECUTABLE_V6_LITERAL_SPAN_ORIGIN_LEDGER`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit integrates the promoted `literal_span_offset` content-origin subprogram into the executable decoder ledger after v5.

Roundtrip remains `70/70`. External bits excluding seed fall from v5 `4097.333` to v6 `4065.013`, a reduction of `32.320` bits. Including the unchanged seed payload, the ledger moves from `9731.323` to `9699.003`.

Copy classes are now `{'both_endpoint_interval': 52, 'end_only': 55, 'fallback': 90, 'literal_span_source': 11}`. The new class derives `11` fallback copy sources from prior literal spans; all derived sources match the raw source in the validation ledger (`11`/`11`).

The replaced subset previously cost `111.547` copy-hint bits and is now addressed by `76.905` literal-span offset bits plus the model declaration. The remaining fallback copy-hint tape is `779.571` bits.

## Decision

`PROMOTED_EXECUTABLE_V6_LITERAL_SPAN_ORIGIN_LEDGER`.

This is a small executable dependency reduction, not a complete generator. `90` v5 fallback copy origins, residual composition, literal payload, seed payload, and row0 remain external.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_executable_v6_literal_span_origin_gate.py](../scripts/01_executable_v6_literal_span_origin_gate.py)
- [01_executable_v6_literal_span_origin_gate.json](test_results/01_executable_v6_literal_span_origin_gate.json)
- [01_executable_v6_literal_span_origin_gate.md](test_results/01_executable_v6_literal_span_origin_gate.md)
