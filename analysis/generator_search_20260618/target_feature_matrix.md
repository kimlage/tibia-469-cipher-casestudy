# Target Feature Matrix

| Target | Fronts | Promotion gate |
|---|---|---|
| `A` table_00_99_to_symbols | `grid_formula_search`, `matrix_generator_exhaustive_search`, `seed_generator_search`, `pair_marginal_signature_search`, `residual_marginal_after_e_search` | Explain the 99-entry code->symbol table; must pass controls |
| `B` unordered_pair_purity | `grid_formula_search`, `matrix_generator_exhaustive_search`, `magic_web_formula_search` | Explain 54/55 pure unordered pair classes; must pass controls |
| `C` conflict_19_91 | `grid_formula_search`, `matrix_generator_exhaustive_search`, `one_equals_tibia_tests` | Explain sole pair conflict {19,91}; must pass controls |
| `D` missing_39 | `grid_formula_search`, `matrix_generator_exhaustive_search`, `seed_generator_search` | Explain absent cell 39; must pass controls |
| `E` symbol_distribution | `grid_formula_search`, `prng_seed_search` | Explain symbol frequencies; must pass controls |
| `F` homophone_class_sizes | `one_equals_tibia_tests`, `homophone_generator_search`, `pair_context_cluster_search`, `pair_context_partition_search` | Explain homophones per symbol; must pass controls |
| `G` book_code_sequence | `homophone_generator_search`, `pair_context_cluster_search`, `pair_context_partition_search`, `pair_symbol_stream_compression_search`, `module_grammar_induction` | Explain code sequence in books; must pass controls |
| `H` long_modules | `module_grammar_induction`, `module_overlap_grammar_search`, `module_tape_origin_search`, `module_tape_order_search`, `tape_based_formula_compile`, `tape_tokenization_analysis`, `tape_first_use_pair_order_search`, `tape_literal_exception_analysis`, `tape_feature_pair_label_search`, `magic_web_formula_search` | Explain long copied modules; must pass controls |
| `I` residuals | `residual_coverage_mdl`, `module_grammar_induction` | Explain 2,083 literal residual digits; must pass controls |
| `J` zero_omissions | `zero_omission_generator`, `zero_exception_decision_list`, `zero_omission_supporting_render_layer` | Explain omitted leading zeros; must pass controls |
| `K` chayenne_ytc | `external_holdout_chayenne_ytc` | Explain external holdouts without training; must pass controls |
| `L` reject_avar_tar | `negative_control_suite` | Reject Avar Tar/control leakage; must pass controls |
