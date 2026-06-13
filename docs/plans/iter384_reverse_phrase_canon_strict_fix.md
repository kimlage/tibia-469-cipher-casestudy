# Iteration 384 - ReversePhrase Canon Fix (STRICT) to Escape Plateau Safely

## Goal
Restore ReversePhrase mining effectiveness by fixing a deep-plateau ladder regression:
- ReversePhrase canon was being auto-aligned to the **Lore canon drop knobs** (`drop_final_e`, `drop_all_o`) at high plateau rungs.
- Those drop knobs are useful for *semantic grouping*, but they can **destroy true-positive phrase matches** by removing letters that still exist in the decoded base alphabet.

This change is **analysis-only** and **does not** affect StrictPlus DP unless a reverse-mined candidate later passes the existing mechanical safety gates.

## Guardrails (Unchanged)
- `Coverage_StrictPlus_v108 == 1` for all books
- `groundtruth_live_check()` must pass
- No regressions in `WEAK`, `MICRO`, `SingleCharFrac` when applying promotions/retext

## Tasks (Status)
- [x] Patch plateau ladder so ReversePhrase canon does **not** inherit `drop_final_e` from Lore canon at deep plateaus.
- [x] Keep `drop_all_o` aligned to Lore canon (empirically improves anagram signature alignment for many active tokens).
- [x] Run `next iteration` (iter384-385) and verify ReversePhrase continues to scan phrases safely.
- [x] Validate workbook invariants.
- [x] Report evolution stats (EvAvg/Weak/Micro/Single/Tokens + ReversePhrase hits/cands/emits).

## Implementation Notes
- File: `./scripts/bonelord_flow_next_iteration.py`
- Change: remove the rung>=7 behavior that blindly aligned ReversePhrase canon to Lore canon drops.
- New behavior: at rung>=7:
  - Force `ReversePhrase_Canon_DropFinalE = FALSE` (dropping final `e` hurts signature alignment overall).
  - Align `ReversePhrase_Canon_DropAllO` to `Lore_Canon_DropAllO` (data-driven; improves alignment for many tokens).
  - Leave `ReversePhrase_Canon_DropAllH` unchanged (managed separately via `Lore_Canon_AutoFix_DropAllH`).

## Implementation Log
- 2026-02-09: Implemented STRICT ReversePhrase canon enforcement at deep plateau rungs (fixes a likely cause of persistent `hits=0`).
- 2026-02-09: Ran iterations `384` and `385`. ReversePhrase scanned ~232-257 phrases/iter, still `hits=0` (no corpus phrase overlap detected yet). Invariants OK.
