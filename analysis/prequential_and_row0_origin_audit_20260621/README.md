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
- [scripts/05_row0_hypothesis_requirement_audit.py](scripts/05_row0_hypothesis_requirement_audit.py) - forces each row0-origin hypothesis through the same algorithm/cost/coverage/control checklist.
- [reports/test_results/05_row0_hypothesis_requirement_audit.md](reports/test_results/05_row0_hypothesis_requirement_audit.md) - row0 hypothesis requirement matrix.
- [reports/test_results/05_row0_hypothesis_requirement_audit.json](reports/test_results/05_row0_hypothesis_requirement_audit.json) - structured requirement ledger.
- [scripts/06_recipe_reparse_evidence_matrix.py](scripts/06_recipe_reparse_evidence_matrix.py) - checks whether deterministic reparse evidence reduces the fixed-recipe externality.
- [reports/test_results/06_recipe_reparse_evidence_matrix.md](reports/test_results/06_recipe_reparse_evidence_matrix.md) - recipe-reparse evidence matrix.
- [reports/test_results/06_recipe_reparse_evidence_matrix.json](reports/test_results/06_recipe_reparse_evidence_matrix.json) - structured recipe-reparse ledger.
- [scripts/07_recipe_reparse_trainset_multicutoff.py](scripts/07_recipe_reparse_trainset_multicutoff.py) - expands random same-size train-set controls beyond cutoff 50.
- [reports/test_results/07_recipe_reparse_trainset_multicutoff.md](reports/test_results/07_recipe_reparse_trainset_multicutoff.md) - multi-cutoff train-set control.
- [reports/test_results/07_recipe_reparse_trainset_multicutoff.json](reports/test_results/07_recipe_reparse_trainset_multicutoff.json) - structured multi-cutoff train-set ledger.
- [scripts/08_recipe_reparse_family_holdout.py](scripts/08_recipe_reparse_family_holdout.py) - tests deterministic reparse under public-bookcase family holdout.
- [reports/test_results/08_recipe_reparse_family_holdout.md](reports/test_results/08_recipe_reparse_family_holdout.md) - family holdout recipe-reparse result.
- [reports/test_results/08_recipe_reparse_family_holdout.json](reports/test_results/08_recipe_reparse_family_holdout.json) - structured family holdout ledger.
- [scripts/09_recipe_reparse_family_loss_decomposition.py](scripts/09_recipe_reparse_family_loss_decomposition.py) - decomposes the five family holdout losses against the active frozen recipe.
- [reports/test_results/09_recipe_reparse_family_loss_decomposition.md](reports/test_results/09_recipe_reparse_family_loss_decomposition.md) - family loss component diagnosis.
- [reports/test_results/09_recipe_reparse_family_loss_decomposition.json](reports/test_results/09_recipe_reparse_family_loss_decomposition.json) - structured family loss ledger.
- [scripts/10_family_holdout_address_space_audit.py](scripts/10_family_holdout_address_space_audit.py) - tests whether the remaining family copy-address losses survive same-coordinate repricing.
- [reports/test_results/10_family_holdout_address_space_audit.md](reports/test_results/10_family_holdout_address_space_audit.md) - address-space repricing result.
- [reports/test_results/10_family_holdout_address_space_audit.json](reports/test_results/10_family_holdout_address_space_audit.json) - structured address-space ledger.
- [scripts/11_family_holdout_address_corrected_scoreboard.py](scripts/11_family_holdout_address_corrected_scoreboard.py) - applies the address-space correction to every public-bookcase family holdout.
- [reports/test_results/11_family_holdout_address_corrected_scoreboard.md](reports/test_results/11_family_holdout_address_corrected_scoreboard.md) - address-corrected family scoreboard.
- [reports/test_results/11_family_holdout_address_corrected_scoreboard.json](reports/test_results/11_family_holdout_address_corrected_scoreboard.json) - structured address-corrected family ledger.
- [scripts/12_family_holdout_no_test_carryover_audit.py](scripts/12_family_holdout_no_test_carryover_audit.py) - tests family holdout reparsing without cross-book carryover inside the held-out family.
- [reports/test_results/12_family_holdout_no_test_carryover_audit.md](reports/test_results/12_family_holdout_no_test_carryover_audit.md) - no-test-carryover family holdout result.
- [reports/test_results/12_family_holdout_no_test_carryover_audit.json](reports/test_results/12_family_holdout_no_test_carryover_audit.json) - structured no-test-carryover ledger.
- [scripts/13_leave_one_book_out_no_self_audit.py](scripts/13_leave_one_book_out_no_self_audit.py) - tests each individual book against an inventory made from the other 69 books only.
- [reports/test_results/13_leave_one_book_out_no_self_audit.md](reports/test_results/13_leave_one_book_out_no_self_audit.md) - singleton holdout no-self result.
- [reports/test_results/13_leave_one_book_out_no_self_audit.json](reports/test_results/13_leave_one_book_out_no_self_audit.json) - structured singleton holdout ledger.

## Boundary

- Predictive result: partial learned-component signal, not a final authorial
  generation method. The follow-up failure audit narrows the family failures to
  small component/sample-size stress cases; the train-CV selector audit then
  rejects a promotable component fallback because only a heldout oracle rescues
  the failures. The recipe-externality audit then quantifies the remaining
  limitation: about half of the `8558.667`-bit ledger is still fixed-recipe or
  non-learned cost, and the prequential split scores rows extracted from the
  full formula rather than discovering held-out recipes. The recipe-reparse
  evidence matrix partially reduces that limitation: deterministic reparse
  roundtrips held-out suffixes and beats content controls, but numeric prefix
  training is not unique against random same-size train inventories. The
  multi-cutoff train-set control sharpens that boundary: numeric prefix wins
  against random-train mean at `2/3` tested cutoffs and loses at cutoff `60`.
  Public-bookcase family holdout further strengthens the recipe signal:
  deterministic reparse beats raw digits in `19/19` families and in `3/3`
  component-failure families, while beating the active frozen recipe in `14/19`.
  The five remaining active-recipe wins are now localized: all roundtrip, all
  still beat raw digits, and four are dominated by copy-address overhead rather
  than changed literal/copy inventory. Same-coordinate address repricing then
  shows those copy-address losses are artifacts of comparing reparse addresses
  emitted after the training complement against active addresses charged in
  original global numeric positions. Applying that correction across every
  public-bookcase family changes the active comparison from `15/19` beat-or-tie
  families before correction to `19/19` after correction. A stricter
  no-test-carryover variant still beats raw digit coding in `19/19` families,
  so the positive family signal does not require earlier held-out books to feed
  later held-out books. Singleton leave-one-book-out reparsing also roundtrips
  `70/70` books and beats raw digit coding in `70/70`, with minimum gain
  `96.055` bits.
- Row0 result: `row0_origin_remains_exogenous`.
- Requirement follow-up: all six requested row0-origin families have explicit
  algorithm, cost or cost note, coverage, contradiction, and control entries;
  promoted origin formulas remain `0`.
- No plaintext, translation, semantic mapping, or case-reopening claim is made.
