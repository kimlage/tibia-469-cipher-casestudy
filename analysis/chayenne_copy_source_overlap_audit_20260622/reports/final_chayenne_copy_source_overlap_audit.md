# Final Chayenne Copy Source Overlap Audit

Classification: `chayenne_copy_source_overlap_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

The Chayenne seed subspans were tested against executable decoder copy-source intervals.
They overlap `17` copy-source rows for `337` source digits.

## Decision

`chayenne_copy_source_overlap_not_promoted`.

No source-choice rule, event policy, origin source, v9 reduction, plaintext, or translation is promoted.

## Reproducible Artifacts

- [01_chayenne_copy_source_overlap_gate.py](../scripts/01_chayenne_copy_source_overlap_gate.py)
- [01_chayenne_copy_source_overlap_gate.json](test_results/01_chayenne_copy_source_overlap_gate.json)
- [01_chayenne_copy_source_overlap_gate.md](test_results/01_chayenne_copy_source_overlap_gate.md)
