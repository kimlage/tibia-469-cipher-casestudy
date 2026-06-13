# Iter 340 - PD Expansion + Tibia SigIndex Fingerprint (Plateau Break, Safe)

## Goal
Advance the 469 decode without touching the mechanical StrictPlus pipeline by:
- Making corpus-derived sheets refresh correctly when canon/URLs change (fingerprint, not only age).
- Expanding public-domain (PD) coverage to increase semantic/context evidence and yield new sequence matches.
- Keeping all guardrails intact (GT live check + Coverage StrictPlus, no WEAK/Micro/Single regressions).

## Tasks (Status)
- [x] Add `TibiaSigIndexFingerprint` (FlowState) so Step 91 refreshes on config/canon changes, not only on `MaxAgeHours`.
- [x] Add FlowSettings knob `Lore_Canon_AutoFix_DropAllH` (default OFF) to avoid surprising auto-flips.
- [x] Expand auto-seeded PD sources when plateau ladder rung>=2:
  - Add: Pride & Prejudice, Frankenstein, Dracula, Moby Dick, Beowulf (Gummere) in addition to existing KJV/Alice/Sherlock/Shakespeare/Paradise Lost.
- [x] Run the loop until stale (bounded) and record evolution stats.
- [x] Validate workbook invariants.

## Implementation Notes
### Runner changes
File: `./scripts/bonelord_flow_next_iteration.py`
- Added helper `_digit_code_map_letters()` (used only for optional auto-fix).
- Added `prev_tibia_sig_fp` load from FlowState.
- Step 91 now computes `tibia_sig_fp_full` and refreshes if fingerprint changed, then writes `FlowState.TibiaSigIndexFingerprint`.
- Added PD URL constants and extended plateau PD auto-seed list with 5 additional Gutenberg sources.
- Made the `Lore_Canon_DropAllH` auto-fix gated behind `FlowSettings.Lore_Canon_AutoFix_DropAllH` (default OFF).

### Workbook settings changes
File: `./bonelord_469_iter129.xlsx`
- Reverted the earlier experiment that auto-enabled `Lore_Canon_DropAllH` (it reduced lore hits/context quality in this workbook).
- Kept `Lore_Canon_AutoFix_DropAllH=FALSE` by default.

## Verification
- `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`:
  - iteration=`340`, status=`RESOLVED`
  - OK: invariants satisfied (GT live check + Coverage StrictPlus + no unsafe regressions)

## Evolution Stats (Key Deltas)
Baseline (pre-change, around Iter 330):
- `SequenceMatches` = 17
- `LoreBigrams` = 109,528 rows
- `ContextEnglish` avg_score ~ 6.218555, oov ~ 0.121261

After PD expansion + refresh (Iter 335):
- `LoreBigrams` refreshed to `127,986` rows
- `SequenceMatches` increased to `20` (fp_changed=1)
- Context layer changed across many books (display-only), mechanical metrics unchanged

Stabilization run (Iter 336..340):
- Mechanical metrics unchanged throughout:
  - `EvAvg=2.326444`, `Weak=0.039798`, `Micro=0.030023`, `Single=0.019899`, `Tokens=893`
- English glossary retext applied once:
  - Iter 338: `en_retext=3` (GT-safe; logged in `EnglishPromotions_Auto`)
- Converged to stale at Iter 339..340 with `SequenceMatches=20` and `ContextEnglish avg_score=5.988454, oov=0.125819`

## Next Steps
1. Improve signal quality of `SequenceMatches_Auto` by biasing toward longer n-grams once ContextEnglish stabilizes, or by adding a high-precision matching mode (fewer false positives).
2. Add an encoder script (optional) to “reproduce” 469 from canonized English using `DigitLetterCodes_Auto` (still safe, does not touch decode).

