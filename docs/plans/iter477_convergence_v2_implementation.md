# Iteration 477 - Convergence v2 Implementation (Method Audit + Shadow A/B)

## Scope Implemented
- Added `SOFT_RESOLVED` status semantics to the runner.
- Switched convergence decision to prefer Step12 live GT counters (`bad_enforced`, `bad_all`, `soft`).
- Added soft/hard GT evidence tiering in `GroundTruthPolicy_Auto`:
  - `EvidenceTier=HARD_EXTERNAL` -> hard-blocking.
  - `EvidenceTier=SOFT_PROVISIONAL` -> non-blocking for hard guardrail, blocks `RESOLVED`.
- Marked default soft-provisional crib IDs: `5,9,12,13`.
- Added FlowState telemetry fields:
  - `GTBadEnforcedCount`, `GTBadAllCount`, `GTSoftMismatchCount`
  - `GroundTruthLiveCheckModeActive`, `GroundTruthEnforcedCount`
  - `PromotionSkipCount`, `PromotionSkipReasonTop`
  - `IterationsSinceLastMechanicalPromotion`
  - `GTSoftMismatchNonDecreasingStreak`
  - `HardResolvedCheck`, `SoftResolvedCheck`
- Added new FlowSettings:
  - `SoftMismatchMaxForResolved` (default `0`)
  - `SoftMismatchMaxForSoftResolved` (default `999`)
  - `PlateauBlock_NoPromotionIters` (default `3`)
  - `Convergence_UseLiveGTCounts` (default `TRUE`)
- Added plateau guard:
  - force `BLOCKED` when no mechanical promotions for `N` iterations with recurring skips.
- Added monotonic soft-mismatch guard:
  - if `SOFT_RESOLVED` persists and soft mismatches do not decrease for >2 iterations, force `BLOCKED`.
- Logged promotion skip counters and dominant reason in FlowRunLog/FlowState.

## Scripts Added
- `scripts/bonelord_ab_shadow_experiment.py`
  - Creates shadow workbooks (`control`, `conservative`, `moderate`).
  - Runs fixed iterations per profile.
  - Applies hard gates and no-regression checks.
  - Computes ranking score and emits `ab_report.json`.

## Validator Updates
- `scripts/bonelord_validate_workbook.py` now enforces:
  - `RESOLVED`/`PUZZLE_SOLVED` must have `soft_gt=0`.
  - `SOFT_RESOLVED` must have `soft_gt>0`.
  - FlowState GT counters must match live GT check results.

## Execution Results
- Canonical run executed at iteration `477`.
- New status: `SOFT_RESOLVED`.
- Live GT counters:
  - `bad_enforced=0`, `bad_all=4`, `soft=4`.
- Validation:
  - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`
  - Result: `OK: invariants satisfied`.

## Shadow A/B Results
- Command:
  - `python scripts/bonelord_ab_shadow_experiment.py bonelord_469_iter129.xlsx --iterations 3`
- Winner:
  - `control`
- Report:
  - `./tmp/spreadsheets/shadow_ab_20260213_123328Z/ab_report.json`
- Note:
  - all profiles hit the new monotonic soft-mismatch guard by iteration 479/480 (`BLOCKED`), which is expected under unchanged soft mismatch count.
