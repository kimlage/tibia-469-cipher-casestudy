# Minimal Capture Design

Classification: `minimal_capture_design_ready_no_source_integrated`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This is an acquisition design for a future rights-clean object-layer capture.
It does not integrate a source and does not change v9, row0, plaintext, translation, semantics, or compression_bound.

The recommended first useful batch is `balanced_v9_probe_22_books`: all seed books `0..9` plus two high-signal derived books from each decade bucket `10s..60s`.
That batch is designed to satisfy the current protocol floor while preserving prefix-holdout splits across the corpus.

## Batch Coverage

| Batch | Books | Derived | Joined v9 ops | Prefix splits | Meets floor |
| --- | ---: | ---: | ---: | --- | --- |
| `balanced_v9_probe_22_books` | 22 | 12 | 102 | prefix_20, prefix_30, prefix_40, prefix_50, prefix_60 | `True` |
| `high_signal_extension_30_books` | 30 | 20 | 171 | prefix_20, prefix_30, prefix_40, prefix_50, prefix_60 | `True` |
| `full_followup_remaining_40_books` | 40 | 40 | 90 | prefix_20, prefix_30, prefix_40, prefix_50, prefix_60 | `True` |

## Decision

`minimal_capture_design_ready_no_source_integrated`.

Progress still requires filling object/container/slot/order and rights fields from a clean primary or authorized source.
The design only reduces acquisition ambiguity; it does not reduce the decoder ledger until real data is supplied and passes v9 holdout/permutation controls.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
