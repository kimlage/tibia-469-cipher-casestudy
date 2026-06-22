# Causal Event Graph Program Gate

Classification: `causal_event_graph_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Baseline

- v6 roundtrip: `True`.
- v6 external bits excluding seed: `4065.013`.
- v6 external bits including seed: `9699.003`.
- v6 reduction vs v5: `32.320` bits.
- Graph nodes: `261`.
- Graph edges: `1120`.
- Source classes: `{'fallback': 90, 'end_only': 55, 'both_endpoint_interval': 52, 'literal_span_source': 11}`.

## Macro Holdout

- Best exact-token cutoff: `60`.
- Best exact-token delta vs minimal v2 test ledger: `86.439` bits.
- Best exact-token nontrivial exact books without correction: `0`.
- Best high-token cutoff: `60`.
- Best high-token delta vs minimal v2 test ledger: `94.934` bits.
- Best high-token nontrivial exact books without correction: `0`.

## Decision

`causal_event_graph_program_not_promoted`.

The graph is a useful unified ledger, but the prefix-learned macro program does not replace the v6 residual tapes after paying declarations and corrections. The current blocker remains content/innovation origin, not a local source/length selector.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
