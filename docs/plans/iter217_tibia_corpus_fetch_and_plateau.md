# iter217: Tibia Internet Corpus (Derived) + Plateau Improvements

## Goal
Break the semantic plateau safely by incorporating an **internet-fetched Tibia corpus** into the existing XLSX loop, without importing or persisting full copyrighted text.

## Approach (Safe)
- Fetch public JSON datasets and store only a **derived signature index** (`Sig -> Word -> Count`) in `LoreSigIndex_Tibia_Auto`.
- Keep all decode guardrails intact (GroundTruth live check, coverage strict, no risky mechanical promotions).
- Keep structural alignment (`AnchorCribs_Auto` import) **idempotent** to avoid churn and false "progress".

## Tasks
- [x] Add Step `91` to `FlowSteps` and runner: `Fetch Tibia SigIndex`.
- [x] Implement `refresh_tibia_sigindex_sheet()` using stdlib `urllib` + derived counts only.
- [x] Execute Step `91` before `Lore Token Hits` (Step `93`) so semantic mining can use the fetched index.
- [x] Add `LoreWordFreq_Tibia_Auto` (derived global word frequency) to support safer semantic retext decisions.
- [x] Tighten semantic retext safety policy (block `GROUNDTRUTH`/`LOGOGRAM_ANCHORED`/`PUNCT_LOGOGRAM`, wordfreq gating, short-word whitelist).
- [x] Add Step `97` to auto-revert unsafe past semantic retext under the current policy (GT-live-check guarded).
- [x] Fix `sync_anchorcribs_from_iter141()` to be idempotent (only write when changed).
- [x] Update validator expected steps to include `91` + `97`.
- [x] Run `run_until_stale` and capture evolution stats table for the user.
- [x] Validate workbook invariants after the run.

## Implementation Log
- Updated `scripts/bonelord_flow_next_iteration.py`:
  - Added constants: `DEFAULT_TIBIA_*_URL`, `LORE_SIGINDEX_TIBIA_SHEET`.
  - Added helper functions for fetching + writing `LoreSigIndex_Tibia_Auto` + `LoreWordFreq_Tibia_Auto`.
  - Added Step `91` execution + FlowRunLog entry.
  - Added Step `97` semantic revert enforcement + logging (`SemanticReverts_Auto`).
  - Made `sync_anchorcribs_from_iter141` idempotent (no rewrite churn).
- Updated `scripts/bonelord_validate_workbook.py` expected steps set.
- Updated `scripts/bonelord_run_until_stale.py` to track `sem_revert` so it doesn't stop early when reverts are the only changes.

## Verification
- Ran multiple auto-chain iterations. Key events:
  - iter219: semantic retext applied `9` (from Tibia-derived semantic hints)
  - iter223: semantic reverts applied `2` (locked evidence classes)
  - iter226: Step91 refreshed and created `LoreWordFreq_Tibia_Auto` (`6000` rows); semantic reverts applied `3`
  - Current workbook iteration: `228`
- Validator:
  - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`
  - Result: `OK: invariants satisfied` at iter228
