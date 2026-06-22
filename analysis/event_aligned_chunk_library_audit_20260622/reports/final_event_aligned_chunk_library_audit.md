# Final Event-Aligned Chunk Library Audit

Status: `analysis_only`
Classification: `event_aligned_chunk_library_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit stepped back from arbitrary content-addressing and tested a more authorially plausible restriction: copy events may select chunks already aligned to previous operation boundaries, including short concatenations of earlier event chunks.

The best mode is max-span `all` with policy `long_recent`. It explains `6/208` copy chunks as event-aligned prior spans and leaves `202` copy chunks on the existing fallback tape.

The resulting residual cost is `3322.129` bits versus `3423.183` for v2, a delta of `-101.054` bits. Prefix holdout improves v2 in `5/5` splits. However, shuffled completed-book boundaries still save `51.361` bits versus v2, leaving only `49.693` bits as the boundary-specific difference.

## Decision

`event_aligned_chunk_library_not_promoted`. The test narrows the candidate universe but coverage is too low to replace the current residual ledger: only a small number of copies are prior event-boundary spans, and the residual saving is partly reproduced by shuffled boundaries. The next blocker remains the origin of copy content, especially subchunks of seed/prior material that are not aligned to event boundaries.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_event_aligned_chunk_library_gate.py](../scripts/01_event_aligned_chunk_library_gate.py)
- [01_event_aligned_chunk_library_gate.json](test_results/01_event_aligned_chunk_library_gate.json)
- [01_event_aligned_chunk_library_gate.md](test_results/01_event_aligned_chunk_library_gate.md)
