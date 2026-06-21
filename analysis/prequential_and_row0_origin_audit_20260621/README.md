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
- [scripts/14_leave_one_book_out_source_attribution_audit.py](scripts/14_leave_one_book_out_source_attribution_audit.py) - maps singleton holdout copy sources to source books or current prefix.
- [reports/test_results/14_leave_one_book_out_source_attribution_audit.md](reports/test_results/14_leave_one_book_out_source_attribution_audit.md) - singleton source attribution atlas.
- [reports/test_results/14_leave_one_book_out_source_attribution_audit.json](reports/test_results/14_leave_one_book_out_source_attribution_audit.json) - structured singleton source-attribution ledger.
- [scripts/15_leave_one_book_out_book_bounded_source_audit.py](scripts/15_leave_one_book_out_book_bounded_source_audit.py) - retests singleton holdout while forbidding source copies from crossing source-book boundaries.
- [reports/test_results/15_leave_one_book_out_book_bounded_source_audit.md](reports/test_results/15_leave_one_book_out_book_bounded_source_audit.md) - book-bounded singleton source result.
- [reports/test_results/15_leave_one_book_out_book_bounded_source_audit.json](reports/test_results/15_leave_one_book_out_book_bounded_source_audit.json) - structured book-bounded singleton ledger.
- [scripts/16_leave_one_book_out_family_excluded_source_audit.py](scripts/16_leave_one_book_out_family_excluded_source_audit.py) - retests singleton holdout after removing same-family books from train counts and copy sources.
- [reports/test_results/16_leave_one_book_out_family_excluded_source_audit.md](reports/test_results/16_leave_one_book_out_family_excluded_source_audit.md) - family-excluded singleton source result.
- [reports/test_results/16_leave_one_book_out_family_excluded_source_audit.json](reports/test_results/16_leave_one_book_out_family_excluded_source_audit.json) - structured family-excluded singleton ledger.
- [scripts/17_online_prefix_book_frontier_audit.py](scripts/17_online_prefix_book_frontier_audit.py) - decomposes the previous-books-only online parser by target book and adds a book-bounded source variant.
- [reports/test_results/17_online_prefix_book_frontier_audit.md](reports/test_results/17_online_prefix_book_frontier_audit.md) - online prefix book frontier result.
- [reports/test_results/17_online_prefix_book_frontier_audit.json](reports/test_results/17_online_prefix_book_frontier_audit.json) - structured online prefix frontier ledger.
- [scripts/18_online_bootstrap_seed_policy_audit.py](scripts/18_online_bootstrap_seed_policy_audit.py) - tests whether an explicit raw seed for book 0 closes the online cold-start failure.
- [reports/test_results/18_online_bootstrap_seed_policy_audit.md](reports/test_results/18_online_bootstrap_seed_policy_audit.md) - online bootstrap seed policy result.
- [reports/test_results/18_online_bootstrap_seed_policy_audit.json](reports/test_results/18_online_bootstrap_seed_policy_audit.json) - structured bootstrap seed policy ledger.
- [scripts/19_seeded_online_formula_rescore_audit.py](scripts/19_seeded_online_formula_rescore_audit.py) - converts the book-0 seed policy back into formula recipes and rescoring under the complete active ledger.
- [reports/test_results/19_seeded_online_formula_rescore_audit.md](reports/test_results/19_seeded_online_formula_rescore_audit.md) - seeded online formula rescore result.
- [reports/test_results/19_seeded_online_formula_rescore_audit.json](reports/test_results/19_seeded_online_formula_rescore_audit.json) - structured seeded-rescore ledger.
- [scripts/20_seeded_rescore_loss_decomposition.py](scripts/20_seeded_rescore_loss_decomposition.py) - decomposes why the seeded formula fails complete rescoring.
- [reports/test_results/20_seeded_rescore_loss_decomposition.md](reports/test_results/20_seeded_rescore_loss_decomposition.md) - seeded rescore loss decomposition.
- [reports/test_results/20_seeded_rescore_loss_decomposition.json](reports/test_results/20_seeded_rescore_loss_decomposition.json) - structured loss-decomposition ledger.
- [scripts/21_seed_exception_signal_cost_audit.py](scripts/21_seed_exception_signal_cost_audit.py) - tests whether exception signaling can rescue the book-0 seed as a formula promotion.
- [reports/test_results/21_seed_exception_signal_cost_audit.md](reports/test_results/21_seed_exception_signal_cost_audit.md) - seed exception signal-cost result.
- [reports/test_results/21_seed_exception_signal_cost_audit.json](reports/test_results/21_seed_exception_signal_cost_audit.json) - structured seed signal-cost ledger.
- [scripts/22_online_order_frontier_controls.py](scripts/22_online_order_frontier_controls.py) - reruns the book-bounded online frontier under named and random order controls.
- [reports/test_results/22_online_order_frontier_controls.md](reports/test_results/22_online_order_frontier_controls.md) - online order frontier control result.
- [reports/test_results/22_online_order_frontier_controls.json](reports/test_results/22_online_order_frontier_controls.json) - structured online order frontier ledger.
- [scripts/23_order_frontier_promotion_gate.py](scripts/23_order_frontier_promotion_gate.py) - checks whether any non-numeric order-frontier control can promote under the complete formula ledger and descriptor cost.
- [reports/test_results/23_order_frontier_promotion_gate.md](reports/test_results/23_order_frontier_promotion_gate.md) - order frontier promotion-gate result.
- [reports/test_results/23_order_frontier_promotion_gate.json](reports/test_results/23_order_frontier_promotion_gate.json) - structured order-promotion gate ledger.
- [scripts/24_source_blocker_structural_context_gate.py](scripts/24_source_blocker_structural_context_gate.py) - checks whether simple source contexts rescue the cross-op near-tie source blocker.
- [reports/test_results/24_source_blocker_structural_context_gate.md](reports/test_results/24_source_blocker_structural_context_gate.md) - source blocker structural-context gate result.
- [reports/test_results/24_source_blocker_structural_context_gate.json](reports/test_results/24_source_blocker_structural_context_gate.json) - structured source-blocker gate ledger.
- [scripts/25_source_canonicality_decodability_gate.py](scripts/25_source_canonicality_decodability_gate.py) - checks whether earliest-source canonicality removes the decoder source dependency.
- [reports/test_results/25_source_canonicality_decodability_gate.md](reports/test_results/25_source_canonicality_decodability_gate.md) - source canonicality/decodability gate result.
- [reports/test_results/25_source_canonicality_decodability_gate.json](reports/test_results/25_source_canonicality_decodability_gate.json) - structured source-canonicality gate ledger.
- [scripts/26_source_state_dependency_gate.py](scripts/26_source_state_dependency_gate.py) - checks whether state-free source defaults remove previous-copy source/length state.
- [reports/test_results/26_source_state_dependency_gate.md](reports/test_results/26_source_state_dependency_gate.md) - source state-dependency gate result.
- [reports/test_results/26_source_state_dependency_gate.json](reports/test_results/26_source_state_dependency_gate.json) - structured source-state dependency ledger.
- [scripts/27_copy_length_midpoint_context_gate.py](scripts/27_copy_length_midpoint_context_gate.py) - checks whether the copy-length midpoint context generalizes without promoting a searched cutoff.
- [reports/test_results/27_copy_length_midpoint_context_gate.md](reports/test_results/27_copy_length_midpoint_context_gate.md) - copy-length midpoint context gate result.
- [reports/test_results/27_copy_length_midpoint_context_gate.json](reports/test_results/27_copy_length_midpoint_context_gate.json) - structured copy-length midpoint ledger.
- [scripts/28_literal_copy_availability_gate.py](scripts/28_literal_copy_availability_gate.py) - checks how much literal payload is forced by copy unavailability and closes simple local repair families.
- [reports/test_results/28_literal_copy_availability_gate.md](reports/test_results/28_literal_copy_availability_gate.md) - literal copy-availability gate result.
- [reports/test_results/28_literal_copy_availability_gate.json](reports/test_results/28_literal_copy_availability_gate.json) - structured literal externality ledger.
- [scripts/29_literal_payload_model_gate.py](scripts/29_literal_payload_model_gate.py) - checks whether the remaining literal payload model can be simplified after the availability gate.
- [reports/test_results/29_literal_payload_model_gate.md](reports/test_results/29_literal_payload_model_gate.md) - literal payload model gate result.
- [reports/test_results/29_literal_payload_model_gate.json](reports/test_results/29_literal_payload_model_gate.json) - structured literal payload model ledger.
- [scripts/30_recipe_representation_dependency_gate.py](scripts/30_recipe_representation_dependency_gate.py) - checks which compact recipe fields are derivable representation artifacts and which dependencies remain declared.
- [reports/test_results/30_recipe_representation_dependency_gate.md](reports/test_results/30_recipe_representation_dependency_gate.md) - recipe representation dependency gate result.
- [reports/test_results/30_recipe_representation_dependency_gate.json](reports/test_results/30_recipe_representation_dependency_gate.json) - structured recipe dependency ledger.
- [scripts/31_source_selection_derivation_boundary_gate.py](scripts/31_source_selection_derivation_boundary_gate.py) - checks whether canonical copy-source selection becomes decoder-derivable after controls, distance coding, and state-free defaults.
- [reports/test_results/31_source_selection_derivation_boundary_gate.md](reports/test_results/31_source_selection_derivation_boundary_gate.md) - source-selection derivation boundary result.
- [reports/test_results/31_source_selection_derivation_boundary_gate.json](reports/test_results/31_source_selection_derivation_boundary_gate.json) - structured source-selection boundary ledger.
- [scripts/32_copy_length_derivation_boundary_gate.py](scripts/32_copy_length_derivation_boundary_gate.py) - checks whether copy length is decoder-derived or remains declared after target-max, decoder-max, midpoint, and compact-recipe evidence.
- [reports/test_results/32_copy_length_derivation_boundary_gate.md](reports/test_results/32_copy_length_derivation_boundary_gate.md) - copy-length derivation boundary result.
- [reports/test_results/32_copy_length_derivation_boundary_gate.json](reports/test_results/32_copy_length_derivation_boundary_gate.json) - structured copy-length boundary ledger.
- [scripts/33_item_type_op_shape_boundary_gate.py](scripts/33_item_type_op_shape_boundary_gate.py) - separates retained item-type sequence modeling from derivable recipe op-type fields.
- [reports/test_results/33_item_type_op_shape_boundary_gate.md](reports/test_results/33_item_type_op_shape_boundary_gate.md) - item-type/op-shape boundary result.
- [reports/test_results/33_item_type_op_shape_boundary_gate.json](reports/test_results/33_item_type_op_shape_boundary_gate.json) - structured item-type/op-shape boundary ledger.
- [scripts/34_current_active_profile_boundary_gate.py](scripts/34_current_active_profile_boundary_gate.py) - consolidates the current `8177.317`-bit active profile and its recipe-discovery blocker.
- [reports/test_results/34_current_active_profile_boundary_gate.md](reports/test_results/34_current_active_profile_boundary_gate.md) - current active profile boundary result.
- [reports/test_results/34_current_active_profile_boundary_gate.json](reports/test_results/34_current_active_profile_boundary_gate.json) - structured current active profile boundary ledger.
- [scripts/35_copy_source_state_compression_gate.py](scripts/35_copy_source_state_compression_gate.py) - tests whether previous copy source/length state compresses to previous copy end for active source defaults.
- [reports/test_results/35_copy_source_state_compression_gate.md](reports/test_results/35_copy_source_state_compression_gate.md) - copy-source state-compression result.
- [reports/test_results/35_copy_source_state_compression_gate.json](reports/test_results/35_copy_source_state_compression_gate.json) - structured copy-source state-compression ledger.
- [scripts/36_active_reparse_feasibility_after_state_compression_gate.py](scripts/36_active_reparse_feasibility_after_state_compression_gate.py) - checks whether source-state compression changes the active-reparse implementation frontier.
- [reports/test_results/36_active_reparse_feasibility_after_state_compression_gate.md](reports/test_results/36_active_reparse_feasibility_after_state_compression_gate.md) - active-reparse feasibility frontier.
- [reports/test_results/36_active_reparse_feasibility_after_state_compression_gate.json](reports/test_results/36_active_reparse_feasibility_after_state_compression_gate.json) - structured active-reparse feasibility ledger.
- [scripts/37_cutoff60_source_state_reparse_prototype_gate.py](scripts/37_cutoff60_source_state_reparse_prototype_gate.py) - reprices cutoff-60 deterministic reparse recipes with the active previous-copy-end source ledger.
- [reports/test_results/37_cutoff60_source_state_reparse_prototype_gate.md](reports/test_results/37_cutoff60_source_state_reparse_prototype_gate.md) - cutoff-60 source-state reparse prototype.
- [reports/test_results/37_cutoff60_source_state_reparse_prototype_gate.json](reports/test_results/37_cutoff60_source_state_reparse_prototype_gate.json) - structured cutoff-60 source-state prototype ledger.
- [scripts/38_multicutoff_source_state_reparse_reprice_gate.py](scripts/38_multicutoff_source_state_reparse_reprice_gate.py) - repeats source-state repricing over prefix cutoffs `10/20/35/50/60`.
- [reports/test_results/38_multicutoff_source_state_reparse_reprice_gate.md](reports/test_results/38_multicutoff_source_state_reparse_reprice_gate.md) - multi-cutoff source-state reprice result.
- [reports/test_results/38_multicutoff_source_state_reparse_reprice_gate.json](reports/test_results/38_multicutoff_source_state_reparse_reprice_gate.json) - structured multi-cutoff source-state reprice ledger.
- [scripts/39_multicutoff_source_choice_optimizer_gate.py](scripts/39_multicutoff_source_choice_optimizer_gate.py) - tests greedy source substitutions while keeping deterministic reparse segmentation and copy lengths fixed.
- [reports/test_results/39_multicutoff_source_choice_optimizer_gate.md](reports/test_results/39_multicutoff_source_choice_optimizer_gate.md) - fixed-segmentation source-choice optimizer result.
- [reports/test_results/39_multicutoff_source_choice_optimizer_gate.json](reports/test_results/39_multicutoff_source_choice_optimizer_gate.json) - structured source-choice optimizer ledger.
- [scripts/40_multicutoff_global_source_path_optimizer_gate.py](scripts/40_multicutoff_global_source_path_optimizer_gate.py) - optimizes fixed deterministic copy-source choices globally under `previous_copy_end`.
- [reports/test_results/40_multicutoff_global_source_path_optimizer_gate.md](reports/test_results/40_multicutoff_global_source_path_optimizer_gate.md) - global source-path optimizer result.
- [reports/test_results/40_multicutoff_global_source_path_optimizer_gate.json](reports/test_results/40_multicutoff_global_source_path_optimizer_gate.json) - structured global source-path optimizer ledger.
- [scripts/41_full_corpus_source_path_formula_gate.py](scripts/41_full_corpus_source_path_formula_gate.py) - tests whether global source-path substitutions survive the full adaptive source-stream rescore.
- [reports/test_results/41_full_corpus_source_path_formula_gate.md](reports/test_results/41_full_corpus_source_path_formula_gate.md) - full-corpus source-path formula result.
- [reports/test_results/41_full_corpus_source_path_formula_gate.json](reports/test_results/41_full_corpus_source_path_formula_gate.json) - structured full-corpus source-path formula ledger.
- [scripts/42_full_corpus_source_substitution_frontier_gate.py](scripts/42_full_corpus_source_substitution_frontier_gate.py) - exhaustively tests single and pair same-chunk source substitutions under adaptive rescore.
- [reports/test_results/42_full_corpus_source_substitution_frontier_gate.md](reports/test_results/42_full_corpus_source_substitution_frontier_gate.md) - source substitution frontier result.
- [reports/test_results/42_full_corpus_source_substitution_frontier_gate.json](reports/test_results/42_full_corpus_source_substitution_frontier_gate.json) - structured source substitution frontier ledger.
- [scripts/43_full_corpus_source_substitution_second_pass_gate.py](scripts/43_full_corpus_source_substitution_second_pass_gate.py) - reruns the exact single/pair source-substitution frontier on the promoted `8160.827` bit formula.
- [reports/test_results/43_full_corpus_source_substitution_second_pass_gate.md](reports/test_results/43_full_corpus_source_substitution_second_pass_gate.md) - second-pass source substitution result.
- [reports/test_results/43_full_corpus_source_substitution_second_pass_gate.json](reports/test_results/43_full_corpus_source_substitution_second_pass_gate.json) - structured second-pass source substitution ledger.
- [scripts/44_full_corpus_source_substitution_third_pass_gate.py](scripts/44_full_corpus_source_substitution_third_pass_gate.py) - reruns the exact single/pair source-substitution frontier on the promoted `8160.826421` bit formula.
- [reports/test_results/44_full_corpus_source_substitution_third_pass_gate.md](reports/test_results/44_full_corpus_source_substitution_third_pass_gate.md) - third-pass source substitution result.
- [reports/test_results/44_full_corpus_source_substitution_third_pass_gate.json](reports/test_results/44_full_corpus_source_substitution_third_pass_gate.json) - structured third-pass source substitution ledger.
- [scripts/45_full_corpus_source_substitution_fourth_pass_gate.py](scripts/45_full_corpus_source_substitution_fourth_pass_gate.py) - reruns the exact single/pair source-substitution frontier on the promoted `8160.825917` bit formula.
- [reports/test_results/45_full_corpus_source_substitution_fourth_pass_gate.md](reports/test_results/45_full_corpus_source_substitution_fourth_pass_gate.md) - fourth-pass source substitution result.
- [reports/test_results/45_full_corpus_source_substitution_fourth_pass_gate.json](reports/test_results/45_full_corpus_source_substitution_fourth_pass_gate.json) - structured fourth-pass source substitution ledger.
- [scripts/46_source_substitution_saturation_audit.py](scripts/46_source_substitution_saturation_audit.py) - applies an explicit stop rule to repeated same-chunk source-substitution passes without running a fifth pass.
- [reports/test_results/46_source_substitution_saturation_audit.md](reports/test_results/46_source_substitution_saturation_audit.md) - source-substitution saturation decision.
- [reports/test_results/46_source_substitution_saturation_audit.json](reports/test_results/46_source_substitution_saturation_audit.json) - structured source-substitution saturation ledger.
- [scripts/47_row0_parallel_provenance_bridge_audit.py](scripts/47_row0_parallel_provenance_bridge_audit.py) - integrates the independent row0 provenance front into this audit without changing book-generation bits.
- [reports/test_results/47_row0_parallel_provenance_bridge_audit.md](reports/test_results/47_row0_parallel_provenance_bridge_audit.md) - row0 parallel provenance bridge.
- [reports/test_results/47_row0_parallel_provenance_bridge_audit.json](reports/test_results/47_row0_parallel_provenance_bridge_audit.json) - structured row0 provenance bridge ledger.
- [scripts/48_current_formula_dependency_scoreboard.py](scripts/48_current_formula_dependency_scoreboard.py) - re-counts retained dependencies on the latest formula and ranks the next structural blocker.
- [reports/test_results/48_current_formula_dependency_scoreboard.md](reports/test_results/48_current_formula_dependency_scoreboard.md) - current formula dependency scoreboard.
- [reports/test_results/48_current_formula_dependency_scoreboard.json](reports/test_results/48_current_formula_dependency_scoreboard.json) - structured dependency scoreboard ledger.
- [scripts/49_source_length_joint_derivability_audit.py](scripts/49_source_length_joint_derivability_audit.py) - tests whether copy source and copy length become derivable as a joint dependency.
- [reports/test_results/49_source_length_joint_derivability_audit.md](reports/test_results/49_source_length_joint_derivability_audit.md) - source-length joint derivability result.
- [reports/test_results/49_source_length_joint_derivability_audit.json](reports/test_results/49_source_length_joint_derivability_audit.json) - structured source-length joint ledger.
- [scripts/50_source_canonicality_tradeoff_audit.py](scripts/50_source_canonicality_tradeoff_audit.py) - prices the compression-vs-canonicality tradeoff between the current source choices and an all-earliest profile.
- [reports/test_results/50_source_canonicality_tradeoff_audit.md](reports/test_results/50_source_canonicality_tradeoff_audit.md) - source canonicality tradeoff result.
- [reports/test_results/50_source_canonicality_tradeoff_audit.json](reports/test_results/50_source_canonicality_tradeoff_audit.json) - structured source canonicality tradeoff ledger.
- [scripts/51_copy_length_segmentation_exception_audit.py](scripts/51_copy_length_segmentation_exception_audit.py) - maps the non-target-max copy lengths to following-operation intrusion boundaries.
- [reports/test_results/51_copy_length_segmentation_exception_audit.md](reports/test_results/51_copy_length_segmentation_exception_audit.md) - copy-length segmentation exception result.
- [reports/test_results/51_copy_length_segmentation_exception_audit.json](reports/test_results/51_copy_length_segmentation_exception_audit.json) - structured copy-length segmentation ledger.
- [scripts/52_targetmax_resegmentation_candidate_audit.py](scripts/52_targetmax_resegmentation_candidate_audit.py) - tests local target-max resegmentation candidates and scores them as proxy diagnostics.
- [reports/test_results/52_targetmax_resegmentation_candidate_audit.md](reports/test_results/52_targetmax_resegmentation_candidate_audit.md) - target-max resegmentation candidate result.
- [reports/test_results/52_targetmax_resegmentation_candidate_audit.json](reports/test_results/52_targetmax_resegmentation_candidate_audit.json) - structured target-max resegmentation candidate ledger.
- [scripts/53_targetmax_resegmentation_formula_gate.py](scripts/53_targetmax_resegmentation_formula_gate.py) - validates the best target-max resegmentation candidate under the exact active component scorer.
- [reports/test_results/53_targetmax_resegmentation_formula_gate.md](reports/test_results/53_targetmax_resegmentation_formula_gate.md) - target-max resegmentation formula gate.
- [reports/test_results/53_targetmax_resegmentation_formula_gate.json](reports/test_results/53_targetmax_resegmentation_formula_gate.json) - structured target-max resegmentation formula ledger.
- [scripts/54_targetmax_resegmentation_second_pass_gate.py](scripts/54_targetmax_resegmentation_second_pass_gate.py) - retests remaining compatible target-max resegmentations after the first promoted rewrite.
- [reports/test_results/54_targetmax_resegmentation_second_pass_gate.md](reports/test_results/54_targetmax_resegmentation_second_pass_gate.md) - target-max resegmentation second-pass gate.
- [reports/test_results/54_targetmax_resegmentation_second_pass_gate.json](reports/test_results/54_targetmax_resegmentation_second_pass_gate.json) - structured second-pass resegmentation ledger.
- [scripts/55_targetmax_resegmentation_saturation_gate.py](scripts/55_targetmax_resegmentation_saturation_gate.py) - greedily promotes exact target-max resegmentations until the local frontier has no positive candidate.
- [reports/test_results/55_targetmax_resegmentation_saturation_gate.md](reports/test_results/55_targetmax_resegmentation_saturation_gate.md) - target-max resegmentation saturation gate.
- [reports/test_results/55_targetmax_resegmentation_saturation_gate.json](reports/test_results/55_targetmax_resegmentation_saturation_gate.json) - structured target-max saturation ledger.
- [scripts/56_post_targetmax_source_substitution_frontier_gate.py](scripts/56_post_targetmax_source_substitution_frontier_gate.py) - reruns exact same-chunk source substitution after target-max saturation.
- [reports/test_results/56_post_targetmax_source_substitution_frontier_gate.md](reports/test_results/56_post_targetmax_source_substitution_frontier_gate.md) - post-target-max source substitution frontier gate.
- [reports/test_results/56_post_targetmax_source_substitution_frontier_gate.json](reports/test_results/56_post_targetmax_source_substitution_frontier_gate.json) - structured post-target-max source substitution ledger.
- [scripts/57_post_targetmax_source_substitution_second_pass_gate.py](scripts/57_post_targetmax_source_substitution_second_pass_gate.py) - reruns exact same-chunk source substitution on the post-target-max source-substituted formula.
- [reports/test_results/57_post_targetmax_source_substitution_second_pass_gate.md](reports/test_results/57_post_targetmax_source_substitution_second_pass_gate.md) - post-target-max source substitution second-pass gate.
- [reports/test_results/57_post_targetmax_source_substitution_second_pass_gate.json](reports/test_results/57_post_targetmax_source_substitution_second_pass_gate.json) - structured post-target-max second-pass source substitution ledger.
- [scripts/58_post_targetmax_source_substitution_stop_audit.py](scripts/58_post_targetmax_source_substitution_stop_audit.py) - freezes the post-target-max source-substitution micro-frontier as non-mainline under explicit selector-cost checks.
- [reports/test_results/58_post_targetmax_source_substitution_stop_audit.md](reports/test_results/58_post_targetmax_source_substitution_stop_audit.md) - post-target-max source substitution stop decision.
- [reports/test_results/58_post_targetmax_source_substitution_stop_audit.json](reports/test_results/58_post_targetmax_source_substitution_stop_audit.json) - structured post-target-max source stop ledger.
- [scripts/59_active_formula_dependency_refresh_gate.py](scripts/59_active_formula_dependency_refresh_gate.py) - refreshes dependency counts on the active post-target-max formula without searching another source pass.
- [reports/test_results/59_active_formula_dependency_refresh_gate.md](reports/test_results/59_active_formula_dependency_refresh_gate.md) - active formula dependency refresh result.
- [reports/test_results/59_active_formula_dependency_refresh_gate.json](reports/test_results/59_active_formula_dependency_refresh_gate.json) - structured active formula dependency refresh ledger.
- [scripts/60_active_source_length_joint_refresh_gate.py](scripts/60_active_source_length_joint_refresh_gate.py) - retests joint source/length derivability on the active post-target-max formula.
- [reports/test_results/60_active_source_length_joint_refresh_gate.md](reports/test_results/60_active_source_length_joint_refresh_gate.md) - active source/length joint refresh result.
- [reports/test_results/60_active_source_length_joint_refresh_gate.json](reports/test_results/60_active_source_length_joint_refresh_gate.json) - structured active source/length joint refresh ledger.
- [scripts/61_active_copy_length_exception_topology_gate.py](scripts/61_active_copy_length_exception_topology_gate.py) - remaps active target-max copy-length exceptions after promoted resegmentations.
- [reports/test_results/61_active_copy_length_exception_topology_gate.md](reports/test_results/61_active_copy_length_exception_topology_gate.md) - active copy-length exception topology result.
- [reports/test_results/61_active_copy_length_exception_topology_gate.json](reports/test_results/61_active_copy_length_exception_topology_gate.json) - structured active copy-length exception topology ledger.
- [scripts/62_active_residual_targetmax_resegmentation_gate.py](scripts/62_active_residual_targetmax_resegmentation_gate.py) - exact-scores residual local target-max extend-and-trim rewrites on the active formula.
- [reports/test_results/62_active_residual_targetmax_resegmentation_gate.md](reports/test_results/62_active_residual_targetmax_resegmentation_gate.md) - active residual target-max resegmentation result.
- [reports/test_results/62_active_residual_targetmax_resegmentation_gate.json](reports/test_results/62_active_residual_targetmax_resegmentation_gate.json) - structured active residual target-max resegmentation ledger.
- [scripts/63_active_exception_stop_rule_separability_gate.py](scripts/63_active_exception_stop_rule_separability_gate.py) - tests whether simple stop rules separate the remaining active target-max exceptions.
- [reports/test_results/63_active_exception_stop_rule_separability_gate.md](reports/test_results/63_active_exception_stop_rule_separability_gate.md) - active exception stop-rule separability result.
- [reports/test_results/63_active_exception_stop_rule_separability_gate.json](reports/test_results/63_active_exception_stop_rule_separability_gate.json) - structured active exception stop-rule separability ledger.
- [scripts/64_active_exception_finite_state_model_gate.py](scripts/64_active_exception_finite_state_model_gate.py) - tests compact finite-state context models for the residual target-max exceptions.
- [reports/test_results/64_active_exception_finite_state_model_gate.md](reports/test_results/64_active_exception_finite_state_model_gate.md) - active exception finite-state model result.
- [reports/test_results/64_active_exception_finite_state_model_gate.json](reports/test_results/64_active_exception_finite_state_model_gate.json) - structured active exception finite-state ledger.
- [scripts/65_active_exception_partial_boundary_shift_gate.py](scripts/65_active_exception_partial_boundary_shift_gate.py) - exact-scores every partial local boundary shift up to target-max for the residual exceptions.
- [reports/test_results/65_active_exception_partial_boundary_shift_gate.md](reports/test_results/65_active_exception_partial_boundary_shift_gate.md) - active exception partial-boundary result.
- [reports/test_results/65_active_exception_partial_boundary_shift_gate.json](reports/test_results/65_active_exception_partial_boundary_shift_gate.json) - structured partial-boundary ledger.
- [scripts/66_partial_boundary_shift_formula_gate.py](scripts/66_partial_boundary_shift_formula_gate.py) - promotes the best exact-scored partial boundary shift into a formula.
- [reports/test_results/66_partial_boundary_shift_formula_gate.md](reports/test_results/66_partial_boundary_shift_formula_gate.md) - partial-boundary formula gate.
- [reports/test_results/66_partial_boundary_shift_formula_gate.json](reports/test_results/66_partial_boundary_shift_formula_gate.json) - structured partial-boundary promotion ledger.
- [scripts/67_partial_boundary_shift_second_pass_gate.py](scripts/67_partial_boundary_shift_second_pass_gate.py) - reruns partial-shift scoring after the first partial-boundary promotion.
- [reports/test_results/67_partial_boundary_shift_second_pass_gate.md](reports/test_results/67_partial_boundary_shift_second_pass_gate.md) - partial-boundary second-pass result.
- [reports/test_results/67_partial_boundary_shift_second_pass_gate.json](reports/test_results/67_partial_boundary_shift_second_pass_gate.json) - structured second-pass partial-boundary ledger.
- [scripts/68_partial_boundary_shift_second_pass_formula_gate.py](scripts/68_partial_boundary_shift_second_pass_formula_gate.py) - promotes the second-pass partial-boundary shift into a formula.
- [reports/test_results/68_partial_boundary_shift_second_pass_formula_gate.md](reports/test_results/68_partial_boundary_shift_second_pass_formula_gate.md) - second-pass partial-boundary formula gate.
- [reports/test_results/68_partial_boundary_shift_second_pass_formula_gate.json](reports/test_results/68_partial_boundary_shift_second_pass_formula_gate.json) - structured second-pass promotion ledger.
- [scripts/69_partial_boundary_shift_saturation_gate.py](scripts/69_partial_boundary_shift_saturation_gate.py) - closes the partial-boundary shift family after the two promotions.
- [reports/test_results/69_partial_boundary_shift_saturation_gate.md](reports/test_results/69_partial_boundary_shift_saturation_gate.md) - partial-boundary saturation result.
- [reports/test_results/69_partial_boundary_shift_saturation_gate.json](reports/test_results/69_partial_boundary_shift_saturation_gate.json) - structured partial-boundary saturation ledger.
- [scripts/70_recent_formula_row0_compatibility_audit.py](scripts/70_recent_formula_row0_compatibility_audit.py) - checks whether the latest book-formula promotions change the independent row0-origin conclusion.
- [reports/test_results/70_recent_formula_row0_compatibility_audit.md](reports/test_results/70_recent_formula_row0_compatibility_audit.md) - recent formula / row0 compatibility result.
- [reports/test_results/70_recent_formula_row0_compatibility_audit.json](reports/test_results/70_recent_formula_row0_compatibility_audit.json) - structured compatibility ledger.
- [scripts/71_final_formula_dependency_refresh_gate.py](scripts/71_final_formula_dependency_refresh_gate.py) - refreshes the source/length dependency scoreboard on the final `8154.676268`-bit formula.
- [reports/test_results/71_final_formula_dependency_refresh_gate.md](reports/test_results/71_final_formula_dependency_refresh_gate.md) - final formula dependency refresh.
- [reports/test_results/71_final_formula_dependency_refresh_gate.json](reports/test_results/71_final_formula_dependency_refresh_gate.json) - structured final dependency ledger.
- [scripts/72_final_source_length_parser_feasibility_audit.py](scripts/72_final_source_length_parser_feasibility_audit.py) - recomputes source/length parser state and transition proxies on the final formula.
- [reports/test_results/72_final_source_length_parser_feasibility_audit.md](reports/test_results/72_final_source_length_parser_feasibility_audit.md) - final parser feasibility audit.
- [reports/test_results/72_final_source_length_parser_feasibility_audit.json](reports/test_results/72_final_source_length_parser_feasibility_audit.json) - structured parser feasibility ledger.
- [scripts/73_book_local_source_length_parser_probe.py](scripts/73_book_local_source_length_parser_probe.py) - executes the active source/length DP on two cutoff-60 books before attacking the hard case.
- [reports/test_results/73_book_local_source_length_parser_probe.md](reports/test_results/73_book_local_source_length_parser_probe.md) - book-local parser probe.
- [reports/test_results/73_book_local_source_length_parser_probe.json](reports/test_results/73_book_local_source_length_parser_probe.json) - structured parser probe ledger.
- [scripts/74_sparse_hard_book_source_length_parser_gate.py](scripts/74_sparse_hard_book_source_length_parser_gate.py) - replaces dense DP with sparse Dijkstra on the cutoff-60 hard book `66`.
- [reports/test_results/74_sparse_hard_book_source_length_parser_gate.md](reports/test_results/74_sparse_hard_book_source_length_parser_gate.md) - sparse hard-book parser result.
- [reports/test_results/74_sparse_hard_book_source_length_parser_gate.json](reports/test_results/74_sparse_hard_book_source_length_parser_gate.json) - structured sparse parser ledger.
- [scripts/75_post_parser_row0_compatibility_audit.py](scripts/75_post_parser_row0_compatibility_audit.py) - checks whether gates 71-74 change row0 origin or only advance the downstream book formula/parser.
- [reports/test_results/75_post_parser_row0_compatibility_audit.md](reports/test_results/75_post_parser_row0_compatibility_audit.md) - post-parser row0 compatibility result.
- [reports/test_results/75_post_parser_row0_compatibility_audit.json](reports/test_results/75_post_parser_row0_compatibility_audit.json) - structured post-parser compatibility ledger.
- [scripts/76_cutoff60_sparse_suffix_parser_gate.py](scripts/76_cutoff60_sparse_suffix_parser_gate.py) - runs the sparse source/length parser over the full cutoff-60 suffix with previous-copy-end state carried between books.
- [reports/test_results/76_cutoff60_sparse_suffix_parser_gate.md](reports/test_results/76_cutoff60_sparse_suffix_parser_gate.md) - cutoff-60 sparse suffix parser result.
- [reports/test_results/76_cutoff60_sparse_suffix_parser_gate.json](reports/test_results/76_cutoff60_sparse_suffix_parser_gate.json) - structured sparse suffix parser ledger.
- [scripts/77_multi_cutoff_sparse_suffix_parser_validation.py](scripts/77_multi_cutoff_sparse_suffix_parser_validation.py) - repeats the sparse suffix parser over cutoffs `10/20/35/50/60` with frozen prefix counts.
- [reports/test_results/77_multi_cutoff_sparse_suffix_parser_validation.md](reports/test_results/77_multi_cutoff_sparse_suffix_parser_validation.md) - multi-cutoff sparse suffix validation result.
- [reports/test_results/77_multi_cutoff_sparse_suffix_parser_validation.json](reports/test_results/77_multi_cutoff_sparse_suffix_parser_validation.json) - structured multi-cutoff validation ledger.
- [scripts/78_multi_cutoff_parser_path_stability_audit.py](scripts/78_multi_cutoff_parser_path_stability_audit.py) - checks whether exact parser paths stay invariant for the same book across different frozen cutoffs.
- [reports/test_results/78_multi_cutoff_parser_path_stability_audit.md](reports/test_results/78_multi_cutoff_parser_path_stability_audit.md) - multi-cutoff parser path-stability result.
- [reports/test_results/78_multi_cutoff_parser_path_stability_audit.json](reports/test_results/78_multi_cutoff_parser_path_stability_audit.json) - structured path-stability ledger.
- [scripts/79_unstable_parser_path_decomposition_audit.py](scripts/79_unstable_parser_path_decomposition_audit.py) - decomposes the unstable parser paths into source-only, boundary-shift, or segmentation-change classes.
- [reports/test_results/79_unstable_parser_path_decomposition_audit.md](reports/test_results/79_unstable_parser_path_decomposition_audit.md) - unstable path decomposition result.
- [reports/test_results/79_unstable_parser_path_decomposition_audit.json](reports/test_results/79_unstable_parser_path_decomposition_audit.json) - structured unstable-path decomposition ledger.
- [scripts/80_boundary_policy_stability_gate.py](scripts/80_boundary_policy_stability_gate.py) - tests fixed simple boundary policies against the unstable path variants with cross-cutoff repricing.
- [reports/test_results/80_boundary_policy_stability_gate.md](reports/test_results/80_boundary_policy_stability_gate.md) - boundary policy stability result.
- [reports/test_results/80_boundary_policy_stability_gate.json](reports/test_results/80_boundary_policy_stability_gate.json) - structured boundary-policy scoreboard.
- [scripts/81_boundary_instability_cost_decomposition_gate.py](scripts/81_boundary_instability_cost_decomposition_gate.py) - decomposes winner-vs-variant boundary instability costs by coding component.
- [reports/test_results/81_boundary_instability_cost_decomposition_gate.md](reports/test_results/81_boundary_instability_cost_decomposition_gate.md) - boundary instability cost decomposition result.
- [reports/test_results/81_boundary_instability_cost_decomposition_gate.json](reports/test_results/81_boundary_instability_cost_decomposition_gate.json) - structured component-delta ledger.
- [scripts/82_component_neutralized_path_stability_gate.py](scripts/82_component_neutralized_path_stability_gate.py) - reruns multi-cutoff path stability after uniformizing learned copy-length/source-exception costs.
- [reports/test_results/82_component_neutralized_path_stability_gate.md](reports/test_results/82_component_neutralized_path_stability_gate.md) - component-neutralized path stability result.
- [reports/test_results/82_component_neutralized_path_stability_gate.json](reports/test_results/82_component_neutralized_path_stability_gate.json) - structured component-neutralization ledger.
- [scripts/83_component_neutralized_residual_tradeoff_audit.py](scripts/83_component_neutralized_residual_tradeoff_audit.py) - localizes resolved, persistent, introduced, and full-source residual instabilities after component neutralization.
- [reports/test_results/83_component_neutralized_residual_tradeoff_audit.md](reports/test_results/83_component_neutralized_residual_tradeoff_audit.md) - residual tradeoff result.
- [reports/test_results/83_component_neutralized_residual_tradeoff_audit.json](reports/test_results/83_component_neutralized_residual_tradeoff_audit.json) - structured residual tradeoff ledger.
- [scripts/84_residual_literal_payload_neutralization_gate.py](scripts/84_residual_literal_payload_neutralization_gate.py) - tests uniform literal-payload cost on top of the copy-length/source-exception neutralized parser.
- [reports/test_results/84_residual_literal_payload_neutralization_gate.md](reports/test_results/84_residual_literal_payload_neutralization_gate.md) - residual literal-payload neutralization result.
- [reports/test_results/84_residual_literal_payload_neutralization_gate.json](reports/test_results/84_residual_literal_payload_neutralization_gate.json) - structured residual literal-payload ledger.
- [scripts/85_book49_residual_split_cause_audit.py](scripts/85_book49_residual_split_cause_audit.py) - localizes the remaining book `49` residual as a prefix split and tests fixed local item/literal-length controls.
- [reports/test_results/85_book49_residual_split_cause_audit.md](reports/test_results/85_book49_residual_split_cause_audit.md) - book `49` residual split cause result.
- [reports/test_results/85_book49_residual_split_cause_audit.json](reports/test_results/85_book49_residual_split_cause_audit.json) - structured book `49` residual split ledger.
- [scripts/86_global_item_literal_length_control_gate.py](scripts/86_global_item_literal_length_control_gate.py) - applies the book `49` local item/literal-length controls globally.
- [reports/test_results/86_global_item_literal_length_control_gate.md](reports/test_results/86_global_item_literal_length_control_gate.md) - global item/literal-length control result.
- [reports/test_results/86_global_item_literal_length_control_gate.json](reports/test_results/86_global_item_literal_length_control_gate.json) - structured global item/literal-length control ledger.
- [scripts/87_stable_path_projection_boundary_audit.py](scripts/87_stable_path_projection_boundary_audit.py) - tests whether the stable no-item/no-literal-length path projection can be promoted as a generator.
- [reports/test_results/87_stable_path_projection_boundary_audit.md](reports/test_results/87_stable_path_projection_boundary_audit.md) - stable path projection boundary result.
- [reports/test_results/87_stable_path_projection_boundary_audit.json](reports/test_results/87_stable_path_projection_boundary_audit.json) - structured stable path projection boundary ledger.
- [scripts/88_decoder_side_rule_coverage_audit.py](scripts/88_decoder_side_rule_coverage_audit.py) - tests simple decoder-side source/length rules against the stable path projection.
- [reports/test_results/88_decoder_side_rule_coverage_audit.md](reports/test_results/88_decoder_side_rule_coverage_audit.md) - decoder-side rule coverage result.
- [reports/test_results/88_decoder_side_rule_coverage_audit.json](reports/test_results/88_decoder_side_rule_coverage_audit.json) - structured decoder-side rule coverage ledger.
- [scripts/89_source_tiebreak_artifact_audit.py](scripts/89_source_tiebreak_artifact_audit.py) - tests whether the `208/208` earliest-target-match source signal is only parser tie-break.
- [reports/test_results/89_source_tiebreak_artifact_audit.md](reports/test_results/89_source_tiebreak_artifact_audit.md) - source tie-break artifact result.
- [reports/test_results/89_source_tiebreak_artifact_audit.json](reports/test_results/89_source_tiebreak_artifact_audit.json) - structured source tie-break artifact ledger.
- [scripts/90_source_candidate_collapse_audit.py](scripts/90_source_candidate_collapse_audit.py) - checks whether `precompute_matches` already collapses source candidates to earliest per length.
- [reports/test_results/90_source_candidate_collapse_audit.md](reports/test_results/90_source_candidate_collapse_audit.md) - source candidate collapse correction.
- [reports/test_results/90_source_candidate_collapse_audit.json](reports/test_results/90_source_candidate_collapse_audit.json) - structured source candidate collapse ledger.
- [scripts/91_full_source_exposure_audit.py](scripts/91_full_source_exposure_audit.py) - exposes all same-length source candidates on the cutoff-60 stable projection.
- [reports/test_results/91_full_source_exposure_audit.md](reports/test_results/91_full_source_exposure_audit.md) - full source exposure cutoff-60 result.
- [reports/test_results/91_full_source_exposure_audit.json](reports/test_results/91_full_source_exposure_audit.json) - structured full source exposure ledger.
- [scripts/92_full_source_latest_multicutoff_probe.py](scripts/92_full_source_latest_multicutoff_probe.py) - probes latest-source full source exposure on cutoffs `50/60`.
- [reports/test_results/92_full_source_latest_multicutoff_probe.md](reports/test_results/92_full_source_latest_multicutoff_probe.md) - full source latest multi-cutoff probe result.
- [reports/test_results/92_full_source_latest_multicutoff_probe.json](reports/test_results/92_full_source_latest_multicutoff_probe.json) - structured full source latest multi-cutoff ledger.
- [scripts/93_full_source_all_policy_multicutoff_probe.py](scripts/93_full_source_all_policy_multicutoff_probe.py) - compares all source tie policies with all same-length sources exposed on cutoffs `50/60`.
- [reports/test_results/93_full_source_all_policy_multicutoff_probe.md](reports/test_results/93_full_source_all_policy_multicutoff_probe.md) - full source all-policy multi-cutoff probe result.
- [reports/test_results/93_full_source_all_policy_multicutoff_probe.json](reports/test_results/93_full_source_all_policy_multicutoff_probe.json) - structured full source all-policy multi-cutoff ledger.
- [scripts/94_full_source_all_policy_fivecutoff_probe.py](scripts/94_full_source_all_policy_fivecutoff_probe.py) - extends all-policy full-source exposure to cutoffs `10/20/35/50/60`.
- [reports/test_results/94_full_source_all_policy_fivecutoff_probe.md](reports/test_results/94_full_source_all_policy_fivecutoff_probe.md) - full source all-policy five-cutoff probe result.
- [reports/test_results/94_full_source_all_policy_fivecutoff_probe.json](reports/test_results/94_full_source_all_policy_fivecutoff_probe.json) - structured full source all-policy five-cutoff ledger.
- [scripts/95_full_source_policy_invariance_boundary.py](scripts/95_full_source_policy_invariance_boundary.py) - checks whether all-policy stability demotes source choice itself.
- [reports/test_results/95_full_source_policy_invariance_boundary.md](reports/test_results/95_full_source_policy_invariance_boundary.md) - source-policy invariance boundary result.
- [reports/test_results/95_full_source_policy_invariance_boundary.json](reports/test_results/95_full_source_policy_invariance_boundary.json) - structured source-policy invariance boundary ledger.
- [scripts/96_full_source_canonical_policy_boundary.py](scripts/96_full_source_canonical_policy_boundary.py) - tests whether any static source tie policy can be frozen without cost.
- [reports/test_results/96_full_source_canonical_policy_boundary.md](reports/test_results/96_full_source_canonical_policy_boundary.md) - canonical source-policy boundary result.
- [reports/test_results/96_full_source_canonical_policy_boundary.json](reports/test_results/96_full_source_canonical_policy_boundary.json) - structured canonical source-policy boundary ledger.
- [scripts/97_source_policy_selector_boundary.py](scripts/97_source_policy_selector_boundary.py) - tests whether a minimal book-specific source-policy selector should be promoted.
- [reports/test_results/97_source_policy_selector_boundary.md](reports/test_results/97_source_policy_selector_boundary.md) - source-policy selector boundary result.
- [reports/test_results/97_source_policy_selector_boundary.json](reports/test_results/97_source_policy_selector_boundary.json) - structured source-policy selector ledger.
- [scripts/98_full_source_exact_skeleton_invariance.py](scripts/98_full_source_exact_skeleton_invariance.py) - checks exact source-free operation skeleton invariance across policies and cutoffs.
- [reports/test_results/98_full_source_exact_skeleton_invariance.md](reports/test_results/98_full_source_exact_skeleton_invariance.md) - exact source-free skeleton invariance result.
- [reports/test_results/98_full_source_exact_skeleton_invariance.json](reports/test_results/98_full_source_exact_skeleton_invariance.json) - structured exact skeleton invariance ledger.
- [scripts/99_exact_skeleton_dependency_ledger.py](scripts/99_exact_skeleton_dependency_ledger.py) - converts the invariant skeleton into an explicit dependency ledger.
- [reports/test_results/99_exact_skeleton_dependency_ledger.md](reports/test_results/99_exact_skeleton_dependency_ledger.md) - exact skeleton dependency ledger result.
- [reports/test_results/99_exact_skeleton_dependency_ledger.json](reports/test_results/99_exact_skeleton_dependency_ledger.json) - structured exact skeleton dependency ledger.
- [scripts/100_skeleton_rule_coverage_audit.py](scripts/100_skeleton_rule_coverage_audit.py) - tests whether simple decoder-visible rules generate the exact skeleton.
- [reports/test_results/100_skeleton_rule_coverage_audit.md](reports/test_results/100_skeleton_rule_coverage_audit.md) - skeleton rule coverage result.
- [reports/test_results/100_skeleton_rule_coverage_audit.json](reports/test_results/100_skeleton_rule_coverage_audit.json) - structured skeleton rule coverage ledger.
- [scripts/101_skeleton_template_reuse_audit.py](scripts/101_skeleton_template_reuse_audit.py) - checks whether repeated skeleton templates reduce the atlas.
- [reports/test_results/101_skeleton_template_reuse_audit.md](reports/test_results/101_skeleton_template_reuse_audit.md) - skeleton template reuse result.
- [reports/test_results/101_skeleton_template_reuse_audit.json](reports/test_results/101_skeleton_template_reuse_audit.json) - structured skeleton template reuse ledger.
- [scripts/102_type_motif_library_ledger.py](scripts/102_type_motif_library_ledger.py) - prices repeated operation-type motifs against the exact skeleton atlas.
- [reports/test_results/102_type_motif_library_ledger.md](reports/test_results/102_type_motif_library_ledger.md) - type motif library ledger result.
- [reports/test_results/102_type_motif_library_ledger.json](reports/test_results/102_type_motif_library_ledger.json) - structured type motif library ledger.
- [scripts/103_copy_availability_type_exception_ledger.py](scripts/103_copy_availability_type_exception_ledger.py) - tests target-dependent copy availability as an operation-type exception ledger.
- [reports/test_results/103_copy_availability_type_exception_ledger.md](reports/test_results/103_copy_availability_type_exception_ledger.md) - copy-availability type exception result.
- [reports/test_results/103_copy_availability_type_exception_ledger.json](reports/test_results/103_copy_availability_type_exception_ledger.json) - structured copy-availability type exception ledger.

