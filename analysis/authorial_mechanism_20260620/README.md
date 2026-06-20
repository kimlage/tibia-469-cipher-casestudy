---
title: "469 authorial mechanism and first-principles model"
date: 2026-06-20
status: mechanism_search_no_semantics
translation_delta: NONE
---

# 469 Authorial Mechanism Model

This directory incorporates the 2026-06-20 first-principles report on
Knightmare/design constraints and the possible fabrication space for the 469
books.

The purpose is not to infer private intent. The purpose is to convert the
report into bounded mechanical hypotheses and run additional generation-method
tests against the current best baseline: `tape_based_formula_469.json`.

## Gates

- No authorial-intent claim is promoted without a direct source.
- No semantic claim is promoted without CipSoft/in-game ground truth.
- A generation-method improvement must reduce recipe/inventory cost, predict a
  held-out mechanical property, or improve a committed manifest.
- Search breadth is charged; lookup-disguises and pretty stories are rejected.

## Contents

- `source_research_summary.md` - distilled incorporation of the first
  first-principles report.
- `source_generation_formula_next_report_summary.md` - incorporation status for
  the follow-up generation-formula report and its recommended tests.
- `hypothesis_registry.yaml` - H-AUTH/H-GEN hypothesis registry.
- `scripts/01_first_principles_hypothesis_audit.py` - checks that the report's
  claims are bucketed without semantic promotion.
- `scripts/02_recipe_supermodule_search.py` - looks for higher-order repeated
  recipe patterns over the tape formula.
- `scripts/03_topology_module_signal_audit.py` - tests whether public topology
  predicts module/component sharing.
- `scripts/04_literal_absorption_search.py` - checks whether remaining tape
  literals can be absorbed by existing tape components.
- `scripts/05_literal_reference_formula_compile.py` - compiles a candidate
  formula that replaces cost-positive literal strings with tape substring
  references and validates 70/70 roundtrip.
- `scripts/06_literal_reference_benchmark_controls.py` - compares the base,
  tape, and literal-reference formulas under the same rough MDL ledger and runs
  negative controls against the literal-reference gain.
- `scripts/07_tape_inventory_self_reference_search.py` - tests whether the 16
  tape components have a smaller self-reference inventory layer, with controls.
- `scripts/08_hierarchical_reference_formula_compile.py` - combines tape
  inventory self-references with book-level literal references into the current
  strongest 70/70 mechanical generation formula.
- `scripts/09_hierarchical_provenance_pair_label_audit.py` - tests whether the
  new hierarchical provenance features explain the unresolved unordered
  pair-table labels.
- `scripts/10_sequential_lz_book_formula_compile.py` - materializes a
  sequential book-level copy/reference generator and compares it with the
  hierarchical formula and negative controls.
- `scripts/11_sequential_lz_order_search.py` - tests whether non-numeric book
  emission orders improve the sequential LZ formula after charging order cost.
- `scripts/12_sequential_lz_literal_run_cost_compile.py` - re-costs the
  sequential LZ generator with literal runs instead of per-digit literal flags.
- `scripts/13_sequential_lz_dp_parse_compile.py` - replaces the greedy
  sequential LZ parse with a dynamic-programming parse under the same
  run-literal cost.
- `scripts/14_copy_source_address_model_search.py` - tests whether source
  positions are cheaper as absolute addresses, back-distances, deltas, or
  book-relative offsets.
- `scripts/15_copy_graph_provenance_audit.py` - materializes the DP LZ copy
  graph and literal seed atlas for provenance analysis.
- `reports/` - generated and human-readable outputs.

Translation delta: `NONE`.
