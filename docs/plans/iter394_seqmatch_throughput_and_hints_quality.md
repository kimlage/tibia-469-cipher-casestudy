# Iteration 394 - SequenceMatches Throughput + SequenceWordHints Quality Filters

## Goal
Increase *useful* progress when mechanical decoding is stable/plateaued by improving the derived layers that drive readability and safe retext candidates:

- Improve `SequenceMatches_Auto` recall under a fixed time budget (avoid spending most time splitting huge PD corpora before scanning the high-signal Tibia corpus).
- Improve `SequenceWordHints_Auto` signal-to-noise so hints are more actionable for `ContextEnglish` / `CodeAware` (still display-only and GT-safe).

Strict requirements remain unchanged:
- No StrictPlus/DP regressions
- `groundtruth_live_check()` must still pass
- All changes remain *analysis-only* or *display-only* unless a guarded retext step explicitly applies and passes GT checks.

## Changes
1. **SequenceMatches scanning order + PD splitting efficiency**
   - Scan Tibia NPC/Books cache earlier (higher overlap) and avoid building gigantic in-memory sentence lists for huge PD sources.
   - Add FlowSettings knobs to cap PD scan size per source (chars/sentences).

2. **SequenceWordHints quality filter**
   - Add `SequenceWordHints_MinRatio` to keep only the dominant replacement per `(CanonSig, FromWord)` when multiple ToWords compete.

3. **Hint boost scaling**
   - Replace linear `bonus = boost * count` with a logarithmic ladder: `bonus = boost * (1 + log1p(count))`.
   - Goal: give repeated hints more weight without exploding counts; still display-only.

## Tasks (Status)
- [x] Patch `materialize_sequence_matches()` to scan Tibia before large PD sources, and cap PD scan size.
- [x] Patch `materialize_sequence_word_hints()` to add ratio filtering (`SequenceWordHints_MinRatio`).
- [x] Update hint injection in `ContextEnglish` and `CodeAware` to use logarithmic ladder bonus.
- [x] Run `scripts/bonelord_run_until_stale.py` (10 iters max, stale=2) and capture evolution stats per iter.
- [x] Run `scripts/bonelord_validate_workbook.py` to confirm invariants.

## Implementation Log
- 2026-02-09: Implemented:
  - `SequenceMatch_ScanTibiaFirst`, `SequenceMatch_PD_MaxChars`, `SequenceMatch_PD_MaxSentencesPerSource` to improve SequenceMatches throughput under time budget.
  - `SequenceWordHints_MinRatio` and ratio filter (dominant ToWord per `(CanonSig, FromWord)` when multiple compete).
  - Log-ladder hint boost: `bonus = boost * (1 + log1p(count))` (display-only).
- 2026-02-09: Ran `scripts/bonelord_run_until_stale.py` and stopped at 2 consecutive stale iters:
  - Iter 394: `seq_matches=4`, `seq_fp_changed=1`, `ctx_score=6.378921`, `books_changed=0/70`
  - Iter 395: `seq_matches=4`, `seq_fp_changed=0`, `ctx_score=6.378913`, `books_changed=0/70`
  - Iter 396: `seq_matches=4`, `seq_fp_changed=0`, `ctx_score=6.378913`, `books_changed=0/70`
- 2026-02-09: Validator: `OK: invariants satisfied` at iteration 396.
