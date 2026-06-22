# Final Content-Addressed Event Program Audit

Status: `analysis_only`
Classification: `content_addressed_event_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

The gate tested a representation shift: copy events select prior content inside the online-x64 coarse bucket, then exact length and canonical source derive from that chunk. Literal events retain an innovation tape and pay a length delimiter because the composition index is no longer granted.

Residual v2 cost for `composition_index + copy_hint_rank/source + literal_payload` is `3423.183` bits. The content-addressed residual costs `3686.781` bits, a delta of `263.598` bits.

All `208` copy events can derive a canonical source after the target content is selected, but only `200/208` canonical sources match the original raw source. The selected content-rank policy has `5/208` top-80 hits.

## Decision

`content_addressed_event_program_not_promoted`. Source can be canonically derived after a content chunk is selected, but the chunk selection tape is larger than the v2 residual it replaces. This is not a smaller executable generator.

The next barrier is origin/content, not coarse-control: exact composition residual, copy chunk content, literal innovation, and seed payload remain external. `row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_content_addressed_event_program_gate.py](../scripts/01_content_addressed_event_program_gate.py)
- [01_content_addressed_event_program_gate.json](test_results/01_content_addressed_event_program_gate.json)
- [01_content_addressed_event_program_gate.md](test_results/01_content_addressed_event_program_gate.md)