## Boundary

- Full-source exposure result: exposing every same-length source candidate and
  comparing all three tie policies on cutoffs `50/60` preserves `30/30`
  roundtrip/raw-positive evaluations per policy and `10/10` multi-cutoff-stable
  books per policy. This is partial parser robustness only. It does not emit a
  source-generation formula, change `row0`, or change the `8154.676268`-bit
  compression bound.
- Full-source five-cutoff result: extending that same exposed-source test to
  cutoffs `10/20/35/50/60` preserves `175/175` roundtrip/raw-positive
  evaluations per policy and `50/50` multi-cutoff-stable books per policy, with
  `0/150` unstable policy-book cases. This strengthens parser robustness but
  still does not make source choice decoder-derived or row0-derived.
- Source-policy invariance boundary: comparing the three policies case-by-case
  shows exact source-bearing signatures are invariant in only `48/175` cases.
  Operation shape is invariant in `175/175`, so the result is shape robustness
  with `127/175` pure source-choice variants, not source-dependency removal.
- Canonical source-policy boundary: no static tie policy is cost-safe across the
  `175` gate-95 cases. `earliest_source` and
  `prefer_previous_end_then_earliest` are min-cost in `170/175`, but
  `latest_source` is cheaper on five book-`63` cases; freezing a static policy
  would require either paying bits or adding a selector.
