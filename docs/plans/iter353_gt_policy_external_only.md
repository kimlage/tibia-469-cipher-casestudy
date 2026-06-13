# Iteration 353 - GroundTruthPolicy_Auto (External-Only Enforcement) to Break Plateau Safely

## Goal
The workbook currently treats many cribs as `GroundTruth` even when their `Expected` text is an **internal** StrictPlus-readable guess (numeric sources are verified, but the translation text is not). This makes the `groundtruth_live_check()` guardrail too strict and blocks safe readability improvements (semantic/English retext).

This iteration introduces an explicit, workbook-owned policy that controls which `CribID`s are **enforced** by the GT live check:
- Keep the guardrail **strong** for externally known translations.
- Treat numeric-only `Expected` text as **soft** (visible in logs but non-blocking).

## Scope
- In:
  - Add `GroundTruthPolicy_Auto` sheet (idempotent; preserves manual edits).
  - Add FlowSettings keys:
    - `GroundTruthLiveCheck_Mode` (`ALL` | `POLICY`)
    - `GroundTruthPolicy_DefaultEnforcedCribIDs` (default `2,3,4,7`)
  - Update all GT-guarded loops (mechanical promotions, semantic retext, English retext, semantic reverts) to respect the enforced set.
  - Enhance logging: include enforced-vs-soft mismatch counts.
- Out:
  - Reclassifying Cribs rows or editing `Expected*` content automatically.

## Tasks
- [ ] Implement `GroundTruthPolicy_Auto` creation/update (non-destructive).
- [ ] Extend `groundtruth_live_check()` to support enforced subset and return both enforced and full mismatches.
- [ ] Thread the enforced set through:
  - Step 12 guardrail
  - Step 40 mech simulation + macro fallback
  - Step 96 semantic retext
  - Step 97 semantic reverts
  - Step 99 English retext
- [ ] Run:
  - `python -m py_compile scripts/bonelord_flow_next_iteration.py`
  - `python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx`
  - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`
  - optional: `python scripts/bonelord_run_until_stale.py bonelord_469_iter129.xlsx --max-iters 20 --stale-consecutive 2`

## Implementation Log
- Files:
  - `./scripts/bonelord_flow_next_iteration.py`
  - `./docs/plans/iter353_gt_policy_external_only.md`
- Notes:
  - `GroundTruthPolicy_Auto` preserves a non-empty `Enforced` cell (manual override).
  - When `GroundTruthLiveCheck_Mode=ALL`, behavior is identical to legacy (enforce all GT cribs).

## Verification
- Ran:
  - `python -m py_compile scripts/bonelord_flow_next_iteration.py` OK
  - `python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx` -> iter `353`
  - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx` OK
- Iter 353 results (from runner stdout):
  - `status=RESOLVED`
  - `mech_promoted=3`, `books_changed=9/70`
  - Metrics:
    - `EvAvg 2.326444 -> 2.328068` (+0.001623)
    - `Weak 0.039798 -> 0.037703` (-0.002095)
    - `Micro 0.030023 -> 0.028452` (-0.001571)
    - `Single 0.019899 -> 0.019026` (-0.000873)
    - `Tokens 893 -> 887` (-6)
