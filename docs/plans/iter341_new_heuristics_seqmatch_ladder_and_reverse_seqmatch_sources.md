# Iteration 341 - New Heuristics: SeqMatch Ladder + ReversePhrase SeqMatch Sources (Safe)

## Goal
Break the plateau safely by increasing *structural* signal (sequence matches + phrase hits) without touching StrictPlus DP:
- Improve `SequenceMatches_Auto` recall on plateaus (still snippet-only).
- Feed those matches into `ReversePhrase` as additional phrase sources (analysis-first).
- Fix a canon mismatch that was starving `AutoPhraseCribs` and causing `ReversePhrase` hits to remain 0.

Guardrails remain unchanged:
- `Coverage_StrictPlus_v108 == 1` for all books.
- `groundtruth_live_check()` must pass.
- Mechanical promotions remain gated by no-regression metrics.

## Tasks
- [x] Add `ReversePhrase` source: `SequenceMatches_Auto` snippets (settings-gated).
- [x] Fix `AutoPhraseCribs` canon flags to match `ReversePhrase` canon flags (share=1.0 feasibility must be consistent).
- [x] Add `SequenceMatch` plateau ladder (rung-aware relax: candidate freq, n-list, time budget, max matches).
- [x] Run `next iteration` and verify:
  - `AutoPhraseCribs` eligible/kept increases or stays stable (but not worse by canon mismatch).
  - `ReversePhrase` finds hits (or at least emits candidates) without breaking guardrails.
  - `SequenceMatches` count/fingerprint changes when the ladder relaxes.
- [x] Run `scripts/bonelord_run_until_stale.py` and capture per-iter deltas.
- [x] Validate workbook invariants via `scripts/bonelord_validate_workbook.py`.

## Changes
File: `./scripts/bonelord_flow_next_iteration.py`
- New FlowSettings:
  - `ReversePhrase_IncludeSequenceMatchesAuto` (default `TRUE`)
  - `ReversePhrase_SeqMatchesMaxPhrasesPerIter` (default `40`)
  - `ReversePhrase_SeqMatchesMinN` (default `5`)
- ReversePhrase step now optionally loads phrase sources from `SequenceMatches_Auto` (`Snippet` column).
- AutoPhraseCribs now uses the *ReversePhrase* canon flags (not the global lore canon flags) for feasibility filtering.
- Plateau ladder now relaxes SequenceMatch knobs by rung:
  - rung0: `cand_max_freq=1`, `n_list=[6,7,8]`, `budget=20s`, `max_matches=60`
  - rung1: `cand_max_freq=2`, add `n=5`, `budget=30s`, `max_matches=80`
  - rung2: `cand_max_freq=3`, add `n=4`, `budget=45s`, `max_matches=120`

## Implementation Log
- Commands:
  - `python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx`
  - `python scripts/bonelord_run_until_stale.py bonelord_469_iter129.xlsx --max-iters 15 --stale-consecutive 2`
  - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`

- Iteration results:
  - Iter `341`:
    - Mechanical evolution unchanged: `EvAvg=2.326444`, `Weak=0.039798`, `Micro=0.030023`, `Single=0.019899`, `Tokens=893`.
    - `SequenceMatches`: `20 -> 34` (fp_changed=1).
    - `AutoPhraseCribs`: scanned=50,000; eligible=34; kept=34 (CHANGED).
    - `ReversePhrase`: phrases_scanned=211; hits=0; emitted_tokens=0.
    - Status: `RESOLVED` (= mechanically stable).
  - Iter `342` + `343`:
    - No further deltas (stale by definition). `SequenceMatches=34` (fp_changed=0), `ReversePhrase hits=0`.

- Validation:
  - `workbook iteration=343 status=RESOLVED`
  - `OK: invariants satisfied`
