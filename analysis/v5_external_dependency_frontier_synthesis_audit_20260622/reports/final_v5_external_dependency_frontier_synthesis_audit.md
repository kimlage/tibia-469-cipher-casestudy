# Final V5 External Dependency Frontier Synthesis Audit

Status: `analysis_only`
Classification: `V5_EXTERNAL_DEPENDENCY_FRONTIER_SYNTHESIS`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This synthesis consolidates the current v5 executable frontier and the post-v5 negative gates. V5 remains the promoted executable program. The largest remaining non-seed blocker components are `copy_fallback_hint_bits` `891.118` bits, `literal_payload_bits` `883.633` bits, `residual_composition_bits` `439.959` bits.

The copy-origin local routes are now closed under current evidence: endpoint priority is full-fit only, near-mark offsets are a lower bound unless mark identity is granted, and exact mark-rank streams remain more expensive than copy hints. Literal payload generator/reference routes are also closed or weak under paid costs.

## Decision

`V5_EXTERNAL_DEPENDENCY_FRONTIER_SYNTHESIS`.

The next aligned route is `joint_content_origin_program`: a representation that jointly models exact copy-origin mark identity and literal innovation payload as content-origin choices. More local endpoint/source selectors should not be the main path unless they introduce a new source of exact identity and clear holdout/controls.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_v5_external_dependency_frontier_synthesis.py](../scripts/01_v5_external_dependency_frontier_synthesis.py)
- [01_v5_external_dependency_frontier_synthesis.json](test_results/01_v5_external_dependency_frontier_synthesis.json)
- [01_v5_external_dependency_frontier_synthesis.md](test_results/01_v5_external_dependency_frontier_synthesis.md)
