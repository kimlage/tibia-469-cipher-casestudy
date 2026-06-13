# Iteration 186 - Maximize Progress (MacroMine Always After RESOLVED + Multi-Pass Promotions)

## Goals
- Maximize safe mechanical progress in a single iteration (re-test skipped candidates after baseline improves).
- Expand macro mining to also target `MICRO_MEDIUM` + single-char sequences, not only WEAK sequences.
- After `RESOLVED`, default to `MacroMine_Mode=ALWAYS` behavior so `next iteration` keeps polishing safely.
- Run iteration 186 and report evolution stats (before/after + delta).

## Tasks (Status)
- [x] Expand macro-mining filter to include sequences containing `MICRO_MEDIUM` or single-char components.
- [x] Add `MacroMine_Mode` logic (default ALWAYS when current status is `RESOLVED`).
- [x] Enable macro-mining even when other candidates exist (adds extra macro candidates to the same iteration).
- [x] Implement multi-pass promotion simulation (`PromotionMaxPasses`, default 2 when `RESOLVED`) so skips can be re-tested.
- [x] Run `scripts/bonelord_flow_next_iteration.py` on `bonelord_469_iter129.xlsx` (creates backup).
- [x] Verify workbook `FlowState`, `FlowRunLog`, and `Iter186_Summary` updated consistently.

## Implementation Log
- Code changes:
  - `./scripts/bonelord_flow_next_iteration.py`
    - Macro mining now triggers on sequences containing any of: WEAK, `MICRO_MEDIUM`, or single-char components.
    - New `MacroMine_Mode` behavior (defaults to ALWAYS when current status is `RESOLVED`).
    - Macro mining can add candidates even when other inactive candidates exist.
    - Promotion simulation supports multiple passes:
      - `PromotionMaxPasses` (default 2 when `RESOLVED`)
      - PROMOTE reasons include `passN:` for traceability.

- Command:
  - `.venv/bin/python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx`

- Outputs:
  - Backup created:
    - `./tmp/spreadsheets/bonelord_469_iter129_backup_iter186.xlsx`
  - Workbook updated in place:
    - `./bonelord_469_iter129.xlsx`

- Run result (iter186):
  - `FlowState`:
    - `CurrentIteration=186`
    - `Status=RESOLVED`
    - `SuccessCheck=TRUE`
  - StrictPlus stability:
    - `Books changed (StrictPlus text)=0/70`
  - Metrics:
    - `EvidenceAvg=2.335294`
    - `WeakFrac=0.087101`
    - `MicroFrac=0.038750`
    - `SingleCharFrac=0.083086`
  - Mechanical promotions accepted: 4 (all `MACRO_ACTIVE`)
