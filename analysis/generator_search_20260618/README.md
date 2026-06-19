# 2026-06-18 generator-origin search

This folder shifts the project axis from "compress/reconstruct the 70 books" to
"search for a compact mechanical generator a CipSoft author could plausibly
have used to manufacture 469."

The central runner is `generator_search_suite.py`. The named front scripts are
thin wrappers that regenerate the same frozen-contract output set, so every
front uses the same holdouts, scoring schema, and controls.

## Rebuild

```bash
/opt/anaconda3/bin/python analysis/generator_search_20260618/generator_search_suite.py
```

## Scope

- Mechanical generator hypotheses only.
- No new translation, glossary, or number<->plaintext promotion.
- Chayenne and Your True Colour are external holdouts.
- Avar Tar is a negative control.

## Main outputs

| File | Role |
|---|---|
| `generator_search_contract.md` | Frozen search contract and scoring formula. |
| `generator_scoring_schema.json` | Machine-readable scoring schema. |
| `generator_holdout_manifest.json` | Frozen train/holdout/control manifest. |
| `cipsoft_clue_ledger.md` | Lore/clue ledger converted into tests. |
| `generator_hypothesis_registry.json` | Testable hypothesis registry. |
| `generator_targets.json` / `target_feature_matrix.md` | Target list and front mapping. |
| `grid_formula_search_report.md` / `grid_formula_leaderboard.json` | 10x10 matrix formula search. |
| `deep_formula_search_report.md` / `deep_formula_leaderboard.json` | Deeper arithmetic, modular, traversal, period, and lore-string search beneath the pair table. |
| `pair_table_constructive_report.md` / `pair_table_constructive_leaderboard.json` | Constructive pair-table search: frequency allocation, source-cycle fill, corpus-slice, and seeded placement. |
| `frequency_weighted_stochastic_inventory_report.md` / `frequency_weighted_stochastic_inventory_results.json` | Stochastic pair-inventory generator: one slot per symbol plus frequency-weighted extras. |
| `deterministic_apportionment_inventory_report.md` / `deterministic_apportionment_inventory_results.json` | Deterministic rounding/apportionment search over the frequency-weighted extra homophone slots. |
| `inventory_residual_explainer_report.md` / `inventory_residual_explainer_results.json` | Small-feature correction search for the residual left by deterministic apportionment. |
| `inventory_shuffle_seed_report.md` / `inventory_shuffle_seed_results.json` | Seed/permutation search for exact placement of the observed homophone multiset over 55 pair cells. |
| `pair_assignment_constraint_report.md` / `pair_assignment_constraint_results.json` | Count-respecting deterministic pair-cell assignment search. |
| `endpoint_affinity_assignment_report.md` / `endpoint_affinity_assignment_results.json` | Tests symbol-specific digit endpoint affinities plus small pair features and exact-inventory assignment diagnostics. |
| `bilinear_low_rank_pair_factor_report.md` / `bilinear_low_rank_pair_factor_results.json` | Formal continuous low-rank/SVD pair-label surface probe with inventory-preserving controls. |
| `quotient_low_rank_pair_factor_report.md` / `quotient_low_rank_pair_factor_results.json` | Low-rank/SVD surface probe rerun on the 46 `6<->9` quotient orbits with mixed-orbit lossless accounting. |
| `matrix_generator_exhaustive_report.md` / `matrix_generator_exhaustive_results.json` / `matrix_generator_exhaustive_candidates.tsv` | Permissive no-hard-gate matrix-generator ledger over pair orders, symbol orders, lore seeds, anomaly overlays, and weak compositions. |
| `pair_rule_cover_report.md` / `pair_rule_cover_results.json` | Human-readable digit-pair predicate decision-list search with inventory-preserving label controls. |
| `symbol_predicate_dnf_report.md` / `symbol_predicate_dnf_results.json` | Per-symbol short predicate/DNF search over digit, line, modular, geometry, and lore-shaped features. |
| `symbol_base_accent_layer_report.md` / `symbol_base_accent_layer_results.json` | Tests whether the 14 internal symbols factor into a smaller base alphabet plus accent/refinement layer. |
| `directed_pair_surface_report.md` / `directed_pair_surface_results.json` | Ordered 00..99 surface audit: upper/lower mirror rendering, missing `39`, and directed `19`/`91` conflict. |
| `directed_surface_sequence_generator_report.md` / `directed_surface_sequence_generator_results.json` | Sequential/automaton search over the 99 present ordered 00..99 codes, separated from upper-only and mirror-render redundancy. |
| `structural_exception_layer_report.md` / `structural_exception_layer_results.json` | Tests whether `39`/`93`, `19`/`91`, `33`/`66`, diagonal-E, and zero-geometry anomalies form a compact render/exception layer. |
| `adaptive_quota_fill_report.md` / `adaptive_quota_fill_results.json` | Online quota-fill generator over the 55 pair cells using simple local rules and inventory controls. |
| `row_column_balance_objective_report.md` / `row_column_balance_objective_results.json` | Tests whether the observed pair-cell placement optimizes row/column/digit balance objectives under inventory-preserving swaps. |
| `composite_objective_inverse_report.md` / `composite_objective_inverse_results.json` | Tests whether a sparse composite of balance, context, digit-shape, zero/repeat, and 6<->9 metrics makes the observed table a local optimum. |
| `marginal_constraint_solver_report.md` / `marginal_constraint_solver_results.json` | Tests whether compact inventory, orbit, row/column, diagonal, and anchor constraints uniquely recover the pair table. |
| `finite_group_pair_formula_report.md` / `finite_group_pair_formula_results.json` | Hidden finite-group digit formula search; records the 55/55 lookup-disguise failure mode. |
| `algebraic_digit_composition_report.md` / `algebraic_digit_composition_results.json` | Simple digit-embedding and algebraic bucket-composition search. |
| `direct_symbol_formula_report.md` / `direct_symbol_formula_results.json` | Direct formula search from cell coordinates to symbol-order index, without key-to-symbol lookup. |
| `digit_symbol_automorphism_report.md` / `digit_symbol_automorphism_results.json` | Tests digit-identity and symbol automorphisms over the 55-cell pair table; records weak `6<->9` symmetry. |
| `digit_orbit_quotient_report.md` / `digit_orbit_quotient_results.json` | Quotient/MDL follow-up for digit-transformation orbits, including the weak lossless `6<->9` compression clue. |
| `digit_orbit_split_label_pair_report.md` / `digit_orbit_split_label_pair_results.json` | Tests whether the nine non-singleton `6<->9` orbit label-pairs have a compact direct generator or only split-metadata bookkeeping. |
| `digit_orbit_directed_provenance_report.md` / `digit_orbit_directed_provenance_results.json` | Label-blind/anomaly-metadata provenance test for which non-singleton `6<->9` orbits are mixed and which side carries the canonical label. |
| `digit_orbit_robust_control_report.md` / `digit_orbit_robust_control_results.json` | Formal robust controls for the `6<->9` clue: global, row-preserving, column-preserving, fixed-swap, and best-of-45 swap controls. |
| `nine_identity_render_split_report.md` / `nine_identity_render_split_results.json` | Tests the stricter 45-cell `0,1,2,3,4,5,Q,7,8` base worksheet plus `Q -> 6/9` renderer. |
| `quotient_inventory_pressure_report.md` / `quotient_inventory_pressure_results.json` | Inventory/apportionment pressure test on the `6<->9` quotient, including explicit mixed-orbit accounting. |
| `quotient_pair_formula_report.md` / `quotient_pair_formula_results.json` | Direct quotient-coordinate formula search over the 46 `6<->9` orbit labels. |
| `quotient_line_order_report.md` / `quotient_line_order_results.json` | Line/template, fill-period, seed-cycle, and symmetry scans over the 46 `6<->9` quotient orbit labels. |
| `quotient_constructive_fill_report.md` / `quotient_constructive_fill_results.json` | Constructive quotient fill search combining frequency-weighted inventory, quotient cell orders, and symbol cycles. |
| `quotient_edit_log_mdl_report.md` / `quotient_edit_log_mdl_results.json` | Human-workflow worksheet plus charged edit-log model over quotient constructive candidates. |
| `digit_orbit_exception_rule_report.md` / `digit_orbit_exception_rule_results.json` | Secondary rule search for the four mixed `6<->9` quotient orbits. |
| `digit_orbit_exception_context_report.md` / `digit_orbit_exception_context_results.json` | Context/usage/tape feature search for the four mixed `6<->9` quotient orbits. |
| `digit_visual_symmetry_report.md` / `digit_visual_symmetry_results.json` | Seven-segment, numpad, clock, and 6/9-specific visual symmetry search. |
| `sevenseg_orbit_exception_selector_report.md` / `sevenseg_orbit_exception_selector_results.json` | Narrow follow-up for the two mixed exact seven-segment rotation orbitals. |
| `digit_signature_formula_report.md` / `digit_signature_formula_results.json` | Digit-signature formula search from marginals, diagonals, frequent-symbol incidence, and tape features. |
| `pair_hash_formula_report.md` / `pair_hash_formula_results.json` | Cell-local hash/PRNG formula search over lore seeds and fixed symbol orders. |
| `block_biclique_cover_report.md` / `block_biclique_cover_results.json` | Set-block and biclique decomposition search over the colored digit graph. |
| `digit_permutation_formula_report.md` / `digit_permutation_formula_results.json` | Arithmetic formula search after permuting digit identities. |
| `digit_order_distance_report.md` / `digit_order_distance_results.json` | Hidden digit-order line/cycle distance and midpoint search. |
| `decision_tree_pair_formula_report.md` / `decision_tree_pair_formula_results.json` | Shallow piecewise grid-region formula search over pair-cell features. |
| `alternative_digit_geometry_report.md` / `alternative_digit_geometry_results.json` | Keypad/numpad/clock/seven-segment digit geometry search for pair-cell placement. |
| `pair_graph_incidence_report.md` / `pair_graph_incidence_results.json` | Graph-incidence/digit-affinity search over symbol degree vectors in the 55-cell pair table. |
| `pair_graph_motif_report.md` / `pair_graph_motif_results.json` | Higher-order colored graph motif search: triangles, wedges, stars, paths, orbits, and same-color spectra. |
| `triangular_line_pattern_report.md` / `triangular_line_pattern_results.json` | Row/column/diagonal line-pattern search over the triangular pair table. |
| `line_template_alignment_report.md` / `line_template_alignment_results.json` | Tests whether line families are substrings/reversals/symbol-shifted variants of one short template line. |
| `row_transition_edit_mdl_report.md` / `row_transition_edit_mdl_results.json` | Tests a human workflow where each row/column/diagonal is edited from the previous line, with charged transforms and controls. |
| `local_2d_pair_rule_report.md` / `local_2d_pair_rule_results.json` | Local 2D/CA-style triangular-grid rule search over already-filled neighbours and lore-seed orders. |
| `pair_sequence_automaton_report.md` / `pair_sequence_automaton_results.json` | Sequential/Markov/automaton search over pair-table traversals. |
| `homophone_intrasymbol_order_report.md` / `homophone_intrasymbol_order_results.json` | Intra-symbol pair choice/order search using first use, frequency, and cell features. |
| `pair_context_cluster_report.md` / `pair_context_cluster_results.json` | Tests whether pair cells assigned to the same symbol share raw code-neighbourhood contexts beyond inventory-preserving controls. |
| `pair_context_partition_report.md` / `pair_context_partition_results.json` | Tests whether pair-window context distances can reconstruct the homophone partition without seeing symbol labels. |
| `pair_symbol_stream_compression_report.md` / `pair_symbol_stream_compression_results.json` | Tests whether the observed pair table makes the induced symbol stream more compressible or repeat-rich than shuffled tables. |
| `pair_symbol_stream_optimization_report.md` / `pair_symbol_stream_optimization_results.json` | Tests whether the observed table is a local optimum for the repeat-rich symbol-stream objective. |
| `latent_digit_factor_report.md` / `latent_digit_factor_results.json` | Hidden digit-class factorization search for pair-cell placement. |
| `lore_text_subsequence_report.md` / `lore_text_subsequence_results.json` | Longer lore quote/formula/title window and subsequence search for pair-cell placement. |
| `lore_anomaly_operator_report.md` / `lore_anomaly_operator_results.json` | Tests lore numbers as selectors for small structural anomaly sets rather than as full-table seeds. |
| `usage_driven_pair_placement_report.md` / `usage_driven_pair_placement_results.json` | Pair-cell placement search using code frequency, first/last use, and orientation-bias orders. |
| `digit_shape_pressure_report.md` / `digit_shape_pressure_results.json` | Pair/code placement search for digit-balance, zero-rate, repeat-rate, and raw-distribution pressure. |
| `symbol_digit_origin_report.md` / `symbol_digit_origin_results.json` | Tests whether assembly happened before or after homophone numeric rendering. |
| `orientation_render_rule_report.md` / `orientation_render_rule_results.json` | Ordered-code orientation render-rule search (`ab` vs `ba`) with book and pair holdouts. |
| `honeminas_vector_report.md` / `magic_web_null_controls.json` | Magic Web/Honeminas vector tests. |
| `one_equals_tibia_report.md` | `1 = Tibia` structural tests. |
| `homophone_selector_leaderboard.md` / `homophone_holdout_report.json` | Homophone selector holdout. |
| `zero_render_rule_report.md` | Zero omission/rendering holdout. |
| `zero_omission_rule_explainer_report.md` / `zero_omission_rule_explainer_results.json` | Converts the ML zero-omission signal into explicit group rules, weights, MDL estimate, and controls. |
| `zero_exception_decision_list_report.md` / `zero_exception_decision_list_results.json` | Tests whether zero omission can be reduced to a sparse ordered exception list over the `code_only` renderer. |
| `zero_compact_rule_report.md` / `zero_compact_rule_results.json` | Fixed human-readable previous-code, boundary, and geometry zero-rendering rules derived from the local-context audit. |
| `shared_e_zero_predicate_report.md` / `shared_e_zero_predicate_results.json` | Fixed `i>=j` predicate test linking diagonal E pressure and previous-code zero omission. |
| `e_layer_predicate_report.md` / `e_layer_predicate_results.json` | E-specific predicate audit separating all-E inventory from the off-diagonal residual after diagonal pressure. |
| `priority_masked_e_layer_report.md` / `priority_masked_e_layer_results.json` | Priority-mask follow-up: F/V/N/A blockers before the high-block E fill. |
| `high_block_blocker_origin_report.md` / `high_block_blocker_origin_results.json` | Tests whether high-block E-priority blockers come from a mini-block drawing/stroke rule. |
| `render_origin_e_priority_probe_report.md` / `render_origin_e_priority_probe_results.json` | Tests whether zero/orientation/render features explain E-priority claims or blockers beyond geometry. |
| `anchored_remaining_fill_report.md` / `anchored_remaining_fill_results.json` | Tests whether fixed E-priority anchors unlock a frequency/6<->9 ordered fill for the remaining cells. |
| `priority_anchored_quotient_residual_fill_report.md` / `priority_anchored_quotient_residual_fill_results.json` | Quotient-correct ablation: preserve E-priority anchors and shuffle/fill only residual quotient labels. |
| `lore_zero_phase_mask_report.md` / `lore_zero_phase_mask_results.json` | Tests whether lore numbers such as 3478/Honeminas/Magic Web act as cyclic leading-zero omission masks. |
| `zero_homophone_transition_origin_probe_report.md` / `zero_homophone_transition_origin_probe_results.json` | Joint probe testing whether zero omission, orientation, and prev/next code context reconstruct the pair-table homophone partition. |
| `module_template_report.md` / `module_mdl_comparison.json` | Module grammar/MDL comparison. |
| `module_overlap_grammar_report.md` / `module_overlap_grammar_results.json` | Overlap-tape/slice grammar search for the 62 literal modules, with digit-shuffle controls. |
| `module_tape_origin_report.md` / `module_tape_origin_results.json` | Tests whether overlap-tape components occur in books and absorb residual literal gaps in recipes. |
| `endpoint_literal_bridge_mdl_report.md` / `endpoint_literal_bridge_mdl_results.json` | Tests whether remaining literal recipe spans are reusable bridge strings keyed by adjacent tape/module endpoints. |
| `module_tape_order_report.md` / `module_tape_order_results.json` | Tests whether the internal order of overlap-tape slices follows simple module/order features. |
| `t00_internal_fsa_compression_report.md` / `t00_internal_fsa_compression_results.json` | Finite-state n-gram compression probe for the tokenized `T00` sequence and slice-order controls. |
| `tape_based_formula_report.md` / `tape_based_formula_469.json` | Lossless 70/70 generator using tape components, module slices, and merged same-component book spans. |
| `tape_tokenization_report.md` / `tape_tokenization_results.json` | Projects known code tokens back onto tape coordinates; checks code/symbol coherence and boundary exceptions. |
| `tape_first_use_pair_order_report.md` / `tape_first_use_pair_order_results.json` | Tests whether pair cells first appear on reusable tapes in a simple matrix/lore-digit traversal order. |
| `tape_literal_exception_report.md` / `tape_literal_exception_results.json` | Tests whether pairs/codes found only outside reusable tapes form a structural exception layer. |
| `tape_feature_pair_label_report.md` / `tape_feature_pair_label_results.json` | Tests whether tape/literal usage features predict pair-table symbol labels beyond inventory-preserving controls. |
| `residual_tape_feature_after_e_report.md` / `residual_tape_feature_after_e_results.json` | Residual tape/usage feature test after removing the fixed E-priority layer. |
| `residual_marginal_after_e_report.md` / `residual_marginal_after_e_results.json` | Residual row/column/diagonal/digit marginal test after removing the fixed E-priority layer. |
| `pair_marginal_signature_report.md` / `pair_marginal_signature_results.json` | Tests whether rows, columns, diagonals, borders, or digit marginals carry a pair-table signature beyond inventory-preserving controls. |
| `prng_seed_leaderboard.md` | Seed/PRNG search. |
| `external_holdout_chayenne_ytc_report.md` | External holdout report. |
| `avar_tar_control_report.md` / `control_leakage_matrix.json` | Negative-control suite. |
| `generator_mdl_leaderboard.md` | Consolidated leaderboard. |
| `generator_model_final_report.md` | Current generator-origin verdict. |
| `saturation_audit_20260619.md` | Parallel subagent saturation audit for remaining matrix and sequence fronts. |

## Related outputs

| File | Role |
|---|---|
| `../ml_formula_probe_20260618/ml_formula_probe_report.md` / `../ml_formula_probe_20260618/ml_formula_probe_results.json` | Controlled ML probes for pair-cell symbols, homophone choice, and zero omission. |
