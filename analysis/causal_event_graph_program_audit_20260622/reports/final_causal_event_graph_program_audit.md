# Final Causal Event Graph Program Audit

Status: `analysis_only`
Classification: `causal_event_graph_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit converts the current executable v6 decoder into a causal event graph. The graph has operation, literal-innovation, copy-interval, source-boundary, and endpoint-reuse edges, then tests whether event macros learned in prefix can replace the residual tapes.

The executable baseline is unchanged: v6 roundtrips `70/70`, external bits excluding seed are `4065.013`, including seed `9699.003`, and the narrow v5 -> v6 literal-span reduction is `32.320` bits.

The causal graph materializes `261` event nodes and `1120` edges. Copy source classes are `{'fallback': 90, 'end_only': 55, 'both_endpoint_interval': 52, 'literal_span_source': 11}`.

The macro program is not promoted. The best exact-token prefix holdout is cutoff `60` with delta `86.439` bits versus the minimal v2 test ledger and `0` nontrivial exact books without correction. High-level tokens cover more shape but still do not replace exact residual fields in the executable v6 ledger.

## Decision

`causal_event_graph_program_not_promoted`.

The graph improves the residual accounting surface, but it does not become a smaller frozen program. The remaining blocker is origin/content: residual composition, remaining copy fallback hints, literal payload, seed payload, and row0 remain external.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_causal_event_graph_program_gate.py](../scripts/01_causal_event_graph_program_gate.py)
- [01_causal_event_graph_program_gate.json](test_results/01_causal_event_graph_program_gate.json)
- [01_causal_event_graph_ledger.json](test_results/01_causal_event_graph_ledger.json)
- [01_causal_event_graph_program_gate.md](test_results/01_causal_event_graph_program_gate.md)
