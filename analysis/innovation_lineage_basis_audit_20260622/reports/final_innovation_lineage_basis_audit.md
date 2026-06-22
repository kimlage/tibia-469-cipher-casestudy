# Final Innovation Lineage Basis Audit

Status: `analysis_only`
Classification: `innovation_lineage_basis_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit propagates digit-level lineage from seed and literal innovation atoms through the executable v6 decoder, then asks whether the remaining v6 fallback copy origins can be addressed in that innovation basis.

The v6 fallback set has `90` copy events and `779.571` copy-hint bits. Only `55` sources are contiguous intervals inside a single seed/literal lineage atom. The lineage-address program costs `1022.251` bits after declaration, delta `242.680` versus copy-hint.

Prefix support is `0/5` positive splits. The randomized-lineage control has p05/p50/p95 deltas `85.693` / `106.016` / `130.492`, and observed beats p05 is `False`.

## Decision

`innovation_lineage_basis_not_promoted`.

The lineage basis is useful provenance for the causal ledger, but it does not explain the remaining fallback source choices as a compact content origin program. The blocker remains origin/selection of innovation content.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_innovation_lineage_basis_gate.py](../scripts/01_innovation_lineage_basis_gate.py)
- [01_innovation_lineage_basis_gate.json](test_results/01_innovation_lineage_basis_gate.json)
- [01_innovation_lineage_basis_gate.md](test_results/01_innovation_lineage_basis_gate.md)
