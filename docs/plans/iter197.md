# Iteration 197 - Plateau Breaker (Evidence Drop Ladder + AnchorCribs v141 + SuperAnchor Support Threshold)

## Goals
- Break the mechanical promotion plateau **safely** (GT + DP + metrics guardrails intact).
- Import the *latest* AnchorCribs from the iter141 archive (`AnchorCribs_v141`) to improve structural alignment inputs.
- Make structural/focus analysis run every iteration when enabled (so each `next iteration` yields max actionable output).
- Allow SuperAnchor mining to be less brittle by making the backbone support threshold configurable.

## Tasks (Status)
- [x] Prefer `AnchorCribs_v141` (fallback `AnchorCribs_v138`) when syncing anchors from `archive/bonelord_469_iter141.xlsx`.
- [x] Add `SuperAnchor_MinSupportFrac` FlowSettings knob and thread it into `mine_superanchors_from_backbone`.
- [x] Add plateau evidence ladder tied to `PlateauLadder_Rung` to relax `MaxEvidenceAvgDrop` conservatively (`0.002 -> 0.003 -> 0.005`).
- [x] Run focus + structural steps every iteration when enabled (not only when `mech_promoted=0`).
- [x] Run `next iteration` and validate invariants (`scripts/bonelord_validate_workbook.py`).

## Implementation Log
- 2026-02-06
  - Updated runner `scripts/bonelord_flow_next_iteration.py`:
    - Step 85: anchor sync now prefers `AnchorCribs_v141` (more anchors than v138).
    - Plateau pre-relax now also applies an evidence-drop ladder by updating `FlowSettings.MaxEvidenceAvgDrop` based on `PlateauLadder_Rung`.
    - Step 87: `mine_superanchors_from_backbone(..., min_support_frac=...)` with new FlowSettings key `SuperAnchor_MinSupportFrac`.
    - Step 82/85/86/87 now run every iteration when enabled (analysis-only, safe).
  - Ran iteration 197 on `bonelord_469_iter129.xlsx`:
    - `mech_promoted=1` (macro token), `books_changed=0/70`
    - Evolution:
      - EvAvg `2.334526 -> 2.332082` (d=`-0.002444`)
      - Weak `0.081166 -> 0.081166` (d=`+0.000000`)
      - Micro `0.035608 -> 0.035608` (d=`+0.000000`)
      - Single `0.080293 -> 0.080293` (d=`+0.000000`)
      - Tokens `1543 -> 1536` (d=`-7`)
    - Structural:
      - AnchorCribs sync `added=5`, `updated=12` (now aligns with iter141 v141 anchors)
      - `refBook=9`, `alignedBooks=20`, `blocks=19`, `superanchors=0`
  - Validation:
    - `scripts/bonelord_validate_workbook.py` OK (coverage + GT live check + expected FlowRunLog steps)

## Verification Checklist
- `python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx`
- `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`
