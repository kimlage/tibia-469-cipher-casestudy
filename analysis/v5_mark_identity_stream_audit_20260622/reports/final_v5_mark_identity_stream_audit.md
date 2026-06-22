# Final V5 Mark-Identity Stream Audit

Status: `analysis_only`
Classification: `V5_MARK_IDENTITY_STREAM_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tested whether the source-mark identity stream for the `101` v5 fallback copies can be coded directly, after the near-mark offset audit showed that local offsets are small.

The best valid exact stream is `global_delta_rank_plus_offset`, but it is `105.634` bits worse than the existing copy-hint tape. A rank-bucket-plus-offset lower bound is much cheaper, but it is not decodable because it does not identify the exact mark.

## Decision

`V5_MARK_IDENTITY_STREAM_NOT_PROMOTED`.

The remaining copy-origin blocker is exact source-mark identity, not local offset or a simple sequential rank-delta stream.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_v5_mark_identity_stream_gate.py](../scripts/01_v5_mark_identity_stream_gate.py)
- [01_v5_mark_identity_stream_gate.json](test_results/01_v5_mark_identity_stream_gate.json)
- [01_v5_mark_identity_stream_gate.md](test_results/01_v5_mark_identity_stream_gate.md)
