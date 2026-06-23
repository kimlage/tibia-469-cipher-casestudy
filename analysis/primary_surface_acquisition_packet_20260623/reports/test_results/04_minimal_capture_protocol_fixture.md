# Minimal Capture Protocol Fixture

Classification: `minimal_capture_protocol_fixture_path_verified_not_evidence`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This is a synthetic, non-evidential engineering fixture for the minimal capture batch.
It verifies the protocol path only: CSV schema, prefix matching, coverage floor, joined v9 rows, and split construction.
It must not be used as an external topology source or v9 reduction claim.

## Protocol Path Result

- Fixture rows: `22`
- Unique matches: `22`
- Derived matches: `12`
- Coverage ok: `True`
- Split count: `5`
- Joined v9 rows: `102`
- Underlying protocol classification: `clean_topology_v9_control_source_not_promoted`

## Decision

`minimal_capture_protocol_fixture_path_verified_not_evidence`.

The minimal capture design is operationally runnable once real authorized object-layer fields exist.
No external source is integrated, and any synthetic target behavior is non-evidential by construction.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
