# Iteration 362 - Code-Aware Homophones (Digits Codes -> Better English Rendering)

## Goal
Break the plateau by exploiting what the workbook already proves:
`Digits -> (2-digit codes) -> base letters` is deterministic, and **codes within the same base letter are homophones**.

Add a safe, display-only loop that uses **digits-code variants** to stabilize ambiguous 1-letter tokens (e.g. `T`, `N`, `V`) into more consistent English, improving:
- readability
- sequence matching against corpora
- downstream hints (without touching StrictPlus/Glossary DP)

## Tasks (Status)
- [x] Add FlowStep `111` "Code-Aware Homophones Render" (SAFE, display-only)
- [x] Add FlowSettings knobs:
  - `CodeAware_Enabled`
  - `CodeAware_MinTotalPerCode`
  - `CodeAware_MinTopShare`
  - `CodeAware_MaxMapRows`
  - `CodeAware_ApplyToTokens`
- [x] Implement renderer + mapping writer:
  - Write `CodeWordMap_Auto` (stable (Token,Code)->TopWord)
  - Write `Books.Translation_CodeAware_Auto` (+ per-book override counts)
- [x] Make `SequenceMatches` prefer `Translation_CodeAware_Auto` when present
- [x] Track progress in FlowState:
  - `CodeWordMapCount`, `CodeWordMapFingerprint`, `CodeWordMapFingerprintChanged`
  - `CodeAwareBooksChangedRows`, `CodeAwareOverridesTotal`
- [x] Update validator to require Step `111` for latest iteration
- [x] Update `run_until_stale` to treat `CodeWordMapFingerprintChanged` / `CodeAwareBooksChangedRows` as progress

## Guardrails
- No edits to `Glossary.Use_StrictPlus_v108` or `Glossary.Translation` in Step 111.
- Uses existing ContextEnglish candidate filtering (blocked logograms; short-word allowlist; optional sequence hints).
- No copyrighted corpus text persisted inside XLSX (only derived counts/mappings).

## Implementation Log
- Code:
  - `./scripts/bonelord_flow_next_iteration.py`
    - Added `CODE_WORD_MAP_SHEET`
    - Added FlowStep `111`
    - Implemented `materialize_codeaware_homophones_render()`
    - Inserted Step 111 execution between Step 104 and Step 105
    - `materialize_sequence_matches()` now prefers `Translation_CodeAware_Auto`
    - FlowState now records code-aware fingerprints + stats
  - `./scripts/bonelord_validate_workbook.py`
    - Added expected Step `111`
  - `./scripts/bonelord_run_until_stale.py`
    - Added code-aware stats + staleness gate

## Verification
- Run after executing `next iteration`:
  - `.venv/bin/python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`
  - `.venv/bin/python scripts/bonelord_run_until_stale.py bonelord_469_iter129.xlsx --max-iters 20 --stale-consecutive 2`

## Results (Observed)
- Baseline before change: workbook at `iter361`, mechanically stable.
- `iter362`: CodeAware column/sheet introduced; `map_rows=0` (thresholds too strict for per-code occurrence counts); filled Books column (70 rows).
- `iter363`: CodeAware `map_rows=28` (sheet populated from hint_min_total), but `overrides=0` (soft boosting did not change choices).
- `iter364`: Added CodeAware ladder + switched to local context scoring mapping:
  - `CodeAware: map_rows=28, books_changed_rows=26, overrides=36`
  - `SequenceMatches fp_changed=1` (match set changed; still capped at 36 rows)
  - Core metrics unchanged (StrictPlus preserved): `EvAvg=2.327439, Weak=0.036307, Micro=0.028452, Single=0.018677, Tokens=881`
- `iter365..iter366`: stale (no further changes under current ladder settings); validator OK.
