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

## Boundary

- Predictive result: partial learned-component signal, not a final authorial
  generation method. The follow-up failure audit narrows the family failures to
  small component/sample-size stress cases.
- Row0 result: `row0_origin_remains_exogenous`.
- No plaintext, translation, semantic mapping, or case-reopening claim is made.