- Source-policy selector boundary: the obvious selector (`latest_source` only on
  book `63`, `earliest_source` otherwise) matches the per-case policy minimum
  and has a positive lower-bound bit balance after a simple selector floor, but
  it is book-specific and leaves source fields materialized, so it is audit-only.
- Exact source-free skeleton boundary: after removing source addresses and
  source-default flags, operation type/target/length/forced skeletons are
  invariant in `175/175` policy-cutoff cases and `60/60` books. This is a real
  segmentation atlas (`261` ops, `208` copies, `53` literal runs), but source
  fields and literal payload remain outside the decoder.
- Exact skeleton dependency ledger: the skeleton atlas moves operation type and
  length into `261` stable skeleton records, leaving `208` copy-source fields and
  `53` literal payload chunks external. Residual external fields drop from `609`
  active fields to `261`, but total materialized atlas+external records are
  still `522`, so no decoder-side generator is promoted.
- Skeleton rule coverage boundary: simple decoder-visible rules do not generate
  the skeleton. The best op-type rule is the trivial `always_copy` at `208/261`,
  the best length rule covers `116/261`, and target-dependent copy availability
  also reaches only `208/261`; the skeleton remains an atlas.
- Skeleton template reuse boundary: exact length/target skeleton reuse is sparse
  (`58` unique templates across `60` books, with only two reused pairs). Type
  sequences show motifs (`28` templates, `39` reused books), but length-bearing
  templates do not reduce the atlas to a small reusable library.
