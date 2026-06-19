---
page_id: generator-origin-search
page_type: finding
context: bonelord-469
visibility: public_candidate
status: closed
updated_at: 2026-06-19
moc_parent: README.md
source_refs: [analysis/generator_search_20260618]
---

# 12. Generator-Origin Search

[<- Mechanism & Origin Model](11-mechanism-origin-model.md) . [Wiki home](README.md) . [Mechanical Origin Model v1 ->](13-mechanical-origin-model-v1.md)

---

> Post-final generator addendum. This page changes the operational question
> from "can we compress/reconstruct the books?" to "can we find the compact
> mechanical generator a CipSoft author could plausibly have used?"

## Rule

Nothing on this page is a translation. A candidate only advances if it improves
mechanical prediction, MDL, or controls without creating plaintext.

Exploration is now deliberately permissive: hard cutoffs such as minimum
coverage or maximum exception count are not used to stop a hypothesis early.
They classify confidence after measurement. Weak, expensive, and failed
hypotheses stay in the ledger.

Full artifacts:
[`analysis/generator_search_20260618/`](../../analysis/generator_search_20260618/).

Core files:

- [`generator_search_contract.md`](../../analysis/generator_search_20260618/generator_search_contract.md)
- [`generator_holdout_manifest.json`](../../analysis/generator_search_20260618/generator_holdout_manifest.json)
- [`cipsoft_clue_ledger.md`](../../analysis/generator_search_20260618/cipsoft_clue_ledger.md)
- [`generator_targets.json`](../../analysis/generator_search_20260618/generator_targets.json)
- [`generator_mdl_leaderboard.md`](../../analysis/generator_search_20260618/generator_mdl_leaderboard.md)
- [`generator_model_final_report.md`](../../analysis/generator_search_20260618/generator_model_final_report.md)
- [`saturation_audit_20260619.md`](../../analysis/generator_search_20260618/saturation_audit_20260619.md)
- [`deep_formula_search_report.md`](../../analysis/generator_search_20260618/deep_formula_search_report.md)
- [`pair_table_constructive_report.md`](../../analysis/generator_search_20260618/pair_table_constructive_report.md)
- [`frequency_weighted_stochastic_inventory_report.md`](../../analysis/generator_search_20260618/frequency_weighted_stochastic_inventory_report.md)
- [`deterministic_apportionment_inventory_report.md`](../../analysis/generator_search_20260618/deterministic_apportionment_inventory_report.md)
- [`inventory_residual_explainer_report.md`](../../analysis/generator_search_20260618/inventory_residual_explainer_report.md)
- [`inventory_shuffle_seed_report.md`](../../analysis/generator_search_20260618/inventory_shuffle_seed_report.md)
- [`pair_assignment_constraint_report.md`](../../analysis/generator_search_20260618/pair_assignment_constraint_report.md)
- [`endpoint_affinity_assignment_report.md`](../../analysis/generator_search_20260618/endpoint_affinity_assignment_report.md)
- [`bilinear_low_rank_pair_factor_report.md`](../../analysis/generator_search_20260618/bilinear_low_rank_pair_factor_report.md)
- [`quotient_low_rank_pair_factor_report.md`](../../analysis/generator_search_20260618/quotient_low_rank_pair_factor_report.md)
- [`matrix_generator_exhaustive_report.md`](../../analysis/generator_search_20260618/matrix_generator_exhaustive_report.md)
- [`pair_rule_cover_report.md`](../../analysis/generator_search_20260618/pair_rule_cover_report.md)
- [`symbol_predicate_dnf_report.md`](../../analysis/generator_search_20260618/symbol_predicate_dnf_report.md)
- [`symbol_base_accent_layer_report.md`](../../analysis/generator_search_20260618/symbol_base_accent_layer_report.md)
- [`directed_pair_surface_report.md`](../../analysis/generator_search_20260618/directed_pair_surface_report.md)
- [`directed_surface_sequence_generator_report.md`](../../analysis/generator_search_20260618/directed_surface_sequence_generator_report.md)
- [`sevenseg_orbit_exception_selector_report.md`](../../analysis/generator_search_20260618/sevenseg_orbit_exception_selector_report.md)
- [`adaptive_quota_fill_report.md`](../../analysis/generator_search_20260618/adaptive_quota_fill_report.md)
- [`row_column_balance_objective_report.md`](../../analysis/generator_search_20260618/row_column_balance_objective_report.md)
- [`composite_objective_inverse_report.md`](../../analysis/generator_search_20260618/composite_objective_inverse_report.md)
- [`marginal_constraint_solver_report.md`](../../analysis/generator_search_20260618/marginal_constraint_solver_report.md)
- [`finite_group_pair_formula_report.md`](../../analysis/generator_search_20260618/finite_group_pair_formula_report.md)
- [`algebraic_digit_composition_report.md`](../../analysis/generator_search_20260618/algebraic_digit_composition_report.md)
- [`digit_permutation_formula_report.md`](../../analysis/generator_search_20260618/digit_permutation_formula_report.md)
- [`digit_order_distance_report.md`](../../analysis/generator_search_20260618/digit_order_distance_report.md)
- [`decision_tree_pair_formula_report.md`](../../analysis/generator_search_20260618/decision_tree_pair_formula_report.md)
- [`alternative_digit_geometry_report.md`](../../analysis/generator_search_20260618/alternative_digit_geometry_report.md)
- [`pair_graph_incidence_report.md`](../../analysis/generator_search_20260618/pair_graph_incidence_report.md)
- [`pair_graph_motif_report.md`](../../analysis/generator_search_20260618/pair_graph_motif_report.md)
- [`triangular_line_pattern_report.md`](../../analysis/generator_search_20260618/triangular_line_pattern_report.md)
- [`local_2d_pair_rule_report.md`](../../analysis/generator_search_20260618/local_2d_pair_rule_report.md)
- [`pair_sequence_automaton_report.md`](../../analysis/generator_search_20260618/pair_sequence_automaton_report.md)
- [`homophone_intrasymbol_order_report.md`](../../analysis/generator_search_20260618/homophone_intrasymbol_order_report.md)
- [`pair_context_cluster_report.md`](../../analysis/generator_search_20260618/pair_context_cluster_report.md)
- [`pair_context_partition_report.md`](../../analysis/generator_search_20260618/pair_context_partition_report.md)
- [`pair_symbol_stream_compression_report.md`](../../analysis/generator_search_20260618/pair_symbol_stream_compression_report.md)
- [`pair_symbol_stream_optimization_report.md`](../../analysis/generator_search_20260618/pair_symbol_stream_optimization_report.md)
- [`latent_digit_factor_report.md`](../../analysis/generator_search_20260618/latent_digit_factor_report.md)
- [`lore_text_subsequence_report.md`](../../analysis/generator_search_20260618/lore_text_subsequence_report.md)
- [`lore_anomaly_operator_report.md`](../../analysis/generator_search_20260618/lore_anomaly_operator_report.md)
- [`usage_driven_pair_placement_report.md`](../../analysis/generator_search_20260618/usage_driven_pair_placement_report.md)
- [`digit_shape_pressure_report.md`](../../analysis/generator_search_20260618/digit_shape_pressure_report.md)
- [`symbol_digit_origin_report.md`](../../analysis/generator_search_20260618/symbol_digit_origin_report.md)
- [`orientation_render_rule_report.md`](../../analysis/generator_search_20260618/orientation_render_rule_report.md)
- [`module_overlap_grammar_report.md`](../../analysis/generator_search_20260618/module_overlap_grammar_report.md)
- [`module_tape_origin_report.md`](../../analysis/generator_search_20260618/module_tape_origin_report.md)
- [`endpoint_literal_bridge_mdl_report.md`](../../analysis/generator_search_20260618/endpoint_literal_bridge_mdl_report.md)
- [`module_tape_order_report.md`](../../analysis/generator_search_20260618/module_tape_order_report.md)
- [`t00_internal_fsa_compression_report.md`](../../analysis/generator_search_20260618/t00_internal_fsa_compression_report.md)
- [`tape_based_formula_report.md`](../../analysis/generator_search_20260618/tape_based_formula_report.md)
- [`tape_tokenization_report.md`](../../analysis/generator_search_20260618/tape_tokenization_report.md)
- [`tape_first_use_pair_order_report.md`](../../analysis/generator_search_20260618/tape_first_use_pair_order_report.md)
- [`tape_literal_exception_report.md`](../../analysis/generator_search_20260618/tape_literal_exception_report.md)
- [`tape_feature_pair_label_report.md`](../../analysis/generator_search_20260618/tape_feature_pair_label_report.md)
- [`residual_tape_feature_after_e_report.md`](../../analysis/generator_search_20260618/residual_tape_feature_after_e_report.md)
- [`residual_marginal_after_e_report.md`](../../analysis/generator_search_20260618/residual_marginal_after_e_report.md)
- [`pair_marginal_signature_report.md`](../../analysis/generator_search_20260618/pair_marginal_signature_report.md)
- [`zero_omission_rule_explainer_report.md`](../../analysis/generator_search_20260618/zero_omission_rule_explainer_report.md)
- [`zero_exception_decision_list_report.md`](../../analysis/generator_search_20260618/zero_exception_decision_list_report.md)
- [`zero_compact_rule_report.md`](../../analysis/generator_search_20260618/zero_compact_rule_report.md)
- [`shared_e_zero_predicate_report.md`](../../analysis/generator_search_20260618/shared_e_zero_predicate_report.md)
- [`e_layer_predicate_report.md`](../../analysis/generator_search_20260618/e_layer_predicate_report.md)
- [`priority_masked_e_layer_report.md`](../../analysis/generator_search_20260618/priority_masked_e_layer_report.md)
- [`high_block_blocker_origin_report.md`](../../analysis/generator_search_20260618/high_block_blocker_origin_report.md)
- [`render_origin_e_priority_probe_report.md`](../../analysis/generator_search_20260618/render_origin_e_priority_probe_report.md)
- [`anchored_remaining_fill_report.md`](../../analysis/generator_search_20260618/anchored_remaining_fill_report.md)
- [`priority_anchored_quotient_residual_fill_report.md`](../../analysis/generator_search_20260618/priority_anchored_quotient_residual_fill_report.md)
- [`lore_zero_phase_mask_report.md`](../../analysis/generator_search_20260618/lore_zero_phase_mask_report.md)
- [`structural_exception_layer_report.md`](../../analysis/generator_search_20260618/structural_exception_layer_report.md)
- [`direct_symbol_formula_report.md`](../../analysis/generator_search_20260618/direct_symbol_formula_report.md)
- [`digit_symbol_automorphism_report.md`](../../analysis/generator_search_20260618/digit_symbol_automorphism_report.md)
- [`digit_orbit_quotient_report.md`](../../analysis/generator_search_20260618/digit_orbit_quotient_report.md)
- [`digit_orbit_split_label_pair_report.md`](../../analysis/generator_search_20260618/digit_orbit_split_label_pair_report.md)
- [`digit_orbit_directed_provenance_report.md`](../../analysis/generator_search_20260618/digit_orbit_directed_provenance_report.md)
- [`digit_orbit_robust_control_report.md`](../../analysis/generator_search_20260618/digit_orbit_robust_control_report.md)
- [`nine_identity_render_split_report.md`](../../analysis/generator_search_20260618/nine_identity_render_split_report.md)
- [`quotient_inventory_pressure_report.md`](../../analysis/generator_search_20260618/quotient_inventory_pressure_report.md)
- [`quotient_pair_formula_report.md`](../../analysis/generator_search_20260618/quotient_pair_formula_report.md)
- [`quotient_line_order_report.md`](../../analysis/generator_search_20260618/quotient_line_order_report.md)
- [`quotient_constructive_fill_report.md`](../../analysis/generator_search_20260618/quotient_constructive_fill_report.md)
- [`quotient_edit_log_mdl_report.md`](../../analysis/generator_search_20260618/quotient_edit_log_mdl_report.md)
- [`digit_orbit_exception_rule_report.md`](../../analysis/generator_search_20260618/digit_orbit_exception_rule_report.md)
- [`digit_orbit_exception_context_report.md`](../../analysis/generator_search_20260618/digit_orbit_exception_context_report.md)
- [`digit_visual_symmetry_report.md`](../../analysis/generator_search_20260618/digit_visual_symmetry_report.md)
- [`digit_signature_formula_report.md`](../../analysis/generator_search_20260618/digit_signature_formula_report.md)
- [`pair_hash_formula_report.md`](../../analysis/generator_search_20260618/pair_hash_formula_report.md)
- [`block_biclique_cover_report.md`](../../analysis/generator_search_20260618/block_biclique_cover_report.md)
- [`line_template_alignment_report.md`](../../analysis/generator_search_20260618/line_template_alignment_report.md)
- [`row_transition_edit_mdl_report.md`](../../analysis/generator_search_20260618/row_transition_edit_mdl_report.md)
- [`zero_homophone_transition_origin_probe_report.md`](../../analysis/generator_search_20260618/zero_homophone_transition_origin_probe_report.md)
- [`ml_formula_probe_report.md`](../../analysis/ml_formula_probe_20260618/ml_formula_probe_report.md)

