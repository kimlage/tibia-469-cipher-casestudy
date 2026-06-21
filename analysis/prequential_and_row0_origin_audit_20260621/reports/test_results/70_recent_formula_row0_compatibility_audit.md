# Recent Formula Row0 Compatibility Audit

Classification: `row0_unchanged_book_formula_improved`
Translation delta: `NONE`

## Purpose

This gate checks whether the latest partial-boundary formula promotions
change the independent row0-origin conclusion. They do not: the formula
front improves the book-generation bound while continuing to assume row0
as an already supplied substrate.

## Result

- Current compression bound checked: `8154.676268` bits.
- Row0 status: `row0_origin_exogenous_under_current_evidence`.
- `row0 changed`: `False`.
- Recent formula status: `book_generation_improved_row0_unchanged`.
- Predicts row0 labels under holdout: `False`.
- Beats row0 lookup after cost: `False`.
- Explains `39`, `93`, `19/91`: `False`.
- New row0 provenance: `False`.
- Promoted origin formulas: `0`.

## Recent Formula Gates Checked

| Source | Classification | Bound/gain | Row0 status |
|---|---|---:|---|
| `analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/66_partial_boundary_shift_formula_gate.json` | `partial_boundary_shift_formula_improves_bound` | `8155.261037 (+0.788949)` | `unchanged_exogenous` |
| `analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/68_partial_boundary_shift_second_pass_formula_gate.json` | `partial_boundary_shift_second_pass_formula_improves_bound` | `8154.676268 (+0.584769)` | `unchanged_exogenous` |
| `analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/69_partial_boundary_shift_saturation_gate.json` | `partial_boundary_shift_saturated` | `8154.676268 (0 improving)` | `unchanged_exogenous` |

## Row0 Compatibility Checks

| Check | Outcome | Interpretation |
|---|---|---|
| Row0 label holdout prediction | `False` | Recent formula gates alter copy/reference recipes; they contain no independent row0 label predictor. |
| Lookup reduction after rule/anchor cost | `False` | Paid anchor gate remains negative after explicit pair+label cost. |
| `39` / `93` / `19/91` explanation | `False` | These stay promoted surface/render clues only, not label-origin derivations. |
| New provenance | `False` | Local project provenance is partially traced, while CipSoft/authorial origin remains untraced. |
| Formula assumes row0 | `True` | The book formula works downstream from the row0 substrate. |

## Taxonomy

- `PROMOTED_ORIGIN_FORMULA`: `0`
- `PROMOTED_MECHANICAL_CLUE`: `1`
- `WEAK_CLUE`: `1`
- `REJECTED_CONTROL`: `1`
- `BLOCKED_NEEDS_EXTERNAL_SOURCE`: `1`
- `AUDIT_ONLY`: `1`

## Decision

- `row0 unchanged`.
- The latest book-formula advances are compatibility-only from the row0 perspective.
- No row0-origin formula is promoted.
- No plaintext, translation, semantic reading, or case reopening is introduced.
