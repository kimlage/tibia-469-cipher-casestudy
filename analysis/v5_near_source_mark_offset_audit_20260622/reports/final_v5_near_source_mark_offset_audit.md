# Final V5 Near-Source-Mark Offset Audit

Status: `analysis_only`
Classification: `V5_NEAR_SOURCE_MARK_OFFSET_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tested whether the remaining v5 fallback copy hints can be replaced by a near-mark offset program. The diagnostic signal is real: the median absolute source offset is `1`, and `41/101` fallback copies start exactly on an existing v5 mark.

But the decodable program fails. If mark identity is granted for free, source offsets would save `760.558` bits, but after paying the recent-rank identity of the mark, source mark+offset costs `153.030` bits more than the existing copy-hint tape. End offsets and best-endpoint mode are also worse.

## Decision

`V5_NEAR_SOURCE_MARK_OFFSET_NOT_PROMOTED`.

The remaining copy-source blocker is not the local offset; it is selecting which existing mark/source origin to use without granting target content.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_v5_near_source_mark_offset_gate.py](../scripts/01_v5_near_source_mark_offset_gate.py)
- [01_v5_near_source_mark_offset_gate.json](test_results/01_v5_near_source_mark_offset_gate.json)
- [01_v5_near_source_mark_offset_gate.md](test_results/01_v5_near_source_mark_offset_gate.md)
