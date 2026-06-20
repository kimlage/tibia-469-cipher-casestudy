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
- `scripts/16_structured_physical_order_lz_test.py` - tests partial public
  Hellgate/bookcase orders against the DP sequential LZ generator.
- `scripts/17_literal_seed_address_model_search.py` - tests literal-seed
  addressing against absolute source positions in the DP copy ledger.
- `scripts/18_literal_seed_grouped_mode_search.py` - tests whether grouped
  source-mode ledgers rescue literal-seed addressing.
- `scripts/19_copy_hub_macro_model_search.py` - tests source-book hub and
  default-source macro ledgers against absolute source positions.
- `scripts/20_restricted_hybrid_vocabulary_reparse.py` - reparses the books
  with a restricted declared motif dictionary plus LZ copies.
- `scripts/21_dp_min_len_sweep_control.py` - sweeps the modern DP sequential
  LZ `min_len` parameter and focused controls.
- `scripts/22_copy_length_code_reparse.py` - reparses the DP sequential LZ
  generator with alternate copy-length codes and emits the Rice-length formula.
- `scripts/23_copy_length_grid_sweep.py` - broadens the Rice-length parameter
  sweep across `min_len=3..12` and Rice `k=0..10`.
- `scripts/24_rice_copy_address_model_search.py` - retests copy-source
  address ledgers on the promoted Rice-length parse.
- `scripts/25_literal_run_length_code_reparse.py` - reparses the promoted
  Rice-length formula while sweeping literal-run length codes.
- `scripts/26_joint_length_code_grid_sweep.py` - tests the interaction between
  copy-length and literal-run length codes around the current best formula.
- `scripts/27_literal_payload_model_search.py` - tests literal digit payload
  coding for the current recipe.
- `scripts/28_current_formula_address_model_search.py` - retests copy-source
  address ledgers on the current best literal-payload formula.
- `scripts/29_literal_to_copy_repair_search.py` - searches for a local
  literal-to-copy recipe repair after adaptive literal-payload coding.
- `scripts/30_post_repair_payload_alpha_sweep.py` - retests adaptive literal
  payload alpha after the local copy repair.
- `scripts/31_post_repair_address_model_search.py` - retests copy-source
  address ledgers after the local copy repair.
- `scripts/32_literal_to_copy_pair_repair_search.py` - tests compatible
  two-repair literal-to-copy recipes under the adaptive payload model.
- `scripts/33_book_length_ledger_search.py` - replaces independent gamma-coded
  book lengths with a cheaper declared signed-Rice residual ledger.
- `scripts/34_book_length_multi_anchor_search.py` - tests multi-anchor
  signed-Rice book-length ledgers after charging mode and anchor costs.
- `scripts/35_digit_only_copy_address_compile.py` - recompiles absolute copy
  addresses over the digit-only stream after book lengths make separators
  reconstructable.
- `scripts/36_digit_address_model_search.py` - retests address ledgers in the
  promoted digit-only coordinate system.
- `scripts/37_digit_address_literal_repair_search.py` - retests local
  literal-to-copy repairs after digit-only address costing.
- `scripts/38_post_digit_repair_payload_alpha_sweep.py` - retests adaptive
  literal-payload alpha after the digit-address repair.
- `scripts/39_post_digit_repair_address_model_search.py` - retests address
  ledgers after the digit-address literal-to-copy repair.
- `scripts/40_item_type_ledger_compile.py` - replaces fixed one-bit
  literal/copy item tags with a decodable adaptive item-type ledger.
- `scripts/41_markov_item_type_ledger_compile.py` - replaces the adaptive iid
  item-type ledger with a decodable previous-type Markov ledger.
- `scripts/42_book_start_item_type_ledger_compile.py` - conditions the
  item-type ledger on declared book starts plus previous item type.
- `scripts/43_literal_forces_copy_type_ledger_compile.py` - tests a charged
  deterministic literal-to-copy item-type rule inside the book-start ledger.
- `scripts/44_remaining_short_forces_literal_type_ledger_compile.py` - tests a
  charged rule that a too-short remaining book suffix forces literal item type.
- `scripts/45_remaining_short_literal_length_compile.py` - removes redundant
  literal-run length bits for forced short book suffixes.
- `scripts/46_forced_length_literal_repair_search.py` - retests one-step
  literal-to-copy repairs after forced suffix literal lengths.
- `scripts/47_post_forced_repair_payload_alpha_sweep.py` - retests adaptive
  literal-payload alpha after the forced-length repair.
- `scripts/48_post_forced_repair_address_model_search.py` - retests copy
  source-address ledgers after the forced-length repair.