## Current Leaderboard

| Hypothesis | Role | Verdict |
|---|---|---|
| `tape_based_mechanical_formula` | lossless 70/70 formula using tape components/slices | `candidate_tape_based_formula` |
| `core_mechanical_formula` | lossless 70/70 formula | `core` |
| `grid_unordered_pair` | compact table geometry | `candidate_generator` |
| `pair_table_frequency_allocation` | homophone class sizes track internal symbol frequency | `candidate_generator` |
| `frequency_weighted_stochastic_inventory` | one slot per symbol plus frequency-weighted extras | `candidate_generator_stochastic_inventory` |
| `deterministic_apportionment_inventory` | deterministic rounding/apportionment of frequency-weighted extras | `secondary_support_not_exact` |
| `inventory_residual_explainer` | small-feature correction of remaining apportionment residual | `rejected_control` |
| `inventory_shuffle_seed_search` | seed/permutation placement of the observed homophone inventory | `rejected_control` |
| `symbol_digit_origin_order` | repeated chunks preserve exact code sequences after rendering | `candidate_generator` |
| `module_overlap_tape_grammar` | 62 modules collapse into overlap-tape components/slices | `candidate_overlap_tape` |
| `module_tape_origin_search` | overlap components occur in books and absorb residual gaps | `secondary_support_overlap_tape_origin` |
| `endpoint_literal_bridge_mdl_search` | endpoint-conditioned bridge test for 28 internal bridge literals | `rejected_control` |
| `module_tape_order_search` | simple order signals for `T00` | `rejected_control` |
| `t00_internal_fsa_compression_probe` | finite-state compression of tokenized `T00` | `slice_internal_regular_not_t00_order_formula` |
| `tape_tokenization_analysis` | code-token projection onto tape coordinates | `candidate_token_coherent_tapes_with_edge_exceptions` |
| `tape_first_use_pair_order_search` | pair-cell first-use order on reusable tapes | `rejected_control` |
| `tape_literal_exception_analysis` | pair/code cells found only outside reusable tapes | `not_promoted` |
| `tape_feature_pair_label_search` | pair labels from tape/literal usage features | `rejected_control` |
| `residual_tape_feature_after_e_search` | tape/usage/grid features on the 40 non-E-priority residual cells | `residual_tape_feature_not_promoted` |
| `residual_marginal_after_e_search` | row/column/diagonal/digit marginals on the 40 non-E-priority residual cells | `residual_marginal_not_promoted` |
| `pair_marginal_signature_search` | diagonal/row/column/border/digit marginal signatures | `rejected_control` |
| `orientation_render_rule` | ordered-code orientation channel (`ab` vs `ba`) | `candidate_orientation_render_channel_not_pair_formula` |
| `directed_pair_surface_search` | ordered 00..99 mirror/orphan/conflict audit | `render_orientation_layer_over_lookup_not_new_matrix_formula` |
| `directed_surface_sequence_generator_search` | sequential/automaton search over 99 ordered codes | `mirror_render_redundancy_not_origin_formula` |
| `structural_exception_layer_search` | compact ordered-surface render/exception layer | `compact_render_layer_over_lookup_not_new_matrix_formula` |
| `digit_symbol_automorphism_search` | weak digit-identity symmetry over pair labels | `weak_symmetry_signal` |
| `digit_orbit_quotient_search` | lossless quotient accounting for 6<->9 orbits | `weak_lossless_orbit_compression` |
| `digit_orbit_split_label_pair_search` | direct label-pair generator test for the nine non-singleton 6<->9 orbits | `weak_split_metadata_compression` |
| `digit_orbit_directed_provenance_search` | label-blind/anomaly-metadata selector for mixed 6<->9 orbits | `weak_directed_provenance_signal` |
| `digit_orbit_robust_control_search` | robust global/row/column controls for the 6<->9 clue | `robust_weak_6_9_orbit_signal` |
| `nine_identity_render_split_search` | 45-cell 9-identity base worksheet plus Q->6/9 renderer | `base45_renderer_not_promoted` |
| `quotient_inventory_pressure_search` | inventory/apportionment pressure under the 6<->9 quotient | `weak_quotient_inventory_pressure_support` |
| `quotient_pair_formula_search` | direct coordinate formulas over the 46 quotient orbits | `rejected_no_compression` |
| `quotient_line_order_search` | line/order/template scans over the 46 quotient orbits | `weak_quotient_structure_signal_not_formula` |
| `quotient_constructive_fill_search` | frequency-weighted inventory plus quotient order and symbol cycle | `weak_constructive_signal` |
| `quotient_edit_log_mdl_search` | quotient worksheet plus charged edit-log process | `edit_log_not_promoted` |
| `digit_orbit_exception_rule_search` | secondary rule for mixed 6<->9 orbits | `not_promoted_exception_microfit_control_failed` |
| `digit_orbit_exception_context_search` | context/tape features for mixed 6<->9 orbits | `rejected_control_no_auditable_exception_pattern` |
| `digit_visual_symmetry_search` | seven-segment/numpad/clock/6-9 visual symmetry | `reject_visual_6_9_symmetry_as_pair_matrix_formula` |
| `sevenseg_orbit_exception_selector` | selector for the two mixed exact seven-segment rotation orbitals | `weak_visual_exception_microfit_not_formula` |
| `digit_signature_formula_search` | row/column marginal and tape-derived digit signatures | `NEGATIVE_PLATEAU_CONFIRMED` |
| `zero_omission_rule_explainer` | explicit zero-omission rule search from ML signal | `supporting_render_layer_signal_only` |
| `zero_exception_decision_list` | sparse exception list over `code_only` zero renderer | `supporting_render_layer_signal_only` |
| `zero_compact_rule_search` | fixed compact previous-code/geometry zero-render rules | `supporting_render_layer` |
| `shared_e_zero_predicate_search` | fixed `i>=j` predicate linking diagonal E pressure and zero omission | `shared_predicate_signal_only` |
| `e_layer_predicate_search` | E-specific predicate audit after spending diagonal pressure | `weak_e_layer_signal` |
| `priority_masked_e_layer_search` | F/V/N/A blockers before high-block E fill | `exact_local_e_priority_layer_not_global_formula` |
| `high_block_blocker_origin_search` | mini-block drawing/stroke rule for `45,55,77,88` | `high_block_blocker_not_promoted` |
| `render_origin_e_priority_probe` | zero/orientation/render features for E-priority claims | `render_origin_e_priority_not_promoted` |
| `anchored_remaining_fill_search` | E-priority anchors plus frequency/6<->9 fill for the rest | `anchored_remaining_fill_not_promoted` |
| `priority_anchored_quotient_residual_fill` | quotient-correct residual fill after fixed E-priority anchors | `priority_anchored_quotient_residual_not_promoted` |
| `lore_zero_phase_mask_search` | lore-number cyclic mask test for leading-zero omission | `rejected_control` |
| `zero_homophone_transition_origin_probe` | joint zero/orientation/prev-next context reconstruction of pair labels | `weak_context_signal_not_matrix_formula` |
| `residual_exact_repeat_pruned` | residual MDL improvement | `candidate_generator` |
| `chayenne_min8_copy_holdout` | external secondary validation | `secondary_validation` |
| `avar_tar_min8_negative_control` | control pass | `negative_control_pass` |
| `magic_web_numbers` | lore-compatible numbers | `rejected_control` |
| `deep_compact_formula_search` | arithmetic/traversal search below pair lookup | `rejected_control` |
| `pair_table_source_cycle` / `pair_table_seeded_placement` | pair-cell placement by source text or lore seed | `rejected_control` |
| `pair_table_spatial_features` | pair-cell placement by matrix feature after unordered-pair controls | `rejected_control` |
| `pair_table_spatial_dispersion` | deliberate spread/anti-clustering of same-symbol cells | `rejected_control` |
| `pair_assignment_constraint_search` | deterministic count-respecting placement of homophone inventory | `rejected_control` |
| `endpoint_affinity_assignment_search` | symbol endpoint-affinity placement model | `rejected_endpoint_affinity` |
| `bilinear_low_rank_pair_factor_search` | continuous rank-1 pair-label surface probe | `weak_low_rank_signal_not_formula` |
| `quotient_low_rank_pair_factor_search` | continuous low-rank probe over 46 `6<->9` quotient orbits | `technical_gap_closed_rejected_control` |
| `matrix_generator_exhaustive_search` | permissive no-hard-gate matrix/pair generator ledger | `mechanical_partial_not_final_no_exact_matrix_formula` |
| `pair_rule_cover_search` | human-readable digit-pair predicate decision-list search | `lookup_disguise` |
| `symbol_predicate_dnf_search` | per-symbol short predicate/DNF search | `lookup_disguise` |
| `symbol_base_accent_layer_search` | latent base alphabet plus accent/refinement layer over the 14 symbols | `symbol_base_accent_not_promoted` |
| `adaptive_quota_fill_search` | online local quota-fill pair-cell generator | `lookup_disguise` |
| `row_column_balance_objective_search` | row/column/digit balance objective test | `rejected_control` |
| `composite_objective_inverse_search` | sparse composite objective/local-optimum test | `weak_composite_objective_signal_not_formula` |
| `marginal_constraint_solver_search` | compact marginal/orbit/anchor constraints over pair labels | `weak_constraint_signal` |
| `finite_group_pair_formula_search` | hidden finite-group digit formulas | `lookup_disguise` |
| `algebraic_digit_composition_search` | small digit embeddings plus algebraic bucket operations | `lookup_disguise` |
| `direct_symbol_formula_search` | direct coordinate-to-symbol-index formulas | `rejected_no_compression` |
| `pair_hash_formula_search` | cell-local hash/PRNG formulas over lore seeds | `rejected_no_compression` |
| `block_biclique_cover_search` | set-block/biclique colored-graph decomposition | `lookup_disguise` |
| `digit_permutation_formula_search` | arithmetic formula after permuting digit identities | `rejected_control` |
| `digit_order_distance_search` | hidden line/cycle digit-order distance search | `lookup_disguise` |
| `decision_tree_pair_formula_search` | shallow piecewise grid-region formula over pair features | `rejected_control` |
| `alternative_digit_geometry_search` | keypad/numpad/clock/seven-segment digit geometry | `rejected_control` |
| `pair_graph_incidence_search` | graph-incidence/digit-affinity structure of pair-table labels | `rejected_control` |
| `pair_graph_motif_search` | colored graph motifs over pair-table labels | `rejected_no_motif_formula` |
| `triangular_line_pattern_search` | row/column/diagonal line strings as local generator | `rejected_control` |
| `line_template_alignment_search` | shifted/reversed line-family template search | `rejected_control` |
| `row_transition_edit_mdl_search` | human row-to-row edit workflow over matrix lines | `row_transition_not_promoted` |
| `local_2d_pair_rule_search` | local 2D/CA-style triangular-grid rule search | `lookup_disguise` |
| `pair_sequence_automaton_search` | Markov/sequential/mod-k automaton over pair-table traversals | `rejected_control` |
| `homophone_intrasymbol_order_search` | pair choices inside each homophone class by use/frequency/features | `rejected_control` |
| `pair_context_cluster_search` | same-symbol raw code-neighbourhood clustering | `not_promoted_context_cluster_hint` |
| `pair_context_partition_search` | context-only reconstruction of homophone partition | `not_promoted_context_partition_hint` |
| `pair_symbol_stream_compression_search` | induced symbol-stream compression/repetition | `not_promoted_symbol_stream_hint` |
| `pair_symbol_stream_optimization_search` | local-optimum test for repeat-rich stream objective | `rejected_as_original_repeat6_maximization_formula` |
| `latent_digit_factor_search` | hidden digit-class factorization for pair placement | `rejected_control` |
| `lore_text_subsequence_search` | longer lore quote/formula/title windows and subsequences | `rejected_control` |
| `lore_anomaly_operator_search` | lore-number operators restricted to small structural anomaly sets | `rejected_control` |
| `usage_driven_pair_placement_search` | pair-cell placement by code frequency/first use/orientation bias | `rejected_control` |
| `digit_shape_pressure_search` | pair/code placement by digit-balance or visual digit-shape pressure | `rejected_control` |
| `ml_pair_cell_probe` / `ml_homophone_probe` / `ml_zero_omission_probe` | controlled ML generalization probes | `not_promoted` / `simple_prev_code_rule_confirmed_not_ml_upgrade` / `supporting_render_layer_signal_only` |
| `one_equals_tibia` | structural hint | `pareidolia_risk` |
| `seed_prng_search` | seed/PRNG search | `rejected_control` |