- Type motif library boundary: pricing those repeated type motifs directly gives
  `193` type entries plus `60` book assignments, saving only `8` records before
  residuals. The representation still requires `261` residual length/target
  records, for `514` total records (`+253` vs the exact skeleton atlas), so no
  type-motif library is promoted.
- Copy-availability type boundary: target-dependent copy availability contains
  every copy event (`208/208`) and forces `36` literals, leaving only `17`
  available-copy literal exceptions. This beats shuffled controls, but it still
  depends on target text/copy availability and yields `278` conditioned skeleton
  records (`+17` vs exact atlas), so it is `AUDIT_ONLY`.
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
  `96.055` bits. Source attribution for that singleton audit maps `11062`
  copied digits to source books or current prefix; `3001` copied digits cross
  artificial source-book boundaries in the concatenated complement inventory.
  A book-bounded singleton reparse forbids those crossings and still beats raw
  digit coding in `70/70` books, with mean gain `464.898` bits. A stricter
  family-excluded singleton reparse removes same-family books from train counts
  and copy sources; it still beats raw digit coding in `70/70` books and in
  `46/46` family-labeled books, with mean gain `460.251` bits. A per-book
  online-prefix frontier audit then tests true previous-books-only generation:
  book-bounded online reparsing beats raw in `69/70`, and the only failure is
  the cold-start book `0`; after bootstrap it wins in `69/69`. A bootstrap
  seed-policy audit charges book `0` as an explicit raw seed and closes the
  local failure as `70/70` wins-or-ties, while not promoting a new compression
  bound or authorial proof. A full formula rescore then rejects promotion:
  seeded online is `+0.979` bits worse than the existing `8343.062`-bit online
  formula, and the book-bounded seeded formula is `+305.198` bits worse. The
  loss decomposition explains the mismatch: the seed saves `36.842` non-payload
  bits but adds `37.821` literal-payload bits under full scoring. Exception
  signaling cannot rescue promotion: even a zero-cost deterministic fallback is
  `+0.979` bits worse, and promotion would require a negative descriptor cost.
  Order-frontier controls then show the online prefix result is predictive but
  not numeric-order-unique: numeric keeps `69/69` after-bootstrap raw wins, but
  `10/11` tested orders do too, including `6/6` seeded random orders; `random_04`
  beats numeric by `+0.549` bits in mean after-bootstrap gain and `+61.452` bits
  in total gain. A promotion gate then checks the complete online formula
  ledger: `random_04` is `+188.584` bits worse before descriptor cost and
  `+521.038` bits worse after descriptor cost, leaving `0` promotable
  non-numeric orders. A source-blocker gate then closes the simple-context
  rescue for the tight cross-op near tie: the candidate is only `+0.027` bits
  worse and a source-free oracle would be `-11.209` bits, but the best
  decodable simple source context (`book_half`) is `+5.872` bits worse than
  global and loses all `5/5` prefix-frozen checks. A canonicality/decodability
  gate then separates encoder regularity from decoder derivation: every source
  is the earliest legal occurrence of the copied chunk (`261/261`), but the rule
  depends on future target text, `138/261` source choices remain ambiguous at
  declared length, and the decoder source dependency is not removed. A
  source-state dependency gate then rejects state-free defaults as a replacement
  for the active previous-copy source/length default: the best rule is
  `+15.186` bits worse and loses all `5/5` prefix-frozen checks. A source-
  selection derivation boundary gate then confirms `261/261` earliest-source
  canonicality while rejecting decoder derivation, backward distance, and
  state-free replacements. A copy-length derivation boundary gate then keeps
  decoder-max/default exceptions and midpoint context while rejecting target-max
  as encoder-only and retaining declared copy-length fields. A copy-length
  midpoint context gate then keeps the natural `book_id < 35` split: it beats
  global by `13.839` bits, wins all `5/5` prefix-frozen checks, passes
  permutation controls (`p=0.0033`), and rejects searched cutoff `37`. A
  literal copy-availability gate then reduces literal externality: `73/87`
  literal starts and `760/857` literal digits are forced by no legal copy
  candidate, while in-literal and cross-op local repairs remain worse. A
  literal payload model gate then retains the active order-2 previous-emitted-
  digit model: order-1 is worse on full corpus and aggregate prefix totals, and
  modal default/exception plus simple structural contexts are also worse. A
  recipe representation dependency gate then removes derivable book length,
  copy target start, literal length, and op type fields while retaining literal
  text, copy source, and copy length as declared dependencies. An item-type/
  op-shape boundary gate then keeps the split-only item-type stream while
  clarifying that explicit compact-recipe op `type` fields are derivable from
  operation shape. A current-active-profile boundary gate then consolidates
  the `8177.317`-bit active profile: all tested prefix, block, and
  public-bookcase family frozen gains are positive, but exact active reparse is
  still blocked by path-dependent copy-source state. A copy-source state
  compression gate then reduces that state from previous `(source, length)` to
  `previous_copy_end`, preserving the active default/exception ledger and
  cutting the aggregate candidate-state proxy by `97.239%`, but without
  promoting a complete parser. A feasibility follow-up then shows the
  compressed source-state frontier is small enough for book-local prototyping by
  proxy: every tested book-level end-state proxy is below one million and
  cutoff `60` has `9/10` books below `250000`. The complete active parser is
  still unpromoted. A full-corpus source-path formula gate then converts part
  of that path-state signal into a fixed-recipe formula improvement: changing
  `2/261` source positions lowers the adaptive copy-source stream enough to
  move the active mechanical bound from `8177.317` to `8162.412` bits. This
  remains fixed in segmentation and copy lengths, so the complete parser is
  still unpromoted. A single/pair source-substitution frontier then searches
  `376` singles and `69849` pairs exactly under adaptive rescore and lowers the
  bound again from `8162.412` to `8160.827` bits; triples and higher-order
  substitutions remain unsearched. A second pass finds only a microscopic
  `+0.000671` bit gain, lowering the bound to `8160.826421`; this is a
  compression-bound update, not stronger generation evidence. A third pass
  finds another microscopic `+0.000503` bit gain, lowering the bound to
  `8160.825917` and reinforcing local source-frontier saturation. A fourth
  pass adds only `+0.000310` bits, lowering the bound to `8160.825608`; this
  further supports local source-frontier saturation. A saturation audit then
  freezes repeated local same-chunk source substitutions as no longer mainline:
  the last three gains sum to only `0.001484` bits and are dwarfed by
  selector-cost sanity checks. A row0 parallel provenance bridge then imports
  the independent provenance front: local workbook/import/reconstruction/audit
  layers are traced, but CipSoft origin remains untraced and paid worksheet
  anchors do not beat lookup once pair and label costs are charged. A current
  formula dependency scoreboard then re-counts the latest formula directly:
  `87` literal payload fields, `261` copy-source fields, and `261` copy-length
  fields remain declared; the next mainline mechanical test is structural
  source/length parsing rather than literal or item-type refinement. A
  source-length joint derivability audit then checks that target directly: the
  latest source-substituted formula no longer preserves the earlier `261/261`
  all-earliest source pattern (`251/261` current), joint
  earliest+target-max covers `230/261` but is encoder-oracle only, and the
  decoder-valid declared-source+decoder-max rule covers only `60/261`. Source
  and length therefore remain declared dependencies. A source canonicality
  tradeoff audit then prices the cleaner all-earliest explanation profile:
  restoring `10` non-earliest current sources raises the total from
  `8160.825608` to `8177.316653` bits (`+16.491045`), so the current bound and
  the simpler generation-explanation profile remain separate ledgers. A
  copy-length segmentation exception audit then maps the `23` target-max
  exceptions: every one enters exactly one following op and stops inside it,
  absorbing `0` whole following ops. This makes copy length a joint
  resegmentation problem rather than a scalar default problem. A local
  target-max resegmentation candidate audit then tests the direct rewrite:
  `42/46` candidates are valid, `5` are proxy improvements, and the best proxy
  candidate is `-2.059513` bits at book `9` op `0`. The exact formula gate
  then validates that candidate against the active component scorer: it
  reproduces the current `8160.825608`-bit bound and promotes the same
  resegmentation to `8158.766094` bits, a `+2.059513`-bit compression-bound
  gain. A second exact gate then retests remaining compatible candidates and
  promotes book `2` op `9`, lowering the bound again to `8157.065654` bits
  (`+1.700440`). A saturation gate then promotes the final two exact positive
  target-max resegmentations and closes this local frontier at `8156.050355`
  bits, with `0` exact improving candidates left. These changes affect neither
  `row0` origin nor semantics. Rerunning same-chunk source substitutions after
  that saturation finds a microscopic pair gain and moves the bound to
  `8156.050167` bits; a second pass moves it to `8156.049986` bits. These
  are fixed-recipe compression bookkeeping only. The stop audit freezes this
  micro-frontier as non-mainline: the cumulative gain is `0.000369` bits, and
  selector-cost sanity checks dominate. The active-formula dependency refresh
  then confirms that the bound improved by `4.775621` bits since the gate-48
  formula, but declared recipe dependencies remain unchanged at `609` fields;
  only one digit moved from literal payload to copied payload. The active
  source/length joint refresh then shows the same boundary from another angle:
  encoder target-max hits improve by `+4`, but decoder-valid joint rules remain
  unchanged. The active copy-length exception topology gate then maps the
  residual frontier: target-max exceptions drop from `23` to `19`, but all
  `19` remaining exceptions still cross into exactly one following op and stop
  inside it. The residual target-max resegmentation gate exact-scores all `38`
  local rewrites for those exceptions and finds `0` improving candidates; the
  best valid rewrite is still `-0.000163` bits worse. A stop-rule separability
  gate then tests simple single-feature and pairwise conjunction rules over all
  `261` copy events. It finds `0` exact separators for the `19` residual
  boundaries; the best rule has F1 `0.265060`, many false positives, and is not
  decoder-valid. A finite-state follow-up then tests `231` compact online
  context models over decoder-valid features; the best costs `112.749463` bits,
  which is `+17.943077` bits worse than an explicit exception list, with
  permutation `p=0.638000`. The missing local-window case is then tested:
  every positive partial shift up to target-max inside the same two-operation
  window. That gate scores `229` candidates, finds `213` valid and `2`
  improving. The promotion gate materializes the best one, book `10` op `0`
  with `preserve_next_mode` and delta `3` of slack `72`, lowering the active
  bound from `8156.049986` to `8155.261037` bits with `70/70` roundtrip and
  zero score errors. A second pass then finds one more exact improvement: book
  `46` op `1`, `preserve_next_mode`, delta `1` of slack `3`, lowering the bound
  again to `8154.676268` bits. A saturation gate then tests the remaining
  `221` partial-shift candidates and finds `0` improvements; the best remaining
  valid candidate is still `-0.000163` bits worse.
  The complete parser is still unpromoted because the full active objective, adaptive counts, tie
  breaking, source/length dependencies, literal payload, and item-type ledger
  remain unresolved. A cutoff-60 prototype then reprices deterministic reparse
  recipes with the active `previous_copy_end` source ledger: `10/10` books
  roundtrip, `10/10` beat raw digit coding, and aggregate cost is `-10.241`
  bits versus uniform-address reparse. This is still repricing only: just
  `4/10` books improve individually and no source-state recipe reoptimization
  is promoted. Repeating the same repricing over cutoffs `10/20/35/50/60`
  generalizes the aggregate signal: `5/5` cutoffs beat uniform-address reparse,
  totaling `-112.968` bits, while still not promoting a source-state-aware
  recipe optimizer. A fixed-segmentation source-choice optimizer then closes a
  simple local improvement path: it changes `0/514` sources and has `+0.000`
  bits against the repriced ledger, so future source-state work must alter
  segmentation, copy lengths, or use a global path-state objective. The global
  fixed-segmentation source-path DP then confirms that path-state matters:
  it changes `10/514` sources and improves the repriced ledger by `-42.359`
  bits with max state count `14`. Segmentation and copy lengths remain fixed,
  so this is still a partial optimizer rather than a complete active parser.
