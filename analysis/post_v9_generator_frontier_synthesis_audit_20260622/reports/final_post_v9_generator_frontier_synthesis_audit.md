# Final Post-v9 Generator Frontier Synthesis Audit

Status: `analysis_only`
Classification: `post_v9_frontier_synthesis_no_new_program_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit steps back after v9 and asks whether the next tempting local codec should actually become v10. It computes the remaining innovation replay dependencies and tests the strongest obvious copy-length default candidate.

The executable frontier remains v9 at `6917.285` content-included bits. The replay still has `62` events: `39` copies and `23` literal runs.

The copy-length default candidate derives `cap` and `len=9` cases. It is positive but too small/control-close: net saving `23.283` bits, below the `50.0` bit promotion threshold, with random-label controls nearby. It is therefore recorded as `MICRO_REDUCTION_NOT_PROMOTED`, not integrated as v10.

## Decision

`post_v9_frontier_synthesis_no_new_program_promoted`.

The next real blocker remains the innovation replay policy: event schedule, copy/literal decision, and non-continuation copy source-length choices. Further tiny field defaults should not be counted as generator progress unless they materially reduce the executable ledger and survive stronger controls.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_post_v9_generator_frontier_synthesis.py](../scripts/01_post_v9_generator_frontier_synthesis.py)
- [01_post_v9_generator_frontier_synthesis.json](test_results/01_post_v9_generator_frontier_synthesis.json)
- [01_post_v9_generator_frontier_synthesis.md](test_results/01_post_v9_generator_frontier_synthesis.md)
