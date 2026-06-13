# Iteration 198 - SuperAnchor Mining (SupportCount + Intersection)

## Goals
- Incorporate the useful part of the iter141 methodology: **SuperAnchors** should be mined from the aligned backbone using:
  - `SupportCount` (not only `SupportFrac==1`), and
  - a **support-book intersection** across the whole run (books that match the consensus at every coord).
- Keep this **analysis-only** (no impact on StrictPlus DP/Books text), but make it actionable with `SupportBooks` output.

## Tasks (Status)
- [x] Extend `mine_superanchors_from_backbone` to use `SupportCount` + `SupportFrac` stability and compute `SupportBooks` intersection.
- [x] Add FlowSettings knobs:
  - `SuperAnchor_MinSupportBooks`
  - `SuperAnchor_MinSupportFrac` (default tuned for clusters: `0.8`)
- [x] Add Step 87 auto-relax: if strict support frac yields 0 candidates, retry with `0.8` and persist the relaxed setting when it produces output.
- [x] Run `next iteration` (iter198) and validate invariants.

## Implementation Log
- 2026-02-06
  - Updated `scripts/bonelord_flow_next_iteration.py`:
    - Step 87 mining now supports cluster-friendly stability:
      - stable coord if `SupportCount >= SuperAnchor_MinSupportBooks` and `SupportFrac >= SuperAnchor_MinSupportFrac`
      - run accepted only if the **same support-book set** matches consensus for every coord in the run
    - `SuperAnchors_Auto` now includes `SupportBookCount`, `SupportBooks`, and `Criteria`.
    - Added Step 87 auto-relax to `SuperAnchor_MinSupportFrac=0.8` when strict settings yield 0.
  - Ran iteration 198 on `bonelord_469_iter129.xlsx`:
    - `mech_promoted=0`, `books_changed=0/70`
    - Structural: `superanchors=2` (new `SuperAnchors_Auto` output)
  - Validation:
    - `scripts/bonelord_validate_workbook.py` OK

## Verification Checklist
- `python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx`
- `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`