- Recent book-formula promotions are compatible with the row0 boundary but do
  not change it: the latest bound `8154.676268` improves only the downstream
  book-generation formula, with no row0-label holdout predictor, no lookup-cost
  reduction after paid anchors, no explanation of `39`/`93`/`19/91`, and no new
  CipSoft/authorial provenance.
- The final formula dependency refresh then checks whether those promotions
  changed the structural source/length frontier. They did not: target-max
  coverage remains `242/261`, declared-source+decoder-max remains `60/261`,
  unique-source+decoder-max remains `28/261`, previous-end+decoder-max remains
  `1/261`, and retained operation dependency fields remain `609`.
- The final source/length parser feasibility audit then recalculates the parser
  frontier on the `8154.676268` formula. Previous-end state compression keeps
  all tested book-level end-state proxies below `1,000,000`, but the copy
  transition proxy is still `1,966,897,365` total transitions, `23045.1x` the
  old frozen-count DP. The next implementation step is a pruned/cached
  per-book source+length parser, with hardest books led by `53`, `51`, `35`,
  and `58`.
- The first book-local source/length parser probe executes that path on two
  cutoff-60 books: `67` and `60` both roundtrip and beat raw digit coding, with
  `125.866` total parser bits, `8,423,281` transition evaluations, and no
  improvement over the same-policy reprice comparator. Book `66` remains the
  held-back cutoff-60 hard case with `26,096,904` transition proxy.
