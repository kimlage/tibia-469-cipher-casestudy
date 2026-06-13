# iter229: Reverse Phrase Mining Auto-Enable (LoreCorpus_Auto)

## Goal
Unblock reverse phrase mining when the user has not yet populated `PhraseCribs_User` / `LoreCorpus_User`, by automatically using the curated, public-domain `LoreCorpus_Auto` seed (Jabberwocky/KJV/Shakespeare/etc.).

This advances translation safely by:
- producing `ReversePhraseHits_Auto` + `ReversePhraseTokenCands_Auto`
- optionally emitting inactive candidates into `Glossary` (`EvidenceClass_v127=PHRASE_CRIB`)
- keeping promotions guarded by the existing Step 40 simulation + GT live check.

## Changes
- Runner: `./scripts/bonelord_flow_next_iteration.py`
  - If reverse mining is enabled and there are **no enabled user phrases**, auto-set:
    - `ReversePhrase_IncludeLoreCorpusAuto = TRUE`
    - bump budgets:
      - `ReversePhrase_MaxPhrasesPerIter >= 200`
      - `ReversePhrase_MaxHitsTotal >= 120`
  - This is logged into `FlowSettings` with `iterN:` notes for reproducibility.

## Safety
- Still analysis-first: candidates are emitted inactive.
- Any promotion requires the existing mechanical simulation guardrails (no GT mismatch, no risk regressions).

## Verification
- Run one iteration and confirm Step 28 no longer reports “no enabled phrases” when user sheets are empty.
- Confirm `ReversePhraseHits_Auto` and `ReversePhraseTokenCands_Auto` are populated (or empty but scanned>0).

