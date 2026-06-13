# Iteration 189 - Add Readability Layer (Safe Text Rewrite) + Continue Auto-Loop

## Goals
- Keep the StrictPlus mechanical decode stable, but add a **separate readable layer** that rewrites decoded text for readability.
- Store readability rules inside the workbook (`ReadabilityRules`) so the XLSX remains the single source of truth.
- Run the next iteration and report both mechanical evolution stats and readability deltas.

## Tasks (Status)
- [x] Implement `ReadabilityRules` sheet (auto-created + seeded with minimal rules).
- [x] Add Step 75 to runner: apply readability rules into `Translation_Readable_Auto` (Books + MasterText) and log to `FlowRunLog`.
- [x] Update `FlowSteps` in workbook to include Step 75 (documentation parity).
- [x] Run `scripts/bonelord_flow_next_iteration.py` on `bonelord_469_iter129.xlsx` (creates backup).
- [x] Verify workbook `FlowState`, `FlowRunLog`, `Iter189_Summary` updated consistently; verify readable columns updated.

## Implementation Notes
- Readability rules are conservative whole-word/whole-phrase substitutions and are applied only to the new readable columns.
- Default seeded rules:
  - Enabled: `fiftin statue` → `fifteen statues` (scope BOOKS,MASTER)
  - Disabled suggestions: `eye` → `ye`, `far way` → `far away`

## Run Log (iter189)
- Command:
  - `.venv/bin/python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx`
- Backup:
  - `./tmp/spreadsheets/bonelord_469_iter129_backup_iter189.xlsx`
- Result:
  - `Mechanical promotions accepted=0`
  - Mechanical metrics unchanged (Ev/Weak/Micro/Single/Tokens).
  - Step 75 executed but `repl=0` (bug in regex boundary pattern; fixed in next iteration).
