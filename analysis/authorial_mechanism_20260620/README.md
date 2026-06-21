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
tests. The original tape baseline is now historical; the current strongest
bound is the deterministic online reparse formula with decodable copy-length
and copy-source default/exception ledgers at roughly `8177.3` bits. Treat this
as `compression_bound` and prefix-frozen partial evidence, not as a final
authorial method: family/bookcase holdouts still have failures.

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
- `scripts/81_post_adaptive_pair_frontier.py` - retests compatible pairs of
  local recipe edits after adaptive copy-length coding is active.
- `scripts/82_post_adaptive_address_model_search.py` - retests alternate
  copy-source address ledgers after adaptive copy-length coding is active.
- `scripts/83_post_adaptive_copy_order_search.py` - retests source-first
  versus length-first copy order after adaptive copy-length coding is active.
- `scripts/84_post_adaptive_copy_length_context_search.py` - retests simple
  decodable contexts for the adaptive copy-length ledger after copy-order
  closure.
- `scripts/85_post_midpoint_local_frontier.py` - retests the immediate
  literal/copy local frontier after the midpoint copy-length context.
- `scripts/86_post_midpoint_parameter_resweep.py` - retests declared
  parameters after the midpoint copy-length context and local-frontier closure.
- `scripts/87_post_midpoint_alpha1_local_frontier.py` - retests the immediate
  literal/copy local frontier after the midpoint copy-length alpha becomes `1`.
- `scripts/88_post_midpoint_alpha1_pair_frontier.py` - retests compatible
  pairs of local edits after the midpoint alpha=1 one-edit frontier closes.
- `scripts/89_post_midpoint_alpha1_address_model_search.py` - retests
  alternate copy-source address ledgers after midpoint alpha=1 becomes active.
- `scripts/90_post_midpoint_alpha1_copy_order_search.py` - retests
  source-first versus length-first copy order after midpoint alpha=1 becomes
  active.
- `scripts/91_post_midpoint_alpha1_copy_length_context_resweep.py` - retests
  copy-length context families after midpoint alpha=1 becomes active.
- `scripts/92_post_midpoint_alpha1_context_alpha_grid.py` - tests separate
  midpoint first-half and second-half copy-length smoothing alphas.
- `scripts/93_post_midpoint_alpha1_literal_payload_context_search.py` -
  retests simple contexts for the adaptive literal-payload model.
- `scripts/94_post_midpoint_alpha1_top60_triple_probe.py` - probes compatible
  triples among the top 60 local single-edit candidates after pair closure.
- `scripts/95_post_midpoint_alpha1_item_type_context_search.py` - tests
  simple contexts for the adaptive item-type model and promotes split book `6`.
- `scripts/96_post_itemctx_parameter_resweep.py` - retests declared
  parameters after split book `6` is active and promotes item-type
  extra-context order `1` / `alpha=2`.
- `scripts/97_post_itemctx_param_local_frontier.py` - retests one-step local
  recipe edits after the itemctx_param promotion.
- `scripts/98_post_itemctx_param_pair_frontier.py` - retests compatible local
  repair pairs after the itemctx_param one-step frontier closes.
- `scripts/99_post_itemctx_param_address_model_search.py` - retests alternate
  copy-source address ledgers after the itemctx_param promotion.
- `scripts/100_post_itemctx_param_copy_order_search.py` - retests
  source-first versus length-first copy order after the itemctx_param
  promotion.
- `scripts/101_post_itemctx_param_copy_length_context_resweep.py` - retests
  copy-length context families after the itemctx_param promotion.
- `scripts/102_post_itemctx_param_context_alpha_grid.py` - retests separate
  midpoint smoothing alphas after the itemctx_param promotion.
- `scripts/103_post_itemctx_param_literal_payload_context_search.py` -
  retests simple literal-payload contexts after the itemctx_param promotion.
- `scripts/104_post_itemctx_param_item_type_context_family_search.py` -
  retests item-type extra-context families with order/alpha sweep after the
  itemctx_param promotion.
- `scripts/105_post_itemctx_param_payload_item_type_pair_context_search.py` -
  retests joint literal-payload and item-type context pairs after the separate
  post-itemctx_param frontiers.
- `scripts/106_post_itemctx_param_copy_length_item_type_pair_context_search.py` -
  retests joint copy-length and item-type context pairs after the separate
  post-itemctx_param frontiers.
- `scripts/107_post_itemctx_param_payload_copy_length_item_type_triple_context_search.py` -
  retests joint literal-payload, copy-length, and item-type context triples
  after the separate post-itemctx_param frontiers.