The highest-value MDL result is now the tape-based mechanical formula: it
roundtrips 70/70 books using 16 numeric tape components, 62 module slices, and
12 merged same-component book spans. It absorbs 107 of the 2,083 residual
literal digits as exact tape gaps and improves the rough internal description
by `6,597.1` bits versus the literal 62-module formula. The residual
exact-repeat pruning remains useful separately: it lowers the estimated
residual description from 24,627.8 bits to 21,844.3 bits while preserving the
no-translation boundary. The highest-value generator-origin clue for the pair
inventory remains frequency-weighted homophone allocation:
pair-slot counts vs internal symbol frequency give Pearson `0.895`, Spearman
`0.914`, and label-shuffle `p=0.00005`. The next strongest formula-like
inventory model is stochastic: give every symbol one pair cell and allocate
the remaining 41 cells by corpus frequency; this beats uniform by `32.15` bits
and the observed vector is typical under the model. A deterministic
apportionment pass gives secondary support for the same pressure (`power`,
alpha `1.030`, Jefferson, L1 `12`, exact hits `0`, control `p=0.00005`), but
does not recover the exact extra-slot counts. A follow-up residual explainer
reduced L1 only from `12` to `10`, and that gain is common under shuffled
residual controls (`p=0.82820`), so the remaining six-slot transfer is not
explained by the tested module/literal, zero-rendering, quota, entropy, or
position features. A context-clustering pass gives the strongest new clue for
exact homophone grouping: same-symbol pair cells have lower weighted
`prev_pair + next_pair` context divergence than inventory-preserving shuffles
(raw `p=0.00120`), but the signal remains below promotion classification
after multiple metrics (`Bonferroni p=0.01320`). This is a mechanical hint, not an accepted cell
placement formula. A stricter follow-up tries to reconstruct the homophone
partition from pair-window context only; the best rule (`desc_weighted`)
recovers 29/155 true same-symbol pair links (`F1=0.187`, ARI `0.092`,
raw `p=0.00405`), but after correcting for six algorithms and two metrics it
also remains below promotion (`Bonferroni p=0.04860`). A full-stream
compression pass then asks whether the observed table makes the induced symbol
stream more repeat-rich than inventory-preserving shuffled tables. The best
metric is `repeat6_excess` (`3786` vs control mean `3735.6`, raw `p=0.00200`),
but it also remains below promotion classification (`Bonferroni p=0.01599`).
A direct local-optimization follow-up rejects `maximize repeat6_excess` as the
original table objective: swapping only `34` and `99` improves the score from
`3786` to `3803`, and a greedy local optimum reaches `3986` after 19 swaps.
A direct
seed/permutation search over the observed inventory
tested 544,352 candidate placements; the best row reached only `19/55`, while
the same broad family fits shuffled labels at least that well routinely
(`p=0.97605`). The next strongest origin-order clue is digit-first copying:
repeated symbol modules preserve exact code-sequence pairs `45/59` times,
while 500 independent homophone re-render controls produced zero exact long
collisions. Controlled ML probes do not change the table-origin verdict:
pair-cell prediction from grid features reaches only `0.222`
leave-one-cell-out accuracy (`p=0.129`), and homophone ML reaches `0.731` on
multi-symbol holdout but loses to the simple previous-code baseline (`0.763`).
They do add support for the separate zero-rendering layer: non-module local
context reaches balanced accuracy `0.871` with `p=0.032`. The explicit rule
search converts that into `code + previous code`, which reaches balanced
accuracy `0.823` and passes code-preserving shuffles (`p=0.00050`), but costs
about `1048.3` more rough MDL bits than code-only, so it is signal-only rather
than an accepted compact formula. A sparse follow-up decision list over
`code_only` improves the holdout to balanced accuracy `0.871` and accuracy
`0.913` with 19 ordered exceptions, and survives code-preserving train shuffles
(`p=0.00498`). It still costs `82.6` more rough holdout MDL bits than
`code_only`, so it strengthens the zero-render clue as a supporting render
layer without becoming the matrix formula.
A compact-rule pass then tests fixed human-readable variants of the same
signal. The best predictive composite reaches balanced accuracy `0.855` and
9 holdout errors, but costs `15.2` bits more than `code_only`. Several simpler
components improve rough holdout MDL individually: a primary previous-code
whitelist (`+9.9` bits), primary+secondary whitelist (`+8.2` bits), boundary
rule (`+1.0` bit), and a geometric proxy where the previous code has first
digit >= second digit (`+11.6` bits). This is the best new render-layer clue:
zero omission is partly driven by local previous-code/geometry context, but it
still does not derive the pair-table symbols.
A fixed shared-predicate pass then freezes that geometry as `P(i,j)=i>=j`
instead of searching variants. On unordered pair cells this is the diagonal;
on previous ordered codes it is the zero-render rule. It links `5/10`
diagonal E cells, `2/2` 33/66 anchors, and a zero holdout balanced-accuracy
delta of `+0.120` with joint control `p=0.00280`. This is the strongest
cross-layer mechanical clue added by the follow-ups, but it still does not
derive the E labels, the off-diagonal E cells, or the pair table.
An E-specific residual audit then spends the diagonal pressure and asks only
whether the six off-diagonal E cells have a compact predicate. The best
residual rule is `prod_eq_5 OR both_in_4578`: it selects
`15,45,47,48,57,58,78`, covering all six residual E cells with one false
positive (`45`), F1 `0.923`, E-only MDL gain `7.0` bits, and best-of-search
conditional control `p=0.00300`. This is a genuine weak E-layer signal, not a
full-table generator: it explains a sublayer and one near miss, but still
leaves the other symbols and the global pair-cell assignment unresolved.
A priority-mask follow-up then tests the natural blocker variant: claim
`45=F`, `55=V`, `77=N`, and `88=A` before letting `both_in_4578` fill E, with
selected E diagonals and `prod_eq_5`. This gives exact `15/15` local claims
(`p=0.00020`), but only `22/55` total hits with default fill and costs
`2.520x` inventory lookup. It upgrades the E clue to a real local priority
layer while rejecting it as the full matrix formula.
A blocker-origin follow-up then treats `{45,55,77,88}` as its own target
inside the mini-block `{4,5,7,8}`. The rule
`first_edge_plus_suffix_diags_4578` selects exactly those four cells, but
random same-size blockers in the same mini-block also fit the searched grammar
often enough (`p=0.17409`), and connected four-cell strokes are common
(`90/210`, `p=0.43128`). So the blockers still look like a local descriptive
pattern, not a promoted origin formula.
A render-origin follow-up then tests the Raman lacuna directly: whether
zero/omission/orientation features explain the 15 E-priority claims or the
four blockers. The 15-claim global control is nominal (`p=0.04459`), but it
collapses under geometry-stratified controls (`p=1.00000`). The blockers fit
perfectly by a render-feature rule, but also fail geometry-stratified controls
(`p=0.75065`). So render context adds no origin rule beyond the already-known
geometry.
The direct composition test then fixes those 15 claims and tries to fill the
remaining 40 cells with frequency-derived inventory, simple pair orders, and
`6<->9` quotient-shaped orders. The best row reaches `26/55` total hits but
only `11/40` hits outside the anchors, with MDL `2.493x` inventory lookup.
Search-level controls mark it nonrandom (`p=0.00100`), but the signal is the
anchors, not a recovered rule for the remaining matrix.
A quotient-correct ablation then collapses `6<->9`, fixes the resulting 14
priority anchors, and shuffles only the 32 residual quotient labels in
controls. The best fill reaches `11/32` residual hits and `25/46` combined
hits, with residual-hit control `p=0.11289` and MDL `2.293x` quotient lookup.
That closes the composed hypothesis negatively: the E-priority layer is real
locally, but it does not unlock a quotient worksheet for the non-E labels.
A lore-number phase/mirror mask pass then tests whether `1`, `3478`,
Honeminas/Magic Web numbers, or `74032/45331` act as cyclic omission masks.
The best row (`34784`, phase equals second digit) improves `code_only` only
slightly (`0.733` balanced accuracy, `+3.4` rough bits), and digit-multiset
permutations or random same-length strings do as well or better (`p=0.87603`
and `p=0.59504`). That rejects the lore-number mask as a zero-render formula.
A follow-up then restricts lore numbers to the small structural anomaly sets
instead of the whole table. The best overlap is the `469` quotient-6/9 operator
covering all mixed 6/9 orbit cells but selecting 16 cells total (F1 `0.667`);
digit-multiset permutations and same-length random strings match or beat it
(`p=1.0000`, `p=0.9858`). That closes the lore-as-anomaly-operator variant
negatively too.
The ordered-surface audit then separates pair-table content from rendering:
the domain has 99/100 ordered codes, with only `39` absent. The strict lower
triangle is complete (`45/45`); upper including diagonal is `54/55`, missing
`39`. Reverse/mirror rendering preserves 43/44 reverse-available unordered
pairs, with one real directed conflict (`19 -> I`, `91 -> N`) and one lower
orphan (`93 -> N`) caused by absent upper `39`. Mirror-copy plus the `91`
exception and missing-`39` metadata renders the ordered surface losslessly, but
the upper/unordered cell labels remain lookup facts. This changes the best
mechanical formula for orientation/rendering, not the unresolved origin of the
matrix labels.
A directed sequence-generator pass then tests whether the 99 present ordered
codes form a short row/column/diagonal/spiral/mirror sequence. Full directed
and mirror-interleaved orders show a strong raw signal (best `p=0.00067`), but
upper-only does not (`p=0.10859`) and periodic templates remain above inventory
lookup. The signal is the mirror render layer reappearing, not an authorial
sequence formula for the upper table.
A structural exception-layer pass makes that accounting explicit: mirror lower
plus exactly the `91` and `93` residuals renders `99/99` ordered codes and
saves `138.4` bits versus a saturated ordered lookup. It is still `18.6` bits
worse than the compact unordered-pair lookup, so it is accepted only as a
render/exception layer, not as the matrix-origin formula. The same pass keeps
`33/66` diagonal-E anchors and zero-geometry as side evidence, not promotions.
A digit/symbol automorphism pass then tests whether the 55-cell pair table is
nearly invariant under non-trivial digit relabeling. The best signal is the
swap `6 <-> 9`: it preserves 47/55 labels overall, including 10/18 moved
cells, with identity-hit control `p=0.0331`. The eight breaks are localized
to `06/09`, `16/19`, `36/39`, and `68/89`. This is the newest matrix-side
clue, but it remains weak: it does not produce labels, its mapped-symbol
control is weaker (`p=0.0728`), and it is not promoted as the original formula.
A quotient follow-up asks the MDL version of the same question. Under
`6 <-> 9`, the table collapses to 46 pair-cell orbits; a lossless split model
stores 50 labels, marks 4 mixed two-cell orbits, and beats raw pair lookup by
only `3.6` rough bits (`0.983x` lookup, control `p=0.0348`). This is the
strongest matrix-side weak clue so far, but it is still mostly a compacted
lookup table rather than a generator for labels.
The split-label follow-up then isolates only the nine non-singleton `6 <-> 9`
orbits. Their directed label pairs are `IT, TI, NN, VN, NN, II, EE, AA, CT`;
canonically, `IT, IT, NN, NV, NN, II, EE, AA, CT`. Direct affine and periodic
cycle models reach only `11/18` directed label hits and do not beat controls.
The exact structural ledger stores the base sequence `IINNNIEAC`, the mixed
set `{0,1,3,8}` as edge-or-`19/39` metadata, the secondary sequence `TTVT`,
and parity orientation; it costs `49.98` bits (`0.827x` pair-label lookup,
pair-row shuffle `p=0.0339`, directed-label shuffle `p=0.0020`). This is
useful bookkeeping for the `6 <-> 9` clue, not a formula that generates the
symbols.
A label-blind/anomaly-metadata provenance pass then asks whether the mixed
orbits can be named before using symbol labels as predictors. The exact
selector is `directed anomaly OR edge pair`, i.e. the `19/91` conflict,
missing-`39`/lower-`93` orphan, and edge digit orbitals `{0,8}`. It has small
local MDL gain versus explicitly naming a 4-of-9 subset, but exact low-cost
selectors are common in nine-case controls (`p=0.1250` by exact-rule cost).
Conflict flags are treated as frozen structural anomaly metadata, not as
independent evidence, because they ultimately come from the compiled mechanical
table. This sharpens the exception ledger but still does not generate labels.
Robust-control follow-up confirms the clue is not just one fragile shuffle:
fixed `6<->9` gives `51/55` hits, 4 mixed non-singleton orbits, and `+3.57`
rough bits; best-of-45 controls remain significant under global (`p=0.04315`),
row-preserving (`p=0.02720`), and column-preserving (`p=0.04435`) shuffles.
This upgrades confidence in the clue while keeping it weak and non-generative.
A final formal gap test treats `6` and `9` as one base identity `Q`, producing
a 45-cell worksheet over `0,1,2,3,4,5,Q,7,8`, then renders `Q -> 6/9`. That
model closes the difference between a pure 9-identity worksheet and the earlier
46-orbit quotient. It does not improve the formula: `QQ -> 66/69/99` introduces
the cross-pair `69:V`, so the renderer-aware model costs `209.99` bits
(`1.003x` raw lookup, `-0.58` bit gain) versus the prior 46-orbit split gain
of `+3.57` bits. The 46-orbit quotient remains the better mechanical notation.
The quotient-inventory pass makes that clue slightly sharper but still
non-promotable. Keeping the four mixed orbits explicit gives a 50-label target
with normalized apportionment L1 `0.200` versus `0.218` in the original 55-cell
inventory, and pair-label shuffles make this weakly nonrandom (`p=0.02435`).
However, the naive mixed-orbit overhead turns the small inventory MDL gain
into a `-21.32` bit loss. A direct quotient-coordinate formula search then
tests 1,248,362 formulas over the 46 quotient orbits; the best reaches only
`16/46`, costs `1.741x` quotient lookup, and is worse than sampled controls.
The parallel quotient line/order pass finds nominal scan structure: best
line-template match `0.696` with fixed-winner controls down to `p=0.0010`, and
best fill-period match `0.630`, but those rows cost `1.550x` and `1.389x`
lookup respectively. That is a weak ordering signal, not compression.
A constructive quotient-fill pass then combines frequency-weighted inventory,
natural/collapsed quotient fill orders, and symbol cycles. Its best non-leaky
row uses code-usage inventory, natural collapsed row order, and `first_code_table`
symbol order; it reaches only `17/46` and costs `1.700x` lookup, although it
beats search/order controls weakly. This supports a faint manufacturing
pressure, not a recovered generator.
An authorial-process edit-log pass then asks whether a human worksheet can be
rescued by a small charged sequence of `swap`, `copy_neighbor`, and
`manual_label` operations. The best non-leaky edit log starts from a quotient
quota/order worksheet with only `14/46` correct cells, then needs 8 swaps, 9
neighbor copies, and 7 manual labels. It is better than shuffled targets
(`p=0.00826`) but still costs `257.92` bits, `1.473x` lookup, or `-82.78`
bits of gain. That rejects the simple "worksheet plus few edits" origin model
under the current cost contract.
A final low-rank/SVD probe over the same 46 quotient orbits also rejects the
rescue path: best base-orbit LOO is only `11/46`, label-shuffle `p=0.56436`,
and the lossless lower bound is `12.208x` the existing split-lossless quotient.
There is no SVD rescue for the quotient.
So `6 <-> 9` remains a real weak structural pressure, not the recovered
coordinate formula.
A secondary exception-rule pass then asks whether the four mixed `6 <-> 9`
orbits can be generated rather than selected by lookup. The best descriptive
rule is exact on the nine non-singleton orbits: mixed iff `x <= 1 or x mod 5
== 3`, with side orientation by parity (`x` even puts the lower symbol on
`x6`). It improves the rough model to `0.955x` raw lookup, but controls find
exact low-cost selectors and perfect orientation rules often enough
(`p=0.3618` and `p=0.6737`), so this is a microfit, not a promoted formula.
A context/usage/tape follow-up finds a tape-position threshold that separates
the same four mixed orbits exactly (`first_tape_position_ratio_9_over_6_smooth
>= 4.23864`), but the exhaustive 4-of-9 label control gives `p=0.28571`
with Bonferroni `1.00000`; therefore it is another non-promoted descriptive
pattern.
A permissive matrix-generator ledger then tested 294,528 candidates across
pair orders, symbol orders, lore seeds, anomaly overlays for `{19,91}`, missing
ordered code `39`, `33/66`, and weak compositions. The best row reaches only
`21/55` acceptable pair-cell hits (`21/55` against the primary conflict
choice), and every row is classified as `lookup_disguise` under rough MDL. This
does not close exploration, but it makes the current matrix formula status
`mechanical_partial_not_final_no_exact_matrix_formula`.
A follow-up human-predicate rule-cover pass tests whether the table can be
described by a short decision list over digit incidence, diagonals, sums,
differences, modulo classes, set membership, and lore digit groups. It reaches
`34/55` with 10 rules, but this is not special: inventory-preserving label
shuffles reach at least that score routinely (`p=0.7273`), and the rough MDL
cost is still `1.314x` lookup. So this closes one tempting "human formula"
class as lookup-disguise, not as origin.
A per-symbol predicate/DNF pass then gives each symbol its own short rule over
digit, line, modular, geometry, and lore-shaped features. It reaches a much
higher raw `44/55`, but costs `4.592x` lookup and controls also build similarly
good symbol rules (`p=0.3588` for hit count). The apparent perfect rules for
rare symbols are therefore another lookup-disguise failure mode, not a
generator.
A symbol-layer factorization pass then tests the remaining `base + accent`
idea directly: map the 14 internal symbols into a smaller base alphabet and pay
for accent/refinement exceptions. The best row groups symbols as
`*ABC / EF / IL / NORS / TV`, with 16 accent exceptions, but costs `209.95`
bits (`1.003x` raw lookup). Inventory-preserving shuffles get the exact same
score (`p=1.00000`), so this is an inventory partition, not a geometric or
origin formula.
An adaptive quota-fill pass gives the generator the observed homophone
inventory and lets simple online local rules place the 55 cells. The best row
reaches only `13/55` and costs `2.007x` lookup, despite nominal shuffle
separation (`p=0.0100`), so this class does not explain placement. A
row/column balance pass asks whether the author placed cells to smooth symbol
incidence over digits and matrix lines. The strongest metric is only nominal
(`p=0.04019`) and improves with one inventory-preserving swap, with greedy
swaps improving much further; balance is therefore rejected as the original
placement objective. A marginal-constraint solver then asks whether compact
global constraints can recover the table without naming cells. The best total
model is inventory plus `6<->9` orbit split metadata: `198.27` bits, `0.947x`
raw lookup, and control `p=0.00200`. That is a real weak signal, but it still
leaves about `2^141` possible tables. Expensive row/column/diagonal constraints
can shrink the residual to five tables, but at `1.450x` lookup; that is a
lookup-disguise, not a formula. A finite group pass is an even sharper warning: hidden digit values and modular
`sum_and_cyclic_diff` can hit `55/55`, but only by forming 55 groups for 55
cells. Shuffled controls also hit `55/55`, and MDL is worse than lookup
(`1.215x`). Formula-shaped coverage is not evidence unless it compresses.
An algebraic digit-composition pass repeats this warning with a broader but
still auditable family of digit embeddings and bucket operations: it also hits
`55/55` only by creating 55 buckets (`1.093x` raw lookup), while the best
compact algebraic row uses the `6<->9` collapse and reaches only `35/55` at
`1.535x` lookup with ordinary shuffle controls. This reinforces the weak
`6<->9` pressure but does not recover a formula.
Direct coordinate-to-symbol formulas then remove the key-to-symbol lookup
entirely: nearly 480k formulas map `(a,b)` features directly to an index in a
symbol order. The best row reaches only `18/55`, costs `1.807x` lookup, and
does not beat inventory or symbol-order controls. Line-template alignment then
asks whether rows, columns, diagonals, or anti-diagonals are shifted/reversed
copies of one short template. The best column template reaches match fraction
`0.618`, but costs `1.627x` lookup and has control p `0.0735`. Neither class
derives the table.
A hash/PRNG pass tests the obvious "lore number as seed" construction at the
cell level: 51,716 small LCG/xorshift/middle-square/hash formulas over fixed
symbol orders. The best row reaches only `16/55`, costs `1.884x` lookup, and
is worse than controls (`p=0.9669` label shuffle, `p=0.9835` symbol-order
shuffle). A colored-graph block/biclique pass then asks whether the table is a
small union of human-readable digit-set blocks. It reaches `27/55` primary
hits with 4 blocks, but costs `2.146x` inventory lookup and is ordinary under
shuffles (`p=0.6049`), so this is also lookup-disguise.
A visual-symmetry pass then tests the intuitive 6/9 route directly:
seven-segment rotation/mirror, numpad geometry, clock geometry, and required
overlays for `19/91`, absent `39` with present `93`, and `33/66`. The best MDL
row is `sevenseg_rotate180_exact`, with 53/55 majority hits, but it costs
`219.0` bits against a `214.9` bit lookup baseline and is therefore rejected
as a complete visual formula. A narrow follow-up then isolates the two mixed
exact seven-segment orbitals as the `0` and `8` anchors (`06/09` and
`68/89`), and this improves the narrow visual accounting by `11.7` bits.
But the target has only five orbitals, and two-of-five controls often find
equally cheap exact selectors (`p=0.40372`), so this remains a weak visual
microfit rather than an origin formula. A digit-signature pass then tries formulas from
row/column marginals, diagonal labels, frequent-symbol incidence, and
tape-derived features. The true index-formula family reaches only 18/55; the
41/55 bucket diagnostic uses 35 buckets and 21 singletons, so it is lookup-like
and worse than inventory-preserving controls.
Higher-order graph tests then ask whether the colored digit graph has motifs
that explain placement: triangles, wedges, 3-stars, paths, orbit counts, and
same-color spectra. The strongest raw metric has `p=0.04948`, but corrected
Bonferroni p is `1.00000`, so no motif formula is promoted. A local 2D/CA pass
then predicts each triangular-grid cell from already-filled neighbours under
19 fill orders and 12 local models. Best primary accuracy is only `14/55`
(`15/55` acceptable), costs `2.001x` lookup, and controls reach `16/55`.
That rejects a simple neighbour-propagation formula.
A hidden digit-order distance pass then tests whether a person first arranged
digits in a line or cycle and assigned symbols by pair distance/midpoint. The
best sampled line order reaches `48/55`, but it uses 40 groups, costs `1.171x`
lookup, and shuffled labels also reach `48/55` under the same family. This is a
good warning case: high raw coverage can still be a lookup-disguise once search
breadth and MDL are counted.
The strongest new module-layer result is an overlap-tape grammar: the 62
literal modules are recoverable as slices of 16 numeric tape components at
minimum overlap 8. This saves `2,307` gross digits, reduces module-table rough
MDL by `6,237.7` bits after component/start/length addressing, and beats both
per-module digit shuffles and global digit-resample controls at the resolution
of 200 trials (`p=0.00498`). Even at minimum overlap 32 it remains positive
(`1,883` gross digits, `4,705.2` rough MDL bits), so the modules are not best
described as 62 independent literals.
The tape-origin pass then checks whether these components behave like book
units rather than only a superstring compression artifact: 15/16 components
occur as full substrings in the books, all 62 module slices validate, and 107
of the 2,083 residual literal digits are absorbed as exact same-component gaps
inside book recipes. Component-shuffle controls max out at 2 absorbed digits
in 2,000 trials (`p=0.00050`), so this is real support for a higher-order
assembly layer. The exception is important: `T00` is a synthetic 953-digit
overlap chain, not an attested full book substring.
An endpoint-conditioned bridge pass then asks whether the remaining literal
recipe spans are reusable connector strings keyed by adjacent tape/module
endpoints. The corrected target is the 28 internal bridge literals between
tape/module neighbors: leave-one-bridge-out and leave-book-out both cover
`0/590` digits, and the final blind residual holdout covers `0/145`. A plain
train-literal exact-repeat baseline also stays at zero. This closes the bridge
hypothesis negatively: the current evidence supports reusable tapes plus exact
same-component gaps, not a transferable literal-bridge formula for the rest.
The compiled tape-based formula makes this layer executable: it stores 2,157
tape-component digits instead of 4,464 literal module-inventory digits, keeps
62 module-slice aliases, and reconstructs every raw book exactly. It is the
current best book-layer generator, but it still stops at numeric manufacture:
it does not explain the pair-table cell placement and does not produce
plaintext.
The token projection pass links that formula back to the internal code layer:
4,670/5,729 known code tokens map onto tape coordinates, covering
2,150/2,157 tape digits with zero interval-level code/symbol conflicts.
Module slice boundaries align to token boundaries in 51/62 cases, far above
boundary controls (`p=0.00050`). The exceptions matter: 78 tokens cross recipe
segment boundaries, and the pair cells `33` and `66` appear only outside the
reusable tape layer. This supports a code-token tape generator with raw-digit
edge exceptions, not a pure symbol-token grammar.
The first-use order of pair cells inside the reusable tapes was then tested as
a possible bridge back to the original 10x10 table. It fails: 53/55 pair cells
appear on tape, missing only `33` and `66`, but no row/column/diagonal/spiral,
coordinate, or lore-digit order explains their first-use order after controls.
The nominal best row is `digit_order_469`, but its raw p is only `0.04119` and
Bonferroni p is `1.00000`.
The literal-exception pass then isolates the cells found only outside reusable
tapes. The pair-only exceptions are `33` and `66`, both diagonal `E` cells.
That is suggestive (`p=0.03130` for two diagonal cells; `p=0.03765` for both
being `E`), but it remains weak after the six-test structural-control
classification
(`Bonferroni p=0.18779`). Current status: weak clue, not a rule.
Finally, a tape-feature label search asks whether tape/literal usage features
predict the symbol assigned to each pair cell. They do not: the best
interpretable stump with tape+grid features reaches only `0.291` accuracy
against inventory-preserving controls (`p=0.38854`), while tape-only features
are exactly at control level (`0.273`, `p=0.70643`).
A residual follow-up removes the 15 fixed E-priority claims first, then tests
tape, usage, and grid features only on the 40 remaining cells. The best
depth-3 tree reaches `24/40`, but costs `2.209x` residual lookup and is
ordinary under residual-label shuffles (`p(MDL)=0.42557`). That closes the
main tape/usage escape hatch: tape explains assembly, not the non-E pair-table
placement after the strongest local matrix layer is removed.
A second residual follow-up tests the same 40 cells for row, column, diagonal,
anti-diagonal, border, and digit-incidence marginals. The best raw metric is
`row_pure_line_count` (`p=0.01500`), but after multiple-metric correction it
falls to `p=0.38992`. So the non-E residual matrix still has no promoted
line/digit constraint.
The marginal-signature follow-up checks whether rows, columns, diagonals,
anti-diagonals, borders, or digit marginals reveal a simpler pair-table
signature. The diagonal has 5 `E` cells in 10 positions, but this is only
nominal (`p=0.01800`) and remains below promotion classification
(`Bonferroni p=0.16199`). No marginal/table-line statistic is promoted.
The follow-up order test prevents overclaiming: the internal order of `T00`
does not correlate with module id, first book, first offset, first occurrence,
module length, or reuse count. Best absolute Spearman values are near zero
after 20,000 permutation controls; every Bonferroni p-value is `1.00000`.
So `T00` is a compact higher-order assembly component, not an independently
recovered original authoring order.
The ordered-code orientation layer also has a strong local channel:
`pair + previous code` predicts orientation in book holdout at `680/730`
(`0.932`, `p=0.00050`), but grid features fail to generalize to unseen
unordered pairs (`0.526`), so this is a render/channel clue rather than the
original pair-table formula.

