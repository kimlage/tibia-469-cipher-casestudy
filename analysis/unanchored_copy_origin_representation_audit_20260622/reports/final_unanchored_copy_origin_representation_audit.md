# Final Unanchored Copy-Origin Representation Audit

Status: `analysis_only`
Classification: `PROMOTED_UNANCHORED_COPY_ORIGIN_REPRESENTATION`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tested two representation changes for the v4 neither-endpoint copy blocker. `source_endpoint_memory` records paid/derived source endpoints as future boundary marks. `within_prior_span_interval` encodes a copy as offsets inside a previous generated span.

Source-endpoint memory costs `3219.336` residual bits versus v4 at `3232.726`, a delta of `-13.390` before declaration and `-11.805` after charging `1.585` bits. The shuffled-control residual p05 is `3229.804`.

Within-span origin is worse on its own terms: `116` copy ops fit inside one prior span, but span+offset coding is `1281.121` bits worse than the existing copy-hint tape on those same ops.

## Decision

`PROMOTED_UNANCHORED_COPY_ORIGIN_REPRESENTATION`.

Source-endpoint memory is promoted as a small executable residual reduction. It is still partial: fallback copy hints, literal payload, seed payload, and row0 remain external.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_unanchored_copy_origin_representation_gate.py](../scripts/01_unanchored_copy_origin_representation_gate.py)
- [01_unanchored_copy_origin_representation_gate.json](test_results/01_unanchored_copy_origin_representation_gate.json)
- [01_unanchored_copy_origin_representation_gate.md](test_results/01_unanchored_copy_origin_representation_gate.md)
