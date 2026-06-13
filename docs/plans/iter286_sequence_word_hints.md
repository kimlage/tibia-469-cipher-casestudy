# Iter 286: SequenceWordHints + ContextEnglish Candidate Boost

## Goal
Break the semantic/readability plateau without touching the mechanical decode (StrictPlus DP), by:
- Deriving stable word-level hints from `SequenceMatches_Auto`.
- Feeding those hints back into `ContextEnglish` candidate ordering (display-only) to improve contextual English rendering and create safer retext opportunities.

All changes must keep:
- `Coverage_StrictPlus_v108 == 1` for all books.
- GroundTruth live check passing.

## Tasks (Status)
- [x] Add Step `107` (`Sequence Word Hints`) to the runner + workbook `FlowSteps`.
- [x] Create/refresh `SequenceWordHints_Auto` from `SequenceMatches_Auto` (analysis-only).
- [x] Add FlowSettings knobs:
  - `SequenceWordHints_Enabled`, `SequenceWordHints_MaxRows`
  - `SequenceHints_Enabled`, `SequenceHints_Boost`, `SequenceHints_MaxWordsPerSig`
- [x] Use `SequenceWordHints_Auto` to boost `ContextEnglish` candidate counts (display-only).
- [x] Fix runner bug: `allow_markers` / `allow_stars` NameError in Step 40 macro-mining closure.
- [x] Update validator to require Step `107`.
- [x] Run iterations until stale and validate invariants.

## Implementation Notes
- `SequenceWordHints_Auto` is derived only from:
  - `Phrase` (ContextEnglish n-gram)
  - `Snippet` (corpus snippet)
  - With signature equality under `_lore_canon_word()` + `_lore_signature()`
- Hints are applied conservatively:
  - Only as a boost to the existing per-token candidate word counts used by Viterbi.
  - Does not change tokenization, DP, or mechanics.

## Verification Log
- Ran:
  - `python scripts/bonelord_run_until_stale.py bonelord_469_iter129.xlsx --max-iters 12 --stale-consecutive 2`
  - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`
- Results:
  - Workbook advanced `Iter 283 -> 286`.
  - `Iter 284`:
    - `ContextEnglish avg_score`: `3.856860 -> 3.878663`
    - `ContextEnglish oov`: `0.160669 -> 0.158585`
    - `English glossary retext applied`: `3` (GT-safe)
    - `SequenceWordHints`: created (`rows=9`, fp_changed=1)
  - `Iter 285` + `Iter 286`: stale (no further changes) with guardrails still passing.

