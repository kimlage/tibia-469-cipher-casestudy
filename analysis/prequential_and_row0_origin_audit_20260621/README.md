---
title: "Prequential and row0 origin audit"
date: 2026-06-21
status: analysis_only_no_semantics
translation_delta: NONE
---

# Prequential and Row0 Origin Audit

This audit freezes the `8558.667` bit model as the validation scope and stops
treating compression-only micro-improvements as generation evidence. It tests
whether learned generation components predict held-out books under frozen
parameters and separately records why `row0` / the 10x10 table remains
exogenous.

## Artifacts

- [scripts/01_prequential_and_row0_origin_audit.py](scripts/01_prequential_and_row0_origin_audit.py) - reproducible audit script.
- [reports/prequential_and_row0_origin_audit.md](reports/prequential_and_row0_origin_audit.md) - consolidated report.
- [reports/test_results/01_prequential_and_row0_origin_audit.md](reports/test_results/01_prequential_and_row0_origin_audit.md) - test-result Markdown.
- [reports/test_results/01_prequential_and_row0_origin_audit.json](reports/test_results/01_prequential_and_row0_origin_audit.json) - structured result ledger.
- [scripts/02_family_holdout_failure_audit.py](scripts/02_family_holdout_failure_audit.py) - decomposes the public-bookcase family holdout failures by component.
- [reports/test_results/02_family_holdout_failure_audit.md](reports/test_results/02_family_holdout_failure_audit.md) - family failure diagnosis.
- [reports/test_results/02_family_holdout_failure_audit.json](reports/test_results/02_family_holdout_failure_audit.json) - structured family failure ledger.
- [scripts/03_train_cv_component_selector_audit.py](scripts/03_train_cv_component_selector_audit.py) - tests whether a train-only component selector can rescue family holdouts.
- [reports/test_results/03_train_cv_component_selector_audit.md](reports/test_results/03_train_cv_component_selector_audit.md) - train-CV selector result.
- [reports/test_results/03_train_cv_component_selector_audit.json](reports/test_results/03_train_cv_component_selector_audit.json) - structured selector ledger.
- [scripts/04_recipe_externality_audit.py](scripts/04_recipe_externality_audit.py) - quantifies how much of the validation still depends on a full-corpus fixed recipe.
- [reports/test_results/04_recipe_externality_audit.md](reports/test_results/04_recipe_externality_audit.md) - recipe-externality result.
- [reports/test_results/04_recipe_externality_audit.json](reports/test_results/04_recipe_externality_audit.json) - structured recipe-externality ledger.

## Boundary

- Predictive result: partial learned-component signal, not a final authorial
  generation method. The follow-up failure audit narrows the family failures to
  small component/sample-size stress cases; the train-CV selector audit then
  rejects a promotable component fallback because only a heldout oracle rescues
  the failures. The recipe-externality audit then quantifies the remaining
  limitation: about half of the `8558.667`-bit ledger is still fixed-recipe or
  non-learned cost, and the prequential split scores rows extracted from the
  full formula rather than discovering held-out recipes.
- Row0 result: `row0_origin_remains_exogenous`.
- No plaintext, translation, semantic mapping, or case-reopening claim is made.
