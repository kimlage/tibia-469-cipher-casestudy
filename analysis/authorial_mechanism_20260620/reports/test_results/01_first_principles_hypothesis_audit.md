# First-Principles Hypothesis Audit

Verdict: `mechanism_prior_integrated`. Translation delta: `NONE`.

This audit converts the report's first-principles claims into bounded
authorial/mechanical hypotheses. It does not infer private intent and
does not promote plaintext.

## Checks

| Check | Verified |
|---|---:|
| `all_required_hypotheses_present` | `True` |
| `baseline_exists` | `True` |
| `baseline_roundtrips_70` | `True` |
| `baseline_translation_delta_none` | `True` |
| `registry_translation_delta_none` | `True` |
| `no_plaintext_from_authorial_model` | `True` |
| `no_fan_gloss_as_ground_truth` | `True` |
| `no_llm_prose_as_evidence` | `True` |

## Hypotheses

| ID | Status | Guard present |
|---|---|---:|
| `H-AUTH1` | `best_design_model_no_intent_claim` | `True` |
| `H-AUTH2` | `plausible_mechanism_frame` | `True` |
| `H-AUTH3` | `plausible_design_interpretation` | `True` |
| `H-GEN1` | `tested_in_this_front` | `True` |
| `H-GEN2` | `tested_in_this_front` | `True` |
| `H-GEN3` | `candidate_compiled_in_this_front` | `True` |
| `H-GEN3B` | `controlled_mechanical_improvement_no_semantics` | `True` |
| `H-GEN3C` | `controlled_inventory_reuse_order_not_promoted` | `True` |
| `H-GEN3D` | `hierarchical_reference_formula_roundtrips_no_semantics` | `True` |
| `H-GEN3E` | `controlled_sequential_lz_book_formula` | `True` |
| `H-GEN3F` | `order_search_not_promoted_after_permutation_cost` | `True` |
| `H-GEN3G` | `controlled_sequential_lz_run_literal_formula` | `True` |
| `H-GEN3H` | `controlled_sequential_lz_dp_parse_formula` | `True` |
| `H-GEN3I` | `copy_source_address_absolute_retained` | `True` |
| `H-GEN3J` | `copy_graph_literal_seed_atlas_compiled_no_formula_promotion` | `True` |
| `H-GEN3K` | `structured_physical_order_not_better_than_numeric` | `True` |
| `H-GEN3L` | `literal_seed_address_optimistic_only_not_promoted` | `True` |
| `H-GEN3M` | `literal_seed_grouped_mode_optimistic_only_not_promoted` | `True` |
| `H-GEN3N` | `copy_hub_macro_model_not_promoted` | `True` |
| `H-GEN3O` | `restricted_hybrid_vocabulary_not_promoted` | `True` |
| `H-GEN3P` | `dp_min_len_sweep_retains_min_len_6` | `True` |
| `H-GEN3Q` | `controlled_copy_length_code_improvement` | `True` |
| `H-GEN3R` | `copy_length_grid_retains_rice_k4_min_len_5` | `True` |
| `H-GEN3S` | `rice_copy_address_optimistic_only_not_promoted` | `True` |
| `H-GEN3T` | `controlled_literal_length_code_improvement` | `True` |
| `H-GEN3U` | `joint_length_grid_retains_rice_k4_literal_rice_k3_min_len_5` | `True` |
| `H-GEN3V` | `controlled_literal_payload_adaptive_improvement` | `True` |
| `H-GEN3W` | `current_formula_address_optimistic_only_not_promoted` | `True` |
| `H-GEN3X` | `controlled_literal_to_copy_single_repair_improvement` | `True` |
| `H-GEN3Y` | `post_repair_payload_alpha_retains_14` | `True` |
| `H-GEN3Z` | `post_repair_address_optimistic_only_not_promoted` | `True` |
| `H-GEN3AA` | `literal_to_copy_pair_repair_not_promoted` | `True` |
| `H-GEN3AB` | `controlled_book_length_ledger_improvement` | `True` |
| `H-GEN3AC` | `multi_anchor_book_length_ledger_not_promoted` | `True` |
| `H-GEN3AD` | `controlled_digit_only_copy_address_improvement` | `True` |
| `H-GEN3AE` | `digit_address_optimistic_only_not_promoted` | `True` |
| `H-GEN3AF` | `controlled_digit_address_literal_repair_improvement` | `True` |
| `H-GEN3AG` | `post_digit_repair_payload_alpha_retains_14` | `True` |
| `H-GEN3AH` | `post_digit_repair_address_optimistic_only_not_promoted` | `True` |
| `H-GEN3AI` | `controlled_item_type_ledger_improvement` | `True` |
| `H-GEN3AJ` | `controlled_markov_item_type_ledger_improvement` | `True` |
| `H-GEN3AK` | `controlled_book_start_item_type_ledger_improvement` | `True` |
| `H-GEN3AL` | `controlled_literal_forces_copy_type_ledger_improvement` | `True` |
| `H-GEN3AM` | `controlled_remaining_short_forces_literal_type_ledger_improvement` | `True` |
| `H-GEN3AN` | `controlled_remaining_short_literal_length_improvement` | `True` |
| `H-GEN3AO` | `controlled_forced_length_literal_repair_improvement` | `True` |
| `H-GEN3AP` | `post_forced_repair_payload_alpha_retains_14` | `True` |
| `H-GEN3AQ` | `post_forced_repair_address_optimistic_only_not_promoted` | `True` |
| `H-GEN3AR` | `post_forced_repair_pair_not_promoted` | `True` |
| `H-GEN3AS` | `post_forced_repair_triple_not_promoted` | `True` |
| `H-GEN3AT` | `post_forced_repair_quad_not_promoted` | `True` |
| `H-GEN3AU` | `post_forced_repair_quint_not_promoted` | `True` |
| `H-GEN3AV` | `post_forced_repair_sext_not_promoted` | `True` |
| `H-GEN3AW` | `post_forced_repair_sept_not_promoted` | `True` |
| `H-GEN3AX` | `post_forced_repair_oct_not_promoted` | `True` |
| `H-GEN3AY` | `post_forced_repair_nonet_not_promoted` | `True` |
| `H-GEN3AZ` | `post_forced_repair_decet_not_promoted` | `True` |
| `H-GEN3BA` | `post_forced_repair_eleven_not_promoted` | `True` |
| `H-GEN3BB` | `post_forced_repair_twelve_not_promoted` | `True` |
| `H-GEN3BC` | `post_forced_repair_high_order_not_promoted` | `True` |
| `H-GEN3BD` | `controlled_literal_payload_context_improvement` | `True` |
| `H-GEN3BE` | `controlled_literal_payload_context_order_improvement` | `True` |
| `H-GEN3BF` | `controlled_item_type_context_order_improvement` | `True` |
| `H-GEN3BG` | `contextual_local_repair_not_promoted` | `True` |
| `H-GEN3BH` | `controlled_contextual_copy_to_literal_improvement` | `True` |
| `H-GEN3BI` | `post_copy_literal_local_frontier_closed` | `True` |
| `H-GEN3BJ` | `contextual_address_optimistic_only_not_promoted` | `True` |
| `H-GEN3BK` | `post_contextual_parameter_resweep_retains_current` | `True` |
| `H-GEN3BL` | `controlled_bounded_copy_length_improvement` | `True` |
| `H-GEN3BM` | `controlled_min_len_bounded_copy_address_improvement` | `True` |
| `H-GEN3BN` | `controlled_minaddr_local_repair_improvement` | `True` |
| `H-GEN3BO` | `controlled_post_minaddr_repair_local_improvement` | `True` |
| `H-GEN3BP` | `post_minaddr_repair2_local_frontier_closed` | `True` |
| `H-GEN3BQ` | `post_repair2_parameter_resweep_retains_current` | `True` |
| `H-GEN3BR` | `post_repair2_pair_frontier_closed` | `True` |
| `H-GEN3BS` | `post_repair2_address_optimistic_only_not_promoted` | `True` |
| `H-GEN3BT` | `post_repair2_copy_order_optimistic_only_not_promoted` | `True` |
| `H-GEN3BU` | `controlled_post_repair2_adaptive_copy_length_improvement` | `True` |
| `H-GEN3BV` | `post_adaptive_copy_length_local_frontier_closed` | `True` |
| `H-GEN3BW` | `post_adaptive_parameter_resweep_retains_current` | `True` |
| `H-GEN3BX` | `post_adaptive_pair_frontier_closed` | `True` |
| `H-GEN3BY` | `post_adaptive_address_optimistic_only_not_promoted` | `True` |
| `H-GEN3BZ` | `post_adaptive_copy_order_optimistic_only_not_promoted` | `True` |
| `H-GEN3CA` | `controlled_post_adaptive_copy_length_midpoint_context_improvement` | `True` |
| `H-GEN3CB` | `post_midpoint_local_frontier_closed` | `True` |
| `H-GEN3CC` | `controlled_post_midpoint_copy_length_alpha_improvement` | `True` |
| `H-GEN3CD` | `post_midpoint_alpha1_local_frontier_closed` | `True` |
| `H-GEN3CE` | `post_midpoint_alpha1_pair_frontier_closed` | `True` |
| `H-GEN3CF` | `post_midpoint_alpha1_address_optimistic_only_not_promoted` | `True` |
| `H-GEN3CG` | `post_midpoint_alpha1_copy_order_optimistic_only_not_promoted` | `True` |
| `H-GEN3CH` | `post_midpoint_alpha1_copy_length_context_retains_midpoint` | `True` |
| `H-GEN3CI` | `post_midpoint_alpha_by_context_not_promoted` | `True` |
| `H-GEN3CJ` | `post_midpoint_literal_payload_context_not_promoted` | `True` |
| `H-GEN3CK` | `bounded_post_midpoint_alpha1_top60_triple_probe_not_promoted` | `True` |
| `H-GEN3CL` | `controlled_post_midpoint_item_type_context_improvement` | `True` |
| `H-GEN3CM` | `controlled_post_itemctx_parameter_improvement` | `True` |
| `H-GEN3CN` | `post_itemctx_param_local_frontier_closed` | `True` |
| `H-GEN3CO` | `post_itemctx_param_pair_frontier_closed` | `True` |
| `H-GEN3CP` | `post_itemctx_param_address_optimistic_only_not_promoted` | `True` |
| `H-GEN3CQ` | `post_itemctx_param_copy_order_optimistic_only_not_promoted` | `True` |
| `H-GEN3CR` | `post_itemctx_param_copy_length_context_retains_midpoint` | `True` |
| `H-GEN3CS` | `post_itemctx_param_alpha_by_context_not_promoted` | `True` |
| `H-GEN3CT` | `post_itemctx_param_literal_payload_context_not_promoted` | `True` |
| `H-GEN3CU` | `post_itemctx_param_item_type_context_family_not_promoted` | `True` |
| `H-GEN3CV` | `post_itemctx_param_payload_item_type_pair_not_promoted` | `True` |
| `H-GEN3CW` | `post_itemctx_param_copy_length_item_type_pair_not_promoted` | `True` |
| `H-GEN3CX` | `post_itemctx_param_payload_copy_length_item_type_triple_not_promoted` | `True` |
| `H-GEN3CY` | `post_itemctx_param_copy_length_alpha_item_type_pair_not_promoted` | `True` |
| `H-GEN3CZ` | `post_itemctx_param_copy_length_alpha_payload_pair_not_promoted` | `True` |
| `H-GEN4` | `open_low_expectation` | `True` |
| `H-GEN4A` | `hierarchical_provenance_not_pair_table_formula` | `True` |
| `H-GEN5` | `watchlist_only` | `True` |

## Conclusion

The report is integrated as a mechanism-search prior. Semantic progress
remains zero until official ground truth appears.
