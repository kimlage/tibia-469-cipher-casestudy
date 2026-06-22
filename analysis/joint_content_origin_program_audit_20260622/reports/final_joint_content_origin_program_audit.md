# Final Joint Content-Origin Program Audit

Status: `analysis_only`
Classification: `PROMOTED_LITERAL_SPAN_CONTENT_ORIGIN_SUBPROGRAM`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tested the constructive route suggested by the v5 frontier synthesis: encode fallback copy origins through already emitted content origins, rather than as an independent copy-hint tape.

The v5 fallback baseline is `891.118` bits over `101` copy events. The best content-origin model is `literal_span_offset` at `858.798` bits after declaration, delta `-32.320` bits vs copy-hint.

Integrated as a limited v5 reduction, this would move external bits excluding seed from `4097.333` to `4065.013`. The saving comes from the `11` fallback sources that start inside prior literal innovation spans; the other fallback sources still use the existing copy-hint tape.

Holdout support is `4/5` positive suffix splits. Only `11` fallback sources start inside prior literal innovation spans; seed/literal spans cover `67` sources, while prior op spans cover `101` as expected from the emitted corpus.

## Decision

`PROMOTED_LITERAL_SPAN_CONTENT_ORIGIN_SUBPROGRAM`.

This is a real but narrow executable dependency reduction, not a complete content-origin generator. Most fallback copy origins remain external; literal payload also remains an external innovation tape.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_joint_content_origin_program_gate.py](../scripts/01_joint_content_origin_program_gate.py)
- [01_joint_content_origin_program_gate.json](test_results/01_joint_content_origin_program_gate.json)
- [01_joint_content_origin_program_gate.md](test_results/01_joint_content_origin_program_gate.md)
