# Final Executable v8 Innovation-Literal Markov Audit

Status: `analysis_only`
Classification: `PROMOTED_EXECUTABLE_V8_INNOVATION_LITERAL_MARKOV_LEDGER`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit integrates a prequential Markov model for the literal digits inside the executable v7 innovation replay. It does not alter the replay events or claim source-free generation; it only replaces raw literal digit declaration inside the already promoted v7 ledger.

The v7 replay has `962` literal digits costing `3195.695` raw bits. The selected order is `2`, costing `2958.453` bits after order declaration.

Integrated total content-included bits move from v7 `7192.151` to v8 `6954.909`, a reduction of `237.242` bits. Same-multiset literal shuffle controls are beaten at p05, and prefix holdouts are positive in `3/3` splits.

## Decision

`PROMOTED_EXECUTABLE_V8_INNOVATION_LITERAL_MARKOV_LEDGER`.

This is a real executable ledger reduction for innovation literal content, but not a complete generator. The replay event schedule, copy/literal decision, and copy source-length policy remain external.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_executable_v8_innovation_literal_markov_gate.py](../scripts/01_executable_v8_innovation_literal_markov_gate.py)
- [01_executable_v8_innovation_literal_markov_gate.json](test_results/01_executable_v8_innovation_literal_markov_gate.json)
- [01_executable_v8_innovation_literal_markov_gate.md](test_results/01_executable_v8_innovation_literal_markov_gate.md)