- `scripts/108_post_itemctx_param_copy_length_alpha_item_type_pair_search.py` -
  retests joint copy-length alpha-by-context and item-type context pairs after
  the separate post-itemctx_param frontiers.
- `scripts/109_post_itemctx_param_copy_length_alpha_payload_pair_search.py` -
  retests joint copy-length alpha-by-context and literal-payload context pairs
  after the separate post-itemctx_param frontiers.
- `scripts/110_post_itemctx_param_copy_alpha_payload_item_type_triple_search.py` -
  retests joint copy-length alpha-by-context, literal-payload, and item-type
  context triples after the separate post-itemctx_param frontiers.
- `scripts/111_post_itemctx_param_copy_length_context_alpha_resweep.py` -
  retests copy-length context candidates with shared alpha values after the
  separate post-itemctx_param context and alpha frontiers.
- `scripts/112_post_itemctx_param_literal_payload_context_alpha_resweep.py` -
  retests literal-payload context candidates with shared alpha values after the
  post-itemctx_param payload context frontier.
- `scripts/113_post_itemctx_param_copy_payload_context_alpha_pair_search.py` -
  combines copy-length context/shared-alpha and literal-payload context/shared-
  alpha frontiers after both component sweeps.
- `scripts/114_post_itemctx_param_copy_payload_item_context_alpha_triple_search.py` -
  combines copy-length context/shared-alpha, literal-payload context/shared-
  alpha, and item-type context/order/alpha frontiers.
- `scripts/115_post_itemctx_param_address_copy_order_pair_search.py` -
  combines copy-source address ledgers with within-copy source/length order
  ledgers after the separate post-itemctx_param copy-cost frontiers.
- `scripts/116_post_itemctx_param_address_item_type_pair_search.py` -
  combines copy-source address ledgers with item-type context/order/alpha
  rows after the separate post-itemctx_param frontiers.
- `scripts/117_post_itemctx_param_address_payload_context_alpha_pair_search.py` -
  combines copy-source address ledgers with literal-payload context/shared-alpha
  rows after the separate post-itemctx_param frontiers.
- `scripts/118_prequential_generation_model_audit.py` - separates
  `compression_bound` from `generation_explanation` by training adaptive
  component counts on prefix books and scoring future books without parameter
  search.
- `scripts/119_row0_origin_frontier_audit.py` - indexes existing row0/table
  origin tests and freezes the current frontier as saturated under the current
  corpus, with no promoted pair-label formula.
- `scripts/120_prequential_order_control_audit.py` - controls the prequential
  result against random same-size train-book sets and rejects numeric order as
  a promoted generation signal.
- `scripts/121_prequential_component_ablation_audit.py` - ablates learned
  component contexts under prefix holdout and separates compression-bound
  refinements from simpler generation-explanation components.
- `scripts/122_simplified_generation_profile_compile.py` - compiles the
  simplified holdout-preferred generation profile against the full corpus and
  confirms it is explanatory, not a lower compression bound.
- `scripts/123_item_type_split_only_formula_compile.py` - promotes split-only
  item-type coding as a decodable formula improvement after conservative
  full-corpus rescoring.
- `scripts/124_item_type_split_only_alpha_resweep.py` - retests the split-only
  item-type smoothing alpha and retains the promoted `alpha=2` bound.
- `scripts/125_prequential_and_row0_origin_audit.py` - freezes `8558.667` as
  the current `compression_bound`, tests learned components under
  prefix/block/family holdout, and records that row0 origin remains exogenous.
- `scripts/126_prequential_recipe_reparse_audit.py` - tests the audit-125
  recipe limitation by reparsing future suffix books with frozen train-prefix
  component counts and a deterministic LZ parser.
- `scripts/127_prequential_recipe_reparse_controls.py` - controls the
  deterministic suffix reparse against random same-length books and shuffled
  suffix/book digit controls.
- `scripts/128_prequential_recipe_reparse_trainset_controls.py` - tests
  whether the deterministic suffix reparse is specific to numeric prefix
  training or also appears with random same-size training inventories.
- `scripts/129_online_deterministic_reparse_compile.py` - compiles the
  deterministic online parser into a full-corpus formula and promotes it only
  if it beats the active split-only bound with `70/70` roundtrip and no
  row0/semantic claim.
- `scripts/130_online_reparse_order_control_audit.py` - controls the promoted
  online parser against reverse, parity, length-derived, and random book
  orders; numeric order remains best in the tested controls.
- `scripts/131_online_formula_recipe_prune_audit.py` - checks which active
  recipe fields are derivable; book `length` and copy `target_start` can be
  pruned losslessly in a canonical projection.
