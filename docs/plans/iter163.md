# Iteration 163 Plan

## Tasks
- [x] Repair `scripts/bonelord_flow_next_iteration.py` (remove corrupted diff artifacts; restore Cribs DP helpers)
- [x] Expand candidate scan to include `EXTERNAL_POEM` tokens via external base corpus
- [x] Implement mechanical promotion simulation with guardrails (no WEAK/single/micro increase; bounded evidence drop)
- [x] Re-enable recompute steps: `Books`/`Contigs`/`MasterText` + `TokenEvidence_*`
- [x] Run next iteration (163) on `./bonelord_469_iter129.xlsx`
- [x] Verify Avar Tar poem crib flips to match (MatchNorm_v112 = 1) after EXTERNAL_POEM promotions
- [x] Update `FlowState`, `FlowRunLog`, `CandidatePromotions`, `Iter163_Summary`, `SheetIndex`, `MethodLog`, `WorkQueue`

## Implementation Log
- 2026-02-06: Plan created and implementation started.
- 2026-02-06: Backup created at `./tmp/spreadsheets/bonelord_469_iter129_backup_iter163.xlsx`.
- 2026-02-06: Iteration 163 executed: 11 EXTERNAL_POEM tokens promoted mechanically (NEI skipped: LOW); `Cribs` updated (5 rows), and Avar Tar poem crib now matches expected (MatchNorm_v112 = 1). Books strictplus unchanged (0/70).
