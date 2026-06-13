# Iteration 202 - MacroMine Unblocked (Allow Markers + Stars)

## Goal
- Break the plateau by enabling safe macro-mining across the actual corpus patterns:
  - marker tokens (`<E>`, `<FF>`, `<*>`) and
  - `*`-containing base tokens.

## What Changed (Code)
- `./scripts/bonelord_flow_next_iteration.py`
  - `mine_macro_candidates_from_books(...)` gained:
    - `allow_marker_tokens`
    - `allow_star_tokens`
  - FlowSettings defaults added:
    - `MacroMine_AllowMarkers=TRUE`
    - `MacroMine_AllowStars=TRUE`
  - Step 30 / Step 40 macro mining now passes those knobs into macro mining.

## Run Result (Iter 202)
- `mech_promoted=38`
- Evolution (Books, length-weighted):
  - EvAvg `2.333566 -> 2.335102` (d=`+0.001536`)
  - Weak `0.081166 -> 0.046081` (d=`-0.035085`)
  - Micro `0.035608 -> 0.028626` (d=`-0.006982`)
  - Single `0.076628 -> 0.051318` (d=`-0.025310`)
  - Tokens `1458 -> 1195` (d=`-263`)
- Backup:
  - `./tmp/spreadsheets/bonelord_469_iter129_backup_iter202.xlsx`

## Notes
- Many newly promoted macros include explicit lossless marker tokens like `<E>` / `<FF>` / `<*>`.
  - This is safe mechanically (DP must match the existing lossless stream), and it significantly reduces `SingleCharFrac`.
  - Readability layers (`Translation_Readable_Auto`, macro-compressed display columns) remain available for presentation.

## Validation
- `scripts/bonelord_validate_workbook.py` OK

