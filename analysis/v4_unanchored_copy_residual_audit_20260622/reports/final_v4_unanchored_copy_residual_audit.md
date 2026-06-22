# Final V4 Unanchored Copy Residual Audit

Status: `analysis_only`
Classification: `V4_UNANCHORED_COPY_RESIDUAL_BLOCKER_LEDGER`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit consolidates the post-v4 copy residual instead of testing another selector. Executable v4 solves copy events when both source endpoints are anchored or when the end endpoint is anchored. The remaining copy-hint burden splits into start-only weak clues and intervals with neither endpoint anchored.

Class counts are `{'start_only_weak_not_promoted': 40, 'end_only_promoted_v4': 56, 'neither_endpoint_anchored': 83, 'both_endpoints_anchored': 29}`. Remaining fallback copy-hint cost is `1068.942` bits: `375.853` from start-only weak intervals and `693.089` from neither-endpoint intervals.

The start-anchor route remains weak: full-fit and op_count-gated variants reduce v4, but the op_count gate did not beat the random-opcount p95 control. The dominant remaining copy blocker is therefore not endpoint activation; it is deriving source-side boundary or chunk-origin structure for the neither-endpoint class.

## Decision

`V4_UNANCHORED_COPY_RESIDUAL_BLOCKER_LEDGER`.

Next aligned route: representation change for unanchored copy origin. Do not keep tuning start-only activation unless it adds a new source of boundary marks or beats controls.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_v4_unanchored_copy_residual_ledger.py](../scripts/01_v4_unanchored_copy_residual_ledger.py)
- [01_v4_unanchored_copy_residual_ledger.json](test_results/01_v4_unanchored_copy_residual_ledger.json)
- [01_v4_unanchored_copy_residual_ledger.md](test_results/01_v4_unanchored_copy_residual_ledger.md)
