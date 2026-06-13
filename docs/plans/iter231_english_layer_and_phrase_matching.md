# iter231: English Layer (Display-Only) + Corpus-Aware Matching Prep

## Summary
The StrictPlus decode is intentionally **canonical** (matches GroundTruth norms like `wit`, `fay`, `lion`).
This is mechanically stable and safe, but it blocks readability and “English-looking” output.

This iteration adds a **display-only English layer** that maps canonical words to their most likely
English surface forms using the internet-derived Tibia corpus signature index already in the workbook.

Key property: **does not change DP/tokenization/metrics**; it only adds new columns/sheets for output.

## Tasks (Status)
- [x] Add FlowSettings knobs for English layer (enabled + thresholds).
- [x] Add `EnglishMap_Auto` sheet (canon_word -> english_word + evidence).
- [x] Materialize `Translation_English_Auto` for `Books` and `MasterText` (display-only).
- [x] Log the step in `FlowRunLog` and document it in `FlowSteps`.
- [x] Extend `bonelord_run_until_stale.py` to include English-layer deltas in the printed table.
- [x] Run `next iteration` until stale and record evolution stats.

## Safety / Guardrails
- English layer is **display-only**:
  - Does not edit `Glossary`, `Books.DecodedBase`, DP outputs, or token evidence.
  - GroundTruth live check remains unchanged and is still the hard guardrail for any mutating step.
- Source policy:
  - Uses only public datasets already integrated: NPC transcripts + books JSON from Tales of Tibia.
  - No leak content, no scraping private sources.

## Verification Checklist
- After running an iteration:
  - `Books` has `Translation_English_Auto` filled (70 rows expected).
  - `MasterText` has `Translation_English_Auto` filled.
  - `EnglishMap_Auto` exists and contains mappings with TopShare/Count evidence.
  - `FlowRunLog` includes Step `98` with counts and `Result=CHANGED` on first run.
  - `scripts/bonelord_validate_workbook.py` still passes.

## Implementation Log
- Code:
  - Updated runner: `./scripts/bonelord_flow_next_iteration.py`
    - Added Step `98` (English layer) + `EnglishMap_Auto` + `Translation_English_Auto` materialization.
    - Added FlowSettings knobs: `EnglishLayer_*`.
    - Included English-layer deltas in plateau bookkeeping and summaries.
  - Updated stale runner: `./scripts/bonelord_run_until_stale.py`
    - Added `en_changed` column parsed from Step 98 summary.
    - Counts English-layer changes as “not stale”.

- Runs:
  - Iter231: English layer first materialization
    - `EnglishLayer: map_rows=3, repl=90, books_changed_rows=70, master_changed_rows=6`
    - Core metrics unchanged: `EvAvg=2.326444`, `Weak=0.039798`, `Micro=0.030023`, `Single=0.019899`, `Tokens=893`.
  - Iter232-233: stale (no new mechanical/semantic/english changes).

- Validation:
  - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx` => OK (iteration=233, status=RESOLVED).
