# Iteration 397 - Allow Bigram SequenceMatches on Deep Plateau + Hint Ladder

## Goal
Break the current plateau where:
- `SequenceMatches` is non-zero but very small (4–5), producing few hints.
- `ContextEnglish` improves score slightly but does not change rendered text.

We will (still safely, analysis/display-only):
- Allow `SequenceMatch_MinN=2` on deep plateau (rung>=8/9) so we can mine high-signal bigrams.
- Add a small ladder for `SequenceWordHints_MinN` and `SequenceWordHints_MinRatio` so bigram matches can generate hints without flooding.

## Safety
- No change to StrictPlus DP or Glossary.
- Guardrails remain: GT live check is enforced only for retext steps; this change does not touch retext.

## Tasks (Status)
- [x] Patch plateau ladder:
  - SequenceMatch: set `min_n` to 2 at rung>=8/9.
  - SequenceWordHints: relax `MinN` to 2 at rung>=8/9; relax `MinRatio` slightly at rung>=9.
- [x] Allow hinted words to bypass bigram-vocab filtering in `ContextEnglish` / `CodeAware` candidate sets.
- [x] Run `scripts/bonelord_run_until_stale.py` (10 iters max, stale=2) and capture evolution stats.
- [x] Validate workbook invariants.

## Implementation Log
- 2026-02-10: Implemented deep-plateau ladder changes in `scripts/bonelord_flow_next_iteration.py`:
  - `SequenceMatch_MinN` now relaxes back to `2` at rung 8/9 to allow bigram matches.
  - `SequenceWordHints_MinN` ladder: `2` at rung 8/9.
  - `SequenceWordHints_MinRatio` ladder: `1.3` at rung 8 and `1.0` at rung 9.
- 2026-02-10: Implemented hinted-word allowlist in candidate selection so SequenceWordHints can inject words
  even when they are outside the `LoreBigrams_Auto` vocabulary (still display-only; no DP changes).
- 2026-02-10: Results (workbook `bonelord_469_iter129.xlsx`):
  - Iter 397: `SequenceMatches=26` (fp_changed=1) on rung 9.
  - Iter 407: `ContextEnglish books_changed=9, master_changed=2` and `CodeAware books_changed=9` (display-only),
    while StrictPlus metrics remained unchanged.
- 2026-02-10: Validator: `OK: invariants satisfied` at iteration 407.