- The sparse hard-book parser gate resolves that immediate implementation
  blocker: sparse Dijkstra over reachable `(position, previous_item,
  previous_copy_end)` states roundtrips book `66` in `0.033` seconds, visiting
  `20,932` states and evaluating `41,832` transitions, a `623.9x` reduction
  versus the gate-72 transition proxy. This is parser implementation progress,
  not a compression-bound promotion.
- The post-parser row0 compatibility audit then consolidates gates 71-74
  against the row0 provenance front: none predicts row0 labels under holdout,
  beats the row0 lookup baseline after paid anchor/rule costs, explains `39`,
  `93`, or `19/91` beyond the existing surface clue, or adds CipSoft/authorial
  provenance. The result is explicitly `row0 unchanged`.
- The cutoff-60 sparse suffix parser gate then runs the sparse parser across
  books `60..69` in sequence, carrying `previous_copy_end` between books. It
  roundtrips `10/10`, beats raw digit uniform on `10/10`, totals `368.531807`
  parser bits, and ties same-policy reprice across all books with only
  `383,548` transition evaluations. This is a real parser execution step, not
  a new compression bound or corpus-wide generator promotion.
- The multi-cutoff sparse suffix validation then repeats that setup for cutoffs
  `10/20/35/50/60`: all `175/175` suffix book evaluations roundtrip and beat
  raw digit uniform, the parser is better/tie/worse than same-policy reprice in
  `12/163/0` cells, and the aggregate parser-minus-reprice delta is
  `-12.180052` bits. This strengthens predictive parser evidence, but it is
  not a new compression bound because the rows are overlapping validation cuts,
  not one charged corpus recipe.
