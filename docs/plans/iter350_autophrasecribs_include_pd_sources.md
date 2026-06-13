# Iteration 350 - AutoPhraseCribs: Include PD Sources (Safe)

## Goal
ReversePhrase plateau persisted with Tibia-only phrase cribs. To increase overlap chances without touching DP:
- Extend `AutoPhraseCribs` to mine **public-domain** phrases (Project Gutenberg) in addition to Tibia JSON.
- Keep the hard feasibility filter (`share=1.0` word-signature presence in current decode stream) so we only emit matchable phrases.

Guardrails unchanged:
- `Coverage_StrictPlus_v108 == 1` for all books.
- `groundtruth_live_check()` must pass.
- ReversePhrase candidate emission stays inactive (`Use_StrictPlus_v108=0`).

## Changes
File: `./scripts/bonelord_flow_next_iteration.py`
- Added helper: `_default_pd_sources()` (shared PD source list).
- Added PD miner: `_select_autophrasecribs_from_pd_sources(...)`.
- Step `27` now:
  - mines Tibia phrases (as before),
  - optionally mines PD phrases (new),
  - then combines + re-ranks + de-dupes before writing `PhraseCribs_Auto`.
- New FlowSettings:
  - `AutoPhraseCribs_IncludePD` (default `TRUE`)
  - `AutoPhraseCribs_PDCacheMaxAgeHours` (default `720`)
  - `AutoPhraseCribs_PDMaxScanSentences` (default `25000`)
  - `AutoPhraseCribs_PDTimeBudgetS` (default `25`)
  - `AutoPhraseCribs_PDMaxSources` (default `0` meaning all, time-budgeted)

## Execution Log
- 2026-02-08
  - Ran next iteration:
    - `python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx`
      - Produced iter `350`
      - Step 27 AutoPhraseCribs:
        - `scanned=75000` total (`tibia=50000`, `pd=25000`)
        - `eligible=69`, `kept=69`, `changed=1`
      - Step 28 ReversePhrase:
        - `phrases=246`, `hits=0`, `candidates=0`, `emitted=0`
      - Core metrics unchanged:
        - `EvAvg=2.326444`, `Weak=0.039798`, `Micro=0.030023`, `Single=0.019899`, `Tokens=893`
  - Auto-chain until stale:
    - `python scripts/bonelord_run_until_stale.py bonelord_469_iter129.xlsx --max-iters 20 --stale-consecutive 2`
      - Produced iters `351` and `352` (no additional changes)
  - Validation:
    - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`
      - OK

## Outcome
- Phrase crib coverage increased materially (`39 -> 69` enabled rows).
- ReversePhrase still found no contiguous signature matches in the current book token stream.
- Plateau persists, but we now have broader phrase sources for future structural/matching experiments.
