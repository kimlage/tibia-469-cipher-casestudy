# Iter241: EnglishMap -> Glossary Retext (GT-Safe)

## Goal
Advance translation usefulness (real English surfaces) without touching tokenization or evidence metrics, by promoting high-confidence `EnglishMap_Auto` mappings into `Glossary.Translation`, guarded by GroundTruth live check.

## Changes
- New FlowStep `99`: **English -> Glossary Retext**
  - Uses `EnglishMap_Auto` (canon_word -> top_word from Tibia sig-index).
  - Applies per-token string edits only when `groundtruth_live_check()` remains OK.
  - Logs all decisions in `EnglishPromotions_Auto`.
  - Syncs `EvidenceLedger_v127.Translation` for traceability.

## Settings (FlowSettings)
- `EnglishGlossaryRetext_Enabled` (default `TRUE`)
- `EnglishGlossaryRetext_MaxPerIter` (default `50`)
- `EnglishGlossaryRetext_MinTotalCount` (default `5`)
- `EnglishGlossaryRetext_MinTopShare` (default `0.90`)

## Results (Iter241)
- Applied: `9` retexts (attempted `13`)
- StrictPlus changed: `19/70` books (expected and acceptable for translation-only edits)
- GroundTruth + Coverage invariants still pass

## Notes
This step is the safest way to improve English output because:
- It never changes DP token boundaries or token evidence.
- It is gated by GroundTruth live check after each candidate edit.