## Front Results

| Front | Result |
|---|---|
| Contract/holdouts | Frozen in `generator_search_contract.md` and `generator_holdout_manifest.json`. |
| Parallel saturation audit | Subagent review found no practical untested matrix/sequence family likely to change the current generator-origin verdict. |
| Lore ledger | Every clue is converted into a test or marked context/control. |
| Targets | A-L target matrix created; each candidate declares target coverage. |
| Grid formula | Unordered pair geometry gives 0.990 table accuracy; other arithmetic rules fail. |
| Deep formula search | `unordered_pair`/`triangular_index` are the only near-exact rules; both are equivalent to a 55-cell pair lookup. Best compact modular rule reaches only 0.495. |
| Pair-table constructive search | Homophone class sizes strongly track internal symbol frequencies, but source-cycle, corpus-slice, line-pattern, sequence-automaton, intra-symbol ordering, latent-digit factorization, spatial-feature, spatial-dispersion, count-assignment, digit-permutation, and seeded-placement searches do not recover exact cell placement. |
| Matrix generator exhaustive search | No hard exploration gates: 294,528 candidates over pair orders, symbol orders, lore seeds, anomaly overlays, and weak compositions were recorded. Best row: 21/55; all rows classify as lookup-disguise under rough MDL. |
| Pair rule-cover search | Human-readable digit-pair predicates reach 34/55 with 10 rules, but label-shuffle controls do at least that well (`p=0.7273`) and rough MDL is `1.314x` lookup; rejected as lookup-disguise. |
| Symbol predicate DNF | Per-symbol predicates reach 44/55, but the model costs `4.592x` lookup and shuffles are comparable (`p=0.3588`); rejected as lookup-disguise. |
| Symbol base+accent layer | Best symbol factorization is `*ABC / EF / IL / NORS / TV`, but it costs `1.003x` raw lookup and is identical under inventory shuffles; not a formula. |
| Algebraic digit composition | Simple digit embeddings plus algebraic bucket operations hit 55/55 only with 55 buckets; best compact row is 35/55 at `1.535x` lookup; rejected as lookup-disguise. |
| Marginal constraint solver | Inventory plus `6<->9` split metadata beats raw lookup weakly (`0.947x`, p `0.00200`) but leaves about `2^141` possible tables; tighter constraints are lookup-disguise. |
| Digit/symbol automorphism | Best non-trivial relabeling is `6 <-> 9`: 47/55 total labels preserved, 10/18 moved cells preserved, identity control `p=0.0331`; weak symmetry clue only. |
| Digit orbit quotient | The `6 <-> 9` quotient gives 46 orbits and a split-lossless model with 50 labels, 4 mixed two-cell orbits, and `3.6` rough bits saved vs raw pair lookup; weak compression clue, not label generator. |
| Digit orbit split label-pair search | The nine non-singleton `6 <-> 9` orbit label-pairs are not generated by direct affine/cycle formulas (`11/18` directed hits), but their split metadata compresses to `0.827x` pair-label lookup; weak bookkeeping only. |
| Digit orbit directed provenance | Label-blind/anomaly metadata gives exact selector `directed anomaly OR edge pair` for the four mixed orbitals, but same-size controls make it weak provenance bookkeeping only. |
| Digit orbit robust controls | The `6 <-> 9` clue survives global, row-preserving, and column-preserving controls, including best-of-45 swap correction; robust weak clue, not label generator. |
| Nine-identity render split | A pure 45-cell `Q=6/9` worksheet plus renderer is worse than raw lookup and worse than the 46-orbit quotient because `69` becomes cross-pair metadata. |
| Quotient inventory pressure | The explicit 50-label quotient improves frequency/apportionment fit weakly (`L1/slot=0.200`, pair-label shuffle `p=0.02435`), but mixed-orbit overhead removes MDL promotion; weak support only. |
| Quotient pair formula | 1,248,362 quotient-coordinate formulas were tested over 46 orbit labels. Best row: 16/46, `1.741x` quotient lookup, sampled controls equal or beat it; rejected. |
| Quotient line/order search | Line-template, fill-period, seed-cycle, and symmetry scans over the quotient show nominal structure, but the best line template still costs `1.550x` lookup; weak signal only. |
| Quotient low-rank pair factor | Low-rank/SVD over the same 46 quotient orbits reaches only `11/46`, with label-shuffle `p=0.56436`, stratified `p=0.55738`, and `12.208x` split-lossless cost; rejected. |
| Quotient constructive fill | Frequency-weighted inventory plus quotient order and symbol cycle beats controls weakly, but only reaches 17/46 and costs `1.700x` lookup; weak signal only. |
| Quotient edit-log MDL | A charged human worksheet edit log is better than shuffled targets but still `1.473x` lookup and needs 7 manual labels; not promoted. |
| Digit orbit exception rule | The four mixed `6 <-> 9` orbits are described by `x <= 1 or x mod 5 == 3` with parity orientation, but controls classify it as nine-case microfit. |
| Digit orbit exception context | A tape-position threshold separates the same four mixed orbits exactly, but exhaustive 4-of-9 controls reject it (`p=0.28571`, Bonferroni `1.00000`). |
| Digit visual symmetry | Seven-segment rotation gives 53/55 majority hits, but still costs more than lookup (`219.0` vs `214.9` bits); rejected as visual pair-matrix formula. |
| Seven-segment orbit exception selector | The two mixed exact seven-segment rotation orbitals are exactly anchors `0` and `8`, giving `+7.6` rough bits versus raw lookup under narrow accounting, but two-of-five controls find cheap selectors often (`p=0.40372`); weak microfit only. |
| Digit signature formula | Marginal/diagonal/frequent-symbol/tape signatures give only 18/55 for the index formula; the 41/55 bucket diagnostic is lookup-like and control-negative. |
| Pair hash/PRNG formula | 51,716 cell-local formulas over lore seeds and fixed symbol orders were tested. Best row reaches 16/55 and costs `1.884x` lookup; rejected. |
| Block/biclique cover | Set-block and biclique decompositions reach 27/55 primary hits but cost `2.146x` inventory lookup and match controls (`p=0.6049`); lookup-disguise. |
| Digit order distance search | Hidden line/cycle digit orders were tested. Best line row reaches 48/55, but with 40 groups, `1.171x` lookup cost, and shuffled controls also reaching 48/55; rejected as lookup-disguise. |
| Frequency-weighted stochastic inventory | Candidate formula: one pair cell per internal symbol, then allocate the remaining 41 cells by corpus symbol frequency. It beats a uniform-extra model by `32.15` bits; exact placement remains random/hand under current evidence. |
| Deterministic apportionment inventory | Best rule is `power` alpha `1.030` with Jefferson apportionment over corpus frequencies. It lands 12 L1 cells from the observed extras with no exact rule found, but beats shuffled symbol-label controls (`p=0.00005`), so it supports frequency weighting without replacing the stochastic model. |
| Pair context cluster | Same-symbol pair cells are unusually close in weighted `prev_pair + next_pair` context (`p=0.00120`), but Bonferroni is `0.01320`; track as a non-promoted homophone-grouping hint. |
| Pair context partition | Context-only clustering recovers 29/155 same-symbol links (`F1=0.187`, ARI `0.092`, raw `p=0.00405`), but corrected `p=0.04860`; track as weak non-promoted support. |
| Pair symbol-stream compression | The observed table yields elevated symbol 6-gram repetition (`repeat6_excess=3786`, raw `p=0.00200`), but Bonferroni is `0.01599`; track as non-promoted stream-manufacture hint. |
| Pair symbol-stream optimization | `maximize repeat6_excess` is rejected as the exact original objective: one swap improves 3786 to 3803, and a greedy local optimum reaches 3986. |
| Composite objective inverse search | Sparse combinations of balance, context, digit-shape, zero/repeat, and `6<->9` metrics were tested as a compromise objective. Best composite still improves by swapping `38` and `45`, and best-of-search shuffles are comparable; weak signal, not formula. |
| Zero/homophone transition origin probe | Joint zero-omission, orientation, and prev/next code-context features do not reconstruct the pair-table labels. Best leave-one-pair-out accuracy is only `0.200`; weak context signal, not matrix-origin formula. |
| Shared E/zero predicate | Fixed `P(i,j)=i>=j` links diagonal E pressure and previous-code zero omission (`5/10` diagonal E, `2/2` 33/66 anchors, zero holdout delta `+0.120`, joint `p=0.00280`); signal only, not label generator. |
| Inventory residual explainer | Small balanced corrections using quota remainder, module/literal rate, zero rendering, code entropy, corpus position, and related features improve L1 only from `12` to `10`; shuffled residual controls do this routinely (`p=0.82820`), so rejected. |
| Inventory shuffle/seed search | Python MT, xorshift, LCG, and affine permutations over known/lore seeds plus a brute seed range were tested against the exact 55-cell placement. Best row: 19/55 (`0.345`), worse than shuffled-control expectation (`p=0.97605`); rejected. |
| Lore text subsequence search | Longer curated lore text gives only 13/55 best contiguous-window hits (`0.236`, global shuffle `p=0.990`) and LCS `44/55` is worse than shuffled controls (`p=0.973`); rejected. |
| Lore anomaly operator search | Lore numbers tested only as anomaly selectors still fail controls: best `469` quotient-6/9 operator reaches F1 `0.667` on mixed orbit cells, but digit-multiset and random-string controls do as well or better (`p=1.0000`, `p=0.9858`); rejected. |
| Usage-driven pair placement | Sorting cells by code frequency, first/last use, or orientation bias gives only 15/55 best train hits (`0.273`, control `p=0.653`) and the same rule drops to 6/55 (`0.109`) on holdout usage; rejected. |
| Digit-shape pressure | Pair-cell and ordered-code placements are not extreme for digit entropy, uniformity, zero rate, repeat rate, or raw-distribution matching; best p-values are `0.1045` and `0.1005`; rejected. |
| ML formula probe | Pair-cell grid ML is not promoted (`0.222`, `p=0.129`); homophone ML beats shuffled labels but loses to `prev_code_symbol_top`; zero omission has a non-module local-context signal (`0.871`, `p=0.032`) and supports the render-pass layer only. |
| Zero omission rule explainer | Best explicit rule is `code + previous code`: balanced accuracy `0.823`, accuracy `0.880`, shuffle `p=0.00050`; rough MDL is worse than code-only by `1048.3` bits, so this is supporting render-layer signal only. Avar Tar is not a supervised zero-omission control because it lacks an attested underlying full-code sequence. |
| Zero exception decision list | A 19-rule exception list over `code_only` reaches holdout balanced accuracy `0.871`, accuracy `0.913`, and shuffle `p=0.00498`; rough MDL is still `82.6` bits worse than `code_only`, so this supports the render layer only. |
| Lore zero phase mask | Cyclic masks from `1`, `3478`, Honeminas/Magic Web, and `74032/45331` improve `code_only` only slightly (`0.733` balanced accuracy); digit permutations and random same-length strings do as well or better, so rejected. |
| Orientation render rule | `pair + previous code` predicts `ab` vs `ba` on book holdout at `0.932` and beats pair-preserving shuffled controls (`p=0.00050`), but leave-one-pair-out grid generalization reaches only `0.526`; useful render channel, not table-origin formula. |
| Directed surface sequence generator | The 99 present ordered codes show a strong full/mirror-order sequence signal (`p=0.00067`), but upper-only is weak (`p=0.10859`) and periodic templates cost more than lookup; mirror redundancy only. |
| Decision-tree grid formula | Shallow region rules reach at most 36/55 (`0.655`) but controls often do the same (`p=0.269`); best compact depth-2 row has `p=0.033`, not enough to promote. |
| Alternative digit geometry | Keypad, numpad, clock/circle and seven-segment layouts were tested with global layout controls; best row was `circle_1_to_0` at 28/55 (`0.509`, global `p=0.348`); rejected. |
| Pair graph incidence | Treating the 55 cells as a colored graph over digits gives no surviving digit-affinity signature. Best metric is degree-vector smoothness (`p=0.08665`, Bonferroni `0.51987`); rejected. |
| Digit-permutation formula | `sum+product` can reach 55/55 only because it uniquely identifies the unordered pair; the best compact non-lookup rule is matched by controls. |
| Endpoint affinity assignment | Symbol-specific digit endpoint affinities plus small pair features reach only `0.145` leave-one-pair-out accuracy; exact-inventory assignment is diagnostic but not predictive, so rejected. |
| Row transition edit MDL | A human workflow that edits each matrix line from the previous line still costs `1.070x` lookup and has negative MDL gain; inventory-preserving shuffles are comparable. |
| Symbol-vs-digit origin | Repeated symbol chunks usually preserve exact numeric code sequences; this supports pre-rendered numeric chunk copying over independent symbol re-rendering. |
| Module overlap grammar | The 62 modules collapse into 16 overlap-tape components; all modules are reconstructed by component slices, with positive rough MDL and digit-shuffle controls. This is a mechanical generator candidate, not semantic content. |
| Module tape origin | 15/16 tape components occur in the books and 107 residual digits become exact same-component gaps in recipes (`p=0.00050`); this supports assembly by reusable numeric tapes. |
| Endpoint literal bridge MDL | The 28 internal bridge literals do not transfer as endpoint-conditioned bridges: best family and train-literal exact-repeat baseline cover `0/590` leave-one-bridge/book digits and `0/145` blind residual-holdout digits; rejected. |
| Module tape order | `T00` order is not explained by module id, first occurrence, length, or reuse. Treat the large component as a compact assembly tape, not recovered authorial order. |
| T00 internal FSA compression | Tokenized `T00` has strong local order-1 code regularity inside slice sequences, but permuting the slice order preserves the gain (`p=0.38162`); this is slice-internal regularity, not recovered authorial order. |
| Tape-based mechanical formula | Lossless 70/70 generator: 16 tape components, 62 module slices, 12 merged same-component spans, 1,976 remaining literal digits, `6,597.1` rough MDL bits saved. |
| Tape tokenization | 4,670 tokens map to tape coordinates with 0 code/symbol conflicts; 51/62 module slices align to token boundaries, but `33`/`66` live outside reusable tapes and some edges cut rendered tokens. |
| Tape first-use pair order | First-use order of 53 tape-observed pair cells does not match tested matrix/lore-digit traversals; `digit_order_469` is not significant after controls. |
| Tape literal exceptions | `33` and `66` are outside-only diagonal `E` pair cells, but the signal is weak after multiple-test correction (`Bonferroni p=0.18779`). |
| Tape feature pair-label search | Tape/literal usage features do not predict symbol labels over pair cells beyond shuffled-inventory controls (`p=0.38854`). |
| Pair marginal signature | Diagonal concentration of `E` is visible but not significant after correction (`p=0.01800`, Bonferroni `0.16199`); rows/columns/borders/marginals rejected. |
| Magic Web / Honeminas | Numbers remain mechanism lore or short overlaps; no predictive generator promoted. |
| `1 = Tibia` | The sole conflict `{19,91}` uses `1`, but no standalone rule is accepted. |
| Homophones | Previous-code selector beats symbol-top baseline modestly on holdout; candidate only. |
| Zero omissions | Context renderer improves over code-only but remains a local supporting render layer, not the matrix formula. |
| Module grammar | Exact residual repeats survive; templates are not yet accepted. |
| Seeds / PRNG | Tested seeds do not beat controls enough to promote. |
| Chayenne / YTC | Chayenne validates copy/generator mechanics secondarily; YTC remains too short/novel. |
| Avar Tar | Negative control passes for minLen=8; short-repeat rules are rejected as leaky. |

