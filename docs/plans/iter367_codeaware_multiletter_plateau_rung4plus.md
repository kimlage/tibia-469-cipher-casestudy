# Iteration 367 - Break Plateau: CodeAware Multi-Letter (CodeSeq) + Plateau Ladder > 3

## Summary
We hit a stable plateau at `iter366`: mechanical promotions stalled, ContextEnglish stopped improving, and CodeAware (single-letter) stabilized at `CodeWordMapCount=28` with `overrides=36`.

To unlock new progress *without touching StrictPlus/Glossary*, this iteration extends the safe loop:
- **CodeAware now supports multi-letter tokens** by using a joined digits-code sequence (e.g. `09-61`) as a homophone key.
- **Plateau ladder is extended beyond rung 3** (up to rung 6) so "run until stale" can keep relaxing *display/analysis-only* layers rather than stopping early.
- Update `bonelord_run_until_stale.py` so changes in `PlateauLadder_Rung` are treated as progress (prevents premature stop while the ladder is still escalating).

Everything remains **GT-safe**:
- No edits to `Glossary.Use_StrictPlus_v108` from these changes.
- CodeAware remains display-only (`Books.Translation_CodeAware_Auto`).
- Mechanical guardrails remain unchanged (no increases in WEAK/Micro/Single from promotions).

## Tasks (Status)
- [x] Add FlowSettings:
  - `CodeAware_MaxTokenLen`
  - `CodeAware_MinTotalPerCodeSeq`
  - `CodeAware_MinTopShareSeq`
- [x] Extend Step `111` CodeAware:
  - Store `CodeSeq` for tokens up to `CodeAware_MaxTokenLen` (joined by `-`)
  - Apply separate thresholds for `len(Token)==1` vs multi-letter tokens
- [x] Extend plateau auto-advance from max rung `3` to max rung `6`
- [x] Extend CodeAware ladder to tune:
  - `CodeAware_MinTotalPerCode`, `CodeAware_MinTopShare`
  - `CodeAware_MaxTokenLen`, `CodeAware_MinTotalPerCodeSeq`, `CodeAware_MinTopShareSeq`
- [x] Log new CodeAware knobs in Step 111 `FlowRunLog` notes
- [x] Update `scripts/bonelord_run_until_stale.py`:
  - Read `FlowSettings.PlateauLadder_Rung`
  - Add `plateau_rung` / `plateau_rung_changed` to IterStats
  - Treat ladder changes as non-stale

## Implementation Log
- Runner updates:
  - `./scripts/bonelord_flow_next_iteration.py`
    - Step 111 signature extended with CodeSeq + multi-token thresholds
    - New FlowSettings keys added
    - Plateau auto-advance cap increased to rung 6
    - CodeAware ladder extended to rung 4..6 (enables multi-letter CodeSeq mapping)
- Tooling updates:
  - `./scripts/bonelord_run_until_stale.py`
    - Tracks plateau rung changes to avoid stopping early

## Verification
- Compile checks:
  - `python -m py_compile scripts/bonelord_flow_next_iteration.py`
  - `python -m py_compile scripts/bonelord_run_until_stale.py`
- Expected runtime check:
  - Run `.venv/bin/python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx`
  - Validate `.venv/bin/python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`
  - Run `.venv/bin/python scripts/bonelord_run_until_stale.py bonelord_469_iter129.xlsx --max-iters 10 --stale-consecutive 2`