- The path-stability audit then replays those `175` parser evaluations with
  exact operation signatures. Among the `50` books seen under multiple cutoffs,
  `38` keep the same exact path and `12` vary. This supports a reusable parser
  mechanism while identifying the remaining prefix-sensitive books, led by
  book `65` with `4` distinct signatures.
- The unstable-path decomposition audit then classifies those `12` books:
  `9/12` are same-shape boundary shifts, `3/12` are segmentation-shape changes,
  and `0/12` are pure source-address swaps. The next structural parser task is
  therefore boundary stabilization, especially book `65`, not another
  source-address micro-sweep.
- The boundary-policy stability gate then tests fixed simple policies over the
  `12` unstable books and `37` cutoff observations. Even the audit-only oracle
  that chooses the lowest average repriced observed variant reaches only
  `18/37` exact matches with `7.849662` regret bits, while the best structural
  policy reaches `16/37` with `8.984788` regret bits. Simple invariant boundary
  rules are therefore rejected rather than promoted.
- The boundary-instability cost decomposition gate then compares each observed
  losing variant against the per-cutoff parser winner. Across `47`
  variant-vs-winner comparisons, the dominant positive component is
  `copy_length` in `30`, `copy_source_exception` in `12`, `literal_payload` in
  `4`, and `copy_source_flag` in `1`. The remaining blocker is therefore
  learned copy-length/source-exception selection, with payload concentrated in
  a few segmentation-shape cases.
