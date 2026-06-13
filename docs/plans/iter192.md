# Iteration 192 - Plateau Escape (GT Live Check + Focus Report + AnchorCribs + MacroCompress + Readability Scope)

## Goals
- Add **GroundTruth live check** guardrail (DP-current vs `ExpectedNorm_v112`) so we can safely expand search space.
- Add **Plateau focus report** (`IterXXX_Focus`) to make each iteration produce actionable next work even when `mech_promoted=0`.
- Import/sync **AnchorCribs** from `archive/bonelord_469_iter141.xlsx` and generate **variant-aware alignment** sheets (analysis-only).
- Materialize **macro-compressed display-only** outputs for Books/MasterText without touching StrictPlus mechanics.
- Fix **ReadabilityRules Scope** handling and make readability stats reflect *actual deltas* (not re-counting the same replacements every run).

## Tasks (Status)
- [x] Update `scripts/bonelord_flow_next_iteration.py`
  - [x] Step 12: GroundTruth live check (baseline + per-candidate guardrail)
  - [x] Step 12b: Auto-repair GT mismatches by appending active GT-macros (FlowSettings: `GroundTruthAutoRepair*`)
  - [x] Step 82: `IterXXX_Focus` report
  - [x] Step 85: Import AnchorCribs into `AnchorCribs_Auto`
  - [x] Step 86: Build `AnchorOccurrences_Auto`, `BookOffsets_Auto`, `AlignedBackbone_Auto`, `VariantAssemblyBlocks_Auto`
  - [x] Step 87: Mine `SuperAnchors_Auto` suggestions
  - [x] Step 90: Materialize macro-compressed display-only outputs
  - [x] Step 75: Respect `ReadabilityRules.Scope` (+ add CRIBS target)
  - [x] Plateau ladder: auto-relax MacroMine knobs when plateau persists
  - [x] Update `FlowSteps` descriptions to include new steps
  - [x] Allow running after `FlowState.Status=BLOCKED` (guardrails will re-block if needed)
- [x] Add workbook validator script `scripts/bonelord_validate_workbook.py`
- [x] Run `next iteration` on `bonelord_469_iter129.xlsx` and verify invariants

## Implementation Log
- 2026-02-06
  - Updated runner:
    - Added Steps 12/82/85/86/87/90 orchestration + FlowRunLog entries.
    - Implemented GT live check guardrail and per-candidate GT guardrail.
    - Added GT auto-repair: on Step 12 failure, append active GT-macros derived from mismatching Cribs (bounded by `GroundTruthAutoRepairMaxMacros`) and re-check.
    - Added plateau ladder MacroMine relax (rungs 0->1->2) + settings persisted in FlowSettings.
    - Fixed ReadabilityRules Scope handling and added CRIBS output `DP_Readable_Auto`.
    - Materialized macro-compressed display-only columns in Books/MasterText.
    - Plateau diagnostics: `Iter{N}_Focus`, AnchorCribs sync + variant alignment sheets.
  - Added validator: `scripts/bonelord_validate_workbook.py`
  - Ran iterations:
    - Iter 192: BLOCKED (GT live check mismatch for CribID(s) 3,4,8,10,14).
    - Iter 193: Step 12 auto-repair added GT-macros `IVTRASOIETFAI*A`, `FETI*VAA`, `IEETEN`, `ENC`; 1 mechanical promotion; WeakFrac improved `0.083959 -> 0.081166`, token count `1547 -> 1543`.
    - Iter 194: Plateau (mech_promoted=0) generated `Iter194_Focus` and structural alignment sheets; no metric change.
    - Iter 195: Plateau repeat (structural sync updated); no metric change.
  - Validation:
    - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx` passed after Iter 193/194.