- `scripts/132_canonical_online_recipe_formula_compile.py` - materializes the
  pruned canonical online formula as the current compact representation of the
  `8343.062` bit bound.
- `scripts/133_literal_length_derived_recipe_compile.py` - derives literal
  op lengths from literal text payload, removing another redundant recipe
  field while retaining copy lengths as declared dependencies.
- `scripts/134_op_type_derived_recipe_compile.py` - derives operation type
  from op field shape, leaving literal text, copy source, and copy length as
  the remaining operation-level recipe dependencies.
- `scripts/135_copy_source_canonicality_audit.py` - checks whether declared
  copy sources are arbitrary; every source is the earliest legal occurrence of
  the copied chunk, while source remains a decoding dependency.
- `scripts/136_copy_length_default_decodability_audit.py` - tests copy-length
  defaults for decodability and promotes a decoder-side default/exception
  copy-length model, lowering the mechanical bound to `8206.178` bits.
- `scripts/137_copy_source_default_decodability_audit.py` - tests a decodable
  previous-source-plus-length default with adaptive exception sources, lowering
  the mechanical bound to `8177.317` bits.
- `scripts/138_literal_payload_default_decodability_audit.py` - tests literal
  payload modal-default/exception candidates and rejects them; the active
  categorical previous-emitted-digit order-2 model remains best.
- `scripts/139_literal_payload_structural_context_audit.py` - tests structural
  literal-run contexts such as offset, run-length bucket, and book half/parity;
  all over-split the stream, so no literal-payload context is promoted.
- `scripts/140_online_copy_source_canonicality_audit.py` - adds controls to
  the copy-source canonicality result: earliest occurrence remains `261/261`,
  while random candidate choice would expect only `169.473` hits.
- `scripts/141_default_exception_prequential_validation.py` - tests the
  promoted copy-length/source default-exception ledgers under prefix, block,
  and family holdout; after the train-count fix, prefix frozen gains are
  positive, but family/bookcase holdouts still include failures.
- `scripts/142_default_exception_component_profile.py` - records `8177.317`
  bits as both `compression_bound` and prefix-frozen generation profile for
  this layer, while keeping the generation claim partial under family holdout.
- `scripts/143_current_literal_payload_profile_audit.py` - retests the old
  literal-payload order-1 profile on the current recipe and retains order-2.
- `scripts/144_copy_source_distance_model_audit.py` - tests backward-distance
  copy-source coding and rejects it; absolute source default/exception remains
  better by `25.551` bits.
- `scripts/145_current_active_prequential_profile_audit.py` - consolidates the
  active `8177.317` bit formula's learned streams; prefix, block, and public
  bookcase family holdouts all beat uniform, while random same-size train
  controls show this is not numeric-order evidence and recipe discovery remains
  unproved.
- `scripts/146_active_reparse_state_boundary_audit.py` - localizes the active
  recipe-discovery blocker: exact reparse with the current copy-source model
  must carry previous-copy source/length state, producing a large state proxy
  rather than the old `(book_pos, previous_item)` DP state.
- `scripts/147_copy_source_state_free_default_audit.py` - tests state-free
  copy-source defaults as a way to remove the previous-copy source/length
  parser state; the best candidate is still `+15.186` bits worse, so the
  active path-dependent source default is retained.
- `scripts/148_copy_length_midpoint_context_audit.py` - validates the fixed
  copy-length midpoint context against a global model, searched boundaries,
  prefix-frozen splits, and book-id permutation controls; midpoint is retained
  as supported context, not a new bound.
- `scripts/149_literal_copy_availability_boundary_audit.py` - separates
  literal runs forced by no legal copy candidate from residual parser choices;
  `73/87` literal starts are forced, leaving `14` optional literal starts as
  the remaining literal recipe frontier.
- `scripts/150_optional_literal_copy_repair_frontier.py` - tests single
  in-literal copy-prefix repairs for the optional literal starts; all `74`
  scored candidates are worse, with the best still `+1.180` bits.
- `scripts/151_cross_op_optional_literal_copy_frontier.py` - allows optional
  literal copy repairs to cross into following operations; all `465` valid
  candidates are still worse, with the best only `+0.027` bits.
- `scripts/152_cross_op_near_tie_decomposition.py` - decomposes the best
  `+0.027` bit cross-op near miss; literal/item savings are almost exactly
  canceled by copy-length/source costs, especially copy source.
- `scripts/153_cross_op_source_break_even_audit.py` - quantifies the
  source-cost break-even for that near miss: a source-free oracle would save
  `11.209` bits, but the active source ledger is `0.027` bits above break-even.
- `reports/` - generated and human-readable outputs.

Translation delta: `NONE`.
