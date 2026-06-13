# iter237: Reverse Phrase Mining (Tibia Corpus + Logogram-Aware Matching)

## Summary
Reverse phrase mining previously plateaued with `hits=0` because it matched phrase word signatures against
raw base-token letters, which fails for logograms and for many canonicalization differences.

This iteration extends Step 28 to:
- pull a **small, capped phrase sample** from the public Tibia NPC transcripts + Tibia books JSON,
- use **logogram-aware match atoms** (canonical translation letters) when token letters are not an anagram
  of their canonical translation, and
- keep all outputs bounded (phrases/hits/candidates) to avoid workbook bloat.

## Tasks (Status)
- [x] Add FlowSettings knobs:
  - `ReversePhrase_IncludeTibiaCorpusAuto`
  - `ReversePhrase_TibiaMaxPhrasesPerIter`
  - `ReversePhrase_TibiaIncludeNPC`, `ReversePhrase_TibiaIncludeBooks`
  - `ReversePhrase_LogogramAware`
  - `ReversePhrase_PhraseTextMaxLen`
  - `ReversePhrase_CandidateMaxBaseLen`
- [x] Implement Tibia phrase sampling (runner fetch, no full corpus persistence).
- [x] Implement logogram-aware matching atoms (token-sig vs translation-sig mismatch).
- [x] Keep `ReversePhraseHits_Auto` and candidate emission behavior unchanged (still gated).
- [x] Run a few iterations and record whether hits appear.

## Safety
- Still analysis-first: emitted candidates remain inactive; promotions are gated by Step 40 simulation + GT live check.
- Phrase text is only persisted for *hits* and is capped by `ReversePhrase_PhraseTextMaxLen`.

## Implementation Log
- Code:
  - Updated runner: `./scripts/bonelord_flow_next_iteration.py`
    - Added Tibia phrase loader + logogram-aware matching atoms.
    - Skips LoreCorpus_Auto phrases when Tibia phrases are enabled (runtime control).

- Runs:
  - Iter237-238:
    - Step 28: `phrases=40, hits=0, candidates=0, emitted=0` (still no matches found).

## Next Diagnostic Direction
Given `hits=0` even with Tibia phrases + logogram-aware matching, the next likely unlock is **book-level shingle matching**
against Tibia books using `Translation_English_Auto` (set similarity), rather than exact phrase matching.

