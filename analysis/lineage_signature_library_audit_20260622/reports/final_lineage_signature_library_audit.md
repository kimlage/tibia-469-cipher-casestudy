# Final Lineage Signature Library Audit

Status: `analysis_only`
Classification: `lineage_signature_library_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tests whether the remaining v6 fallback copy chunks reuse a small library of causal lineage signatures rather than requiring source copy-hints event by event.

The best signature family is `signature_kind_run_lengths`. Full-fit cost uses a library of `63` signatures and is `737.215` bits versus copy-hint. Prefix support is `0/5` positive splits, and the shuffled signature control has p05/p50/p95 deltas `737.215` / `737.215` / `737.215`.

## Decision

`lineage_signature_library_not_promoted`.

The remaining fallback chunks do not currently share a compact paid lineage-signature library. This further narrows the blocker to content selection/origin rather than event graph organization.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_lineage_signature_library_gate.py](../scripts/01_lineage_signature_library_gate.py)
- [01_lineage_signature_library_gate.json](test_results/01_lineage_signature_library_gate.json)
- [01_lineage_signature_library_gate.md](test_results/01_lineage_signature_library_gate.md)
