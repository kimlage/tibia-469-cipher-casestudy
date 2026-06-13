# Iteration 344 - Digit Code Context + ReversePhrase (SeqMatch Phrase + Apostrophe Split) (Safe)

## Goal
Escape the plateau using *structural* signal without touching StrictPlus DP:
- Add a deterministic, analysis-only view of **digits-code homophones** by context (prev/next neighbors).
- Improve `ReversePhrase` hit-rate by:
  - using `SequenceMatches_Auto` **book-side phrases** (not only source snippets), and
  - splitting apostrophes into word-parts (`you've -> you + ve`) to align with how the decode usually renders contractions.

Guardrails remain unchanged:
- `Coverage_StrictPlus_v108 == 1` for all books.
- `groundtruth_live_check()` must pass.
- Promotions remain gated by no-regression metrics.

## Changes
File: `./scripts/bonelord_flow_next_iteration.py`
- New sheet: `DigitCodeContext_Auto`
  - Step `110` writes neighbor distributions per digits code, plus an outlier score (JS divergence) within each homophone set.
- ReversePhrase improvements:
  - SequenceMatches phrases now include both `Phrase` (book-side) and `Snippet` (source-side).
  - `_phrase_word_sigs()` splits apostrophes into letter-only parts and drops 1-letter contraction suffixes (except `a/i/o`).
- New FlowSettings:
  - `DigitCodeContext_Enabled` (default `TRUE`)
  - `DigitCodeContext_TopK` (default `8`)
  - `DigitCodeContext_JSAlpha` (default `0.20`)
- New FlowState keys:
  - `DigitCodeContextCount`
  - `DigitCodeContextFingerprint`
  - `DigitCodeContextFingerprintChanged`
  - `DigitCodeContextBestOutlier`

File: `./scripts/bonelord_validate_workbook.py`
- Added expected Step `110`.

## Execution Log
- 2026-02-08
  - Baseline check (workbook was at iter `343` when Step `110` was introduced):
    - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`
      - Failed: `FlowRunLog missing steps for iter 343: [110]` (expected because the workbook hadn’t run with Step 110 yet).
  - Ran next iteration:
    - `python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx`
      - Produced iter `344`
      - Guardrails: `Coverage_StrictPlus_v108==1` and `groundtruth_live_check()` OK
      - DigitCtx: `rows=99`, `homophone_letters=13`, `best_outlier=0.341290`, `fp_changed=1`
      - ReversePhrase: `phrases=216`, `hits=0`, `emitted=0`
      - SequenceMatches: `34` (no change)
      - Core metrics unchanged:
        - `EvAvg=2.326444`, `Weak=0.039798`, `Micro=0.030023`, `Single=0.019899`, `Tokens=893`
  - Validation:
    - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`
      - OK
  - Ran auto-chain until stale (no-progress plateau):
    - `python scripts/bonelord_run_until_stale.py bonelord_469_iter129.xlsx --max-iters 20 --stale-consecutive 2`
      - Produced iters `345` and `346`
      - No promotions/retext/hits; all tracked metrics unchanged across `344..346`.

## Outcome
- Step `110` is now part of the stable workbook loop and creates/updates `DigitCodeContext_Auto` idempotently.
- ReversePhrase improvements did not yield hits yet (likely due to lack of contiguous phrase overlap rather than canonization bugs).
- The loop remains mechanically stable; the plateau persists without additional new signal sources.