## Verdict

The generator-origin search strengthens the manufacturing explanation:

```text
handmade 10x10 table
+ unordered-pair geometry
+ frequency-weighted homophone allocation
+ homophone choices
+ copied pre-rendered numeric modules reducible to 16 overlap-tape components
+ 70/70 tape-based book formula with same-component gap absorption
+ mostly coherent code-token projection with raw-digit edge exceptions
+ copied shorter residual repeats
+ secondary zero render pass
```

It still does not find the original exact pair-cell placement formula. It also
does not find a new translation, a new word, or an official number<->plaintext
pair.

The 2026-06-19 saturation audit classifies the remaining obvious routes as
practically exhausted under the current corpus. A formal bilinear low-rank
variant was run after the audit: it gives a weak rank-1 predictive signal
(`18/55` LOO, `p=0.02597`) but costs far more than compressed inventory lookup,
so it does not derive the original 10x10 matrix. The same test rerun on the
`6 <-> 9` quotient is weaker (`11/46`, `p=0.56436`, `12.208x`
split-lossless), so the quotient does not rescue the continuous-surface
hypothesis. The finite compressor for
`T00` was also run: it confirms local token regularity, but slice-order controls
show that the order of slices itself is not recovered.

---

[<- Mechanism & Origin Model](11-mechanism-origin-model.md) . [Wiki home](README.md)
