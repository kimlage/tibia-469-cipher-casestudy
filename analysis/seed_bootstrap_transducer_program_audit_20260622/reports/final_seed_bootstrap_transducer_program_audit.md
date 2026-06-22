# Final Seed Bootstrap Transducer Program Audit

Status: `analysis_only`
Classification: `seed_bootstrap_transducer_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit converts the promoted seed copy-surface clue into a stricter target-free decoder test. The decoder receives seed book lengths, a literal tape extracted from the target-conditioned min_len=4 surface, and one deterministic context-copy policy. It does not inspect the target while choosing copy actions.

The surface literal tape has `361` digits. The best target-free policy uses context `4`, copy_len `4`, source `latest`. It matches only the first `55` seed digits before correction and `0`-indexed exact-book scoring gives `0/10` exact seed books. After raw suffix correction it costs `6656.992` bits, delta `1023.002` versus raw seed payload.

Shuffled literal-tape controls have p05/p50/p95 exact-prefix lengths `0` / `0` / `1`.

## Decision

`seed_bootstrap_transducer_not_promoted`.

The seed stream has a real previous-copy surface, but these tested target-free context-copy policies do not convert that surface into a smaller executable seed generator. The next blocker is the policy that decides copy starts and source/length choices, not the existence of repeated seed content.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_seed_bootstrap_transducer_program_gate.py](../scripts/01_seed_bootstrap_transducer_program_gate.py)
- [01_seed_bootstrap_transducer_program_gate.json](test_results/01_seed_bootstrap_transducer_program_gate.json)
- [01_seed_bootstrap_transducer_program_gate.md](test_results/01_seed_bootstrap_transducer_program_gate.md)
