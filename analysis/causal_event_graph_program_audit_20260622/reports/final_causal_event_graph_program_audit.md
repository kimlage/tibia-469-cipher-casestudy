# Final Causal Event Graph Program Audit

Status: `analysis_only`
Classification: `causal_event_graph_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit converts the current executable v6 decoder into a causal event graph with seed spans, literal innovation spans, copy source spans, operation spans, source-boundary/endpoint marks, and edges for emitting, copying, consuming literal tape, deriving sources, and creating marks.

The graph has `261` operation events. The current executable baseline remains `4065.013` external bits excluding seed.

Prefix/family macro tests cover `72` split-stream rows. The best macro delta versus direct event labels is `88.238` bits; `0` rows are positive, `2` beat shuffled p05, and only `1` tested sequence is generated without raw corrections.

Required controls do not rescue the route: same-multiset shuffled graph controls are beaten in only a small minority of rows, permuted book order and randomized source-span controls remain non-promoting, shuffled macro labels do not expose a hidden paid saving, and shuffled literal tape does not preserve the literal innovation schedule.

## Decision

`causal_event_graph_program_not_promoted`.

The current blocker is still origin of innovation/content rather than a local source/endpoint/composition selector. The causal graph is useful as a ledger, but the tested macros do not become a smaller executable generation program.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_causal_event_graph_program_gate.py](../scripts/01_causal_event_graph_program_gate.py)
- [01_causal_event_graph_program_gate.json](test_results/01_causal_event_graph_program_gate.json)
- [01_causal_event_graph_ledger.json](test_results/01_causal_event_graph_ledger.json)
- [01_causal_event_graph_program_gate.md](test_results/01_causal_event_graph_program_gate.md)
