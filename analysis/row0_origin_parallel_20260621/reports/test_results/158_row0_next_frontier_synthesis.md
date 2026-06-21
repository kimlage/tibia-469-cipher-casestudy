# 158. Row0 Next Frontier Synthesis

Classification: `AUDIT_ONLY`
Translation delta: `NONE`

## Decision

`row0_advance_requires_primary_source_or_paid_partial_worksheet_anchor_reduction`.

## Priority order

1. Provenance primary-source search: identify whether row0 entered through workbook/tooling/community reconstruction or an older fixed source.
2. Ordered-surface exception source: look for a fixed source that naturally predicts missing `39`, present `93`, and `19/91` direction.
3. Partial worksheet anchor costing: keep only anchors that pay their rule/source cost and reduce residual lookup.
4. Label-blind pair behavior retest only if new provenance/corpus features appear.

## Current state

- No `PROMOTED_ORIGIN_FORMULA`.
- Surface asymmetry is a real mechanical clue.
- Partial worksheet model is plausible but currently weak because anchor/source costs are unpaid.
- External source remains the only likely strong unlock.
