# recent_book_formula_as_row0_evidence

Classification: `AUDIT_ONLY`.

Algorithm: Ask whether the current 8154.676268-bit book formula predicts the row0 table rather than merely using it.

Description cost: excluded from row0 scoring

Holdout labels predicted: `0`.

Coverage: 0/55 direct row0 predictions.

Bits below lookup after costs: `0.0`.

39/93/19/91: no.

Controls: compatibility gate has predicts_row0_labels_under_holdout=false and beats_row0_lookup_after_cost=false.

Contradictions: The formula improves downstream book generation while assuming row0 as substrate.

Evidence: `analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/70_recent_formula_row0_compatibility_audit.json`.
