# Final Seed Bootstrap Copy-Surface Audit

Status: `analysis_only`
Classification: `PROMOTED_SEED_BOOTSTRAP_COPY_SURFACE_CLUE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit turns back to the largest remaining executable-ledger field: the raw seed payload for books `0..9`. It asks whether those seed digits have a strong previous-copy surface that could justify a future bootstrap transducer route.

The seed payload has `1696` digits and costs `5633.990` raw bits in v6. Under target-conditioned greedy previous-copy parsing with `min_len=4`, `1335` digits are copy-covered and `361` remain literal. Same-multiset digit shuffles have p95 copied digits `534`; seed-book order permutations have p95 copied digits `1354`.

Strong same-multiset wins hold for min_lens `[4, 5, 6, 8, 10, 12]`. Order-sensitive wins hold for min_lens `[5]`.

## Decision

`PROMOTED_SEED_BOOTSTRAP_COPY_SURFACE_CLUE`.

This is not a generator and does not reduce the executable ledger yet: the copy surface is target-conditioned. The valid next constructive question is whether a target-free bootstrap policy can derive starts and copy choices for the seed stream from a much smaller innovation tape.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_seed_bootstrap_copy_surface_gate.py](../scripts/01_seed_bootstrap_copy_surface_gate.py)
- [01_seed_bootstrap_copy_surface_gate.json](test_results/01_seed_bootstrap_copy_surface_gate.json)
- [01_seed_bootstrap_copy_surface_gate.md](test_results/01_seed_bootstrap_copy_surface_gate.md)