- `scripts/49_post_forced_repair_pair_search.py` - tests compatible pairs of
  literal-to-copy repairs after the forced-length repair.
- `scripts/50_post_forced_repair_triple_search.py` - tests compatible triples
  of literal-to-copy repairs after the forced-length repair.
- `scripts/51_post_forced_repair_quad_search.py` - tests compatible quartets
  of literal-to-copy repairs after the forced-length repair.
- `scripts/52_post_forced_repair_quint_search.py` - tests compatible quintets
  of literal-to-copy repairs after the forced-length repair.
- `scripts/53_post_forced_repair_sext_search.py` - tests compatible sextets
  of literal-to-copy repairs after the forced-length repair.
- `scripts/54_post_forced_repair_sept_search.py` - tests compatible septets
  of literal-to-copy repairs after the forced-length repair.
- `scripts/55_post_forced_repair_oct_search.py` - tests compatible octets
  of literal-to-copy repairs after the forced-length repair.
- `scripts/56_post_forced_repair_nonet_search.py` - tests compatible nonets
  of literal-to-copy repairs after the forced-length repair.
- `scripts/57_post_forced_repair_decet_search.py` - tests compatible decets
  of literal-to-copy repairs after the forced-length repair.
- `scripts/58_post_forced_repair_eleven_search.py` - tests compatible
  eleven-repair sets after the forced-length repair.
- `scripts/59_post_forced_repair_twelve_search.py` - tests compatible
  twelve-repair sets after the forced-length repair.
- `scripts/60_post_forced_repair_high_order_exhaustion.py` - closes the
  remaining compatible high-order repair sets from size 13 through 22.
- `scripts/61_post_forced_repair_literal_payload_context_search.py` - tests
  contextual literal-payload coding after the forced-length repair.
- `scripts/62_literal_payload_context_order_sweep.py` - sweeps deterministic
  previous-emitted-digit context order for the final literal payload model.
- `scripts/63_item_type_context_order_sweep.py` - sweeps declared previous
  item-type context order for the final literal/copy item-type ledger.
- `scripts/64_contextual_local_repair_search.py` - retests literal-to-copy
  repairs under the current contextual cost model.
- `scripts/65_contextual_copy_to_literal_repair_search.py` - tests whether
  short copy items should become explicit literals under the contextual cost
  model.
- `scripts/66_post_copy_literal_local_frontier.py` - retests the immediate
  local frontier after the contextual copy-to-literal repair.
- `scripts/67_contextual_address_model_search.py` - retests copy-source
  address ledgers on the current contextual formula.
- `scripts/68_post_contextual_parameter_resweep.py` - retests declared length,
  literal-payload context, and item-type context parameters after the
  contextual copy-to-literal repair.
- `scripts/69_bounded_copy_length_code_compile.py` - replaces unbounded Rice
  copy lengths with a decodable truncated-binary code bounded by declared book
  remaining length and emitted digits after the decoded source address.
- `scripts/70_min_len_bounded_copy_address_compile.py` - tightens absolute
  copy source addresses by excluding the impossible last `min_len - 1` emitted
  digit positions.
- `scripts/71_minaddr_local_frontier.py` - retests single literal-to-copy and
  copy-to-literal repairs under the bounded copy-length and min_len-bounded
  address cost model.
- `scripts/72_post_minaddr_repair_local_frontier.py` - retests the same local
  frontier after the first minaddr literal-to-copy repair changes the recipe.
- `scripts/73_post_minaddr_repair2_local_frontier.py` - retests the local
  frontier after the second minaddr literal-to-copy repair and records closure.
- `scripts/74_post_repair2_parameter_resweep.py` - retests literal-run,
  literal-payload context, and item-type context parameters after the second
  minaddr local repair.
- `scripts/75_post_repair2_pair_frontier.py` - tests compatible pairs of local
  edits after the post-repair2 one-step frontier is closed.
- `scripts/76_post_repair2_address_model_search.py` - retests alternate
  copy-source address ledgers after the post-repair2 formula.
- `scripts/77_post_repair2_copy_order_search.py` - retests source-first versus
  length-first within-copy coding order after the post-repair2 formula.
- `scripts/78_post_repair2_adaptive_copy_length_compile.py` - promotes an
  adaptive bounded copy-length index ledger after the post-repair2 formula.
- `scripts/79_post_adaptive_copy_length_local_frontier.py` - retests the
  one-edit local recipe frontier after adaptive copy-length coding is active.
- `scripts/80_post_adaptive_parameter_resweep.py` - retests declared
  parameters after adaptive copy-length coding is active.
- `reports/` - generated and human-readable outputs.

Translation delta: `NONE`.
