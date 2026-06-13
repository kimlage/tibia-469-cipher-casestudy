# Iteration 199 - SuperAnchor Macro Candidates (Token-Boundary Snap)

## Goals
- Convert structural progress into mechanical progress safely by deriving **macro candidates from SuperAnchors**:
  - Snap SuperAnchor coord ranges to **DP token boundaries** in the reference book.
  - Build macro translation strictly from existing token translations (lossless stream), so it is semantics-preserving.
- Keep GT + DP + metric guardrails intact.

## What Changed (Code)
- `./scripts/bonelord_flow_next_iteration.py`
  - `add_mined_macros_to_glossary(...)` generalized to support multiple mining sources:
    - sets `StarCount` correctly
    - configurable note kind + `EvidenceSources_v127` tag
  - `refresh_mined_ngram_macro_evidence(...)` now refreshes any `mined macro (...)` note pattern (still safe: never decreases evidence/confidence).
  - New superanchor-macro mining utilities:
    - `_book_base_and_lossless`, `_dp_token_spans`
    - `mine_macro_candidates_from_superanchors(...)`
  - Step 30 enhancement:
    - when `SuperAnchorMacro_Enabled=TRUE`, use previous iteration `SuperAnchors_Auto` (source `cur_iter`) to append `STRUCT_MACRO_CAND` macro candidates.
  - Structural enhancements:
    - `build_variant_alignment_from_anchorcribs` now reads optional `Kind`; for `*_AUTO` anchors it requires unique occurrences per book.
    - Added `promote_superanchors_to_anchorcribs_auto(...)` (analysis-only bootstrap) and related FlowSettings knobs (not yet the main progress driver for iter199).

## Run Result (Iter 199)
- `mech_promoted=2` (both `STRUCT_MACRO_CAND`)
  - `ENNAIFIININSBASTFNENIIFINI*` → `men a I infinite fasten infinity`
  - `FAIFVI*NAESESTIENFATCTIVVTISETE` → `fay fool I <*> no a <E> sestine fact wit wit set <E>`
- Evolution (Books, length-weighted):
  - EvAvg `2.332082 -> 2.333566` (d=`+0.001484`)
  - Weak `0.081166 -> 0.081166` (d=`+0.000000`)
  - Micro `0.035608 -> 0.035608` (d=`+0.000000`)
  - Single `0.080293 -> 0.076628` (d=`-0.003666`)
  - Tokens `1536 -> 1458` (d=`-78`)
- Structural: `superanchors=2` (still)
- Backup:
  - `./tmp/spreadsheets/bonelord_469_iter129_backup_iter199.xlsx`

## Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx` OK

