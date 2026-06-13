# Iteration 165 Plan

## Tasks
- [x] Compare `./archive/bonelord_469_iter141.xlsx` vs current workbook to look for missing translations/methodology to incorporate
- [x] Improve candidate discovery so AUTO_CHAIN does not stall when `Glossary.TotalOcc` is stale for inactive tokens
- [x] Add safe macro-mining fallback (DP-aligned n-grams -> new inactive macros) to generate new mechanical candidates
- [x] Run next iteration (165) on `./bonelord_469_iter129.xlsx`
- [x] Verify: no Books StrictPlus drift; logs/summaries updated

## Implementation Log
- 2026-02-06: Verified iter141 vs current: token set matches (313/313) and translations match; differences are activation state + evidence bookkeeping from later iterations. No extra “new words” to import from iter141.
- 2026-02-06: Updated `scripts/bonelord_flow_next_iteration.py`:
  - Candidate scan corpus now includes `Books.DecodedBase` (for inactive tokens with stale `TotalOcc`).
  - Added macro-mining fallback: mine consistent n-grams from Books DP alignment, append as inactive macros in `Glossary`, and then run the normal simulation+promotion guardrails.
  - Mechanical promotion now skips “no effect” candidates (tokens not used in DP metrics).
- 2026-02-06: Backup created at `./tmp/spreadsheets/bonelord_469_iter129_backup_iter165.xlsx`.
- 2026-02-06: Iteration 165 executed: only candidate discovered was `NEI` (EXTERNAL_POEM) but it had no effect in DP metrics, so 0 promotions and FlowState went BLOCKED (no-progress).
