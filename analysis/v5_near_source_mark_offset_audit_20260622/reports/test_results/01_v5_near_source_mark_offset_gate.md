# V5 Near-Source-Mark Offset Gate

Classification: `V5_NEAR_SOURCE_MARK_OFFSET_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- V5 fallback copies tested: `101`.
- Existing copy-hint bits: `891.118`.
- Median abs source/end offset: `1` / `1`.
- Exact source-mark count: `41`.
- Invalid source-offset-only delta: `-760.558`.
- Paid source mark+offset delta: `153.030`.
- Paid end mark+offset delta: `236.760`.
- Paid best endpoint+mode delta: `229.908`.
- Shuffled paid-source p05/p50/p95: `1241.541` / `1281.804` / `1311.869`.

## Decision

`V5_NEAR_SOURCE_MARK_OFFSET_NOT_PROMOTED`: offset-only is a lower bound that grants mark identity.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