- The component-neutralized path-stability gate then tests that diagnosis by
  replacing learned copy-length and source-exception priors with uniform
  decodable costs. Exact multi-cutoff path stability improves from `38/50` to
  `48/50`, with `175/175` roundtrip/raw-positive evaluations, but pays
  `+67.605622` parser bits and still leaves books `26` and `34` unstable. This
  is a structural simplification candidate, not a compression-bound promotion.
- The residual tradeoff audit then separates that `48/50` result: the best
  neutralized mode resolves `11` of the `12` active unstable books, keeps book
  `34` unstable, and introduces book `26` as a new instability. Full-source
  uniformization changes the residual pair to books `35` and `45` but costs
  another `+367.448154` bits over the best mode, so source-flag uniformization
  is not promoted.
- The residual literal-payload neutralization gate then tests the remaining
  segmentation pressure. Adding uniform literal-payload cost resolves books
  `26` and `34` and improves exact path stability to `49/50`, but introduces
  book `49` as the sole residual and pays `+170.606311` parser bits over the
  previous neutralized mode. This is a narrower simplification candidate, still
  not a closed generator.
- The book `49` residual split cause audit then localizes that final residual:
  cutoffs `10/20` choose a `literal-copy-literal` prefix split
  (`11+7+7`), while cutoff `35` chooses the coalesced `25`-digit literal.
  Removing either local `literal_length` or local `item_type` charge makes the
  split-prefix variant win in all three cutoffs, but this remains audit-only
  and does not emit a corpus-wide formula.
- The global item/literal-length control gate then tests those local controls
  corpus-wide. Removing `item_type` charge closes exact path stability at
  `50/50`; removing both `item_type` and `literal_length` also reaches `50/50`
  and gives the best parser-bit delta (`-770.657134` versus the
  payload-uniform baseline), with `175/175` roundtrip/raw-positive evaluations.
  This is a parser-stability simplification, not a compression-bound change or
  row0-origin result.
- The stable path projection boundary audit then checks the promotion boundary:
  the best stable mode covers `11263/11263` digits with `208` canonical copy
  items, `54` literal runs, and `265` parsed literal digits after the 10
  seed books, and it reduces materialized operation dependency fields by `139`
  versus the active formula. It still uses the target book text to find copy
  candidates, literal payload, and literal endpoints, so it is an encoder-side
  projection only, not a decoder-side generator.
- The decoder-side rule coverage audit then tests whether simple rules can turn
  that projection into a generator. The best source rule is
  `source_is_previous_copy_end` at `6/208`; the best length rule is
  `length_is_decoder_max` at `58/208`; and the best decoder-side joint rule is
  only `2/208`. The decoder-max length signal beats shuffled-length controls
  (`p=0.0000`) but is far from complete, and `265` literal payload digits remain
  materialized.
- The source tie-break artifact audit then checks whether the `208/208`
  earliest-target-match source result is merely parser ordering. Re-running the
  stable projection under `earliest_source`, `latest_source`, and
  `prefer_previous_end_then_earliest` tie policies keeps the same primary cost
  (`11459.765681`) and `50/50` stability, but source sums do not change
  (`source_sum_span=0`). The tie-break artifact hypothesis is therefore not
  supported, but the rule still remains target-dependent and is not promoted.
- The source candidate collapse audit then corrects that interpretation:
  `precompute_matches` stores one source per length and keeps the lower
  `source_pos`, so the heap never saw later same-length sources. The `208/208`
  earliest-target-match result is induced by candidate generation; `130/208`
  projected copy events have hidden alternate sources, with up to `13` hidden
  alternatives for one event. Gate 89 is superseded for source-canonicality
  evidence.
- The full source exposure audit then reruns the stable projection on cutoff
  `60` with all same-length source candidates exposed. The tested slice remains
  stable and roundtrips under all three tie policies (`10/10` books). The
  `latest_source` policy chooses `10` non-earliest sources with only
  `+0.017676` primary bits versus the collapsed frontier, while earliest and
  previous-end-preferred policies match collapsed cost. This supports parser
  robustness locally but keeps source choice target-dependent.
- The full-source latest multi-cutoff probe then extends the disruptive
  `latest_source` policy to cutoffs `50/60`. It roundtrips and beats raw on
  `30/30` evaluations, keeps the `10` books observed at both cutoffs stable
  (`10/10`), and selects `35` non-earliest sources while exposing `1246561`
  hidden candidates. This strengthens local parser robustness under exposed
  sources, but remains a probe rather than a full multi-cutoff formula.
- Row0 result: `row0_origin_remains_exogenous`.
- Requirement follow-up: all six requested row0-origin families have explicit
  algorithm, cost or cost note, coverage, contradiction, and control entries;
  promoted origin formulas remain `0`.
- No plaintext, translation, semantic mapping, or case-reopening claim is made.
