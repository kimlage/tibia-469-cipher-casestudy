# Final Chayenne Seed Subspan Reuse Audit

Classification: `chayenne_seed_subspan_external_cover_clue_not_reuse_program`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

The Chayenne holdout spans were tested as seed submodules against random same-length seed subspans.
They cover `49/49` Chayenne digits and have `15` derived-book occurrences across `15` derived books.

## Decision

`chayenne_seed_subspan_external_cover_clue_not_reuse_program`.

This is an external-cover clue only: the same spans reconstruct Chayenne, but their derived-book reuse does not beat same-length seed controls. It does not derive module selection, replay events, innovation origin, plaintext, or translation.

## Reproducible Artifacts

- [01_chayenne_seed_subspan_reuse_gate.py](../scripts/01_chayenne_seed_subspan_reuse_gate.py)
- [01_chayenne_seed_subspan_reuse_gate.json](test_results/01_chayenne_seed_subspan_reuse_gate.json)
- [01_chayenne_seed_subspan_reuse_gate.md](test_results/01_chayenne_seed_subspan_reuse_gate.md)
