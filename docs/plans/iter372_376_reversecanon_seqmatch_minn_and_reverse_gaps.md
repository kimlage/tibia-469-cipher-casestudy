# Iterations 372-377 - Plateau Ladder Rung 7-9: Reverse Canon, SeqMatch MinN, Reverse Gaps

## Summary
After the CodeAware multi-letter breakthrough (iter367-371), we escalated the plateau ladder to explore deeper-but-still-safe structural knobs:
- Align ReversePhrase canon flags to Lore canon on deep plateaus (drop rules + reduced alphabet buckets).
- Add `SequenceMatch_MinN` and ladder it upward to remove noisy bigram matches and focus on higher-signal longer n-grams.
- Add `ReversePhrase_MaxGapTokens` and update reverse phrase matcher to allow small gaps between words (still analysis-only; candidate derivation skipped when gaps are used).

## Tasks (Status)
- [x] Plateau ladder max rung: `9`
- [x] ReversePhrase canon alignment at rung>=7:
  - `ReversePhrase_Canon_DropFinalE`
  - `ReversePhrase_Canon_DropAllH`
  - `ReversePhrase_Canon_DropAllO`
- [x] SequenceMatch quality filter:
  - New `FlowSettings.SequenceMatch_MinN`
  - `materialize_sequence_matches(..., min_n=...)`
  - Ladder increases `SequenceMatch_MinN` (2->3->4->5)
- [x] ReversePhrase gaps:
  - New `FlowSettings.ReversePhrase_MaxGapTokens`
  - `_reverse_phrase_find_matches(..., max_gap_tokens=...)`
  - Ladder increases `ReversePhrase_MaxGapTokens` at deep rungs
  - Candidate derivation skipped when `gap_tokens>0`

## Implementation Log
- `./scripts/bonelord_flow_next_iteration.py`
  - Plateau ladder max rung bumped to `9`
  - Added settings `SequenceMatch_MinN`, `ReversePhrase_MaxGapTokens`
  - `SequenceMatch ladder` now updates `SequenceMatch_MinN` and extends n-lists to include 9..12 at high rungs
  - ReversePhrase ladder aligns canon flags to lore at rung>=7 and increases max span/gap
  - ReversePhrase matcher now supports small gaps (analysis-only)

## Results (Observed)
- Iter 372-376:
  - Core metrics unchanged (StrictPlus preserved): `EvAvg=2.327439, Weak=0.036307, Micro=0.028452, Single=0.018677, Tokens=881`
  - `PlateauLadder_Rung` advanced `7 -> 9`
  - CodeAware map expanded slightly (`55 -> 68` rows) but no additional output overrides beyond the existing `55`.
  - `SequenceMatches` became `0` after `SequenceMatch_MinN` rose to 4+ (noise removed; no high-N matches found yet).
  - ReversePhrase still `hits=0` (even with canon align + gaps).

## Verification
- `python -m py_compile scripts/bonelord_flow_next_iteration.py`
- `python -m py_compile scripts/bonelord_run_until_stale.py`
- `.venv/bin/python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx` (OK at iter 376+)

