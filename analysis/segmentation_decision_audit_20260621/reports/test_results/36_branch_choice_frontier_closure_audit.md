# Branch Choice Frontier Closure Audit

Classification: `branch_choice_frontier_closed_audit_only`
Translation delta: `NONE`

## Purpose

Gate 36 closes the current branch-choice weak-signal frontier. It does not
propose a new parser. It checks whether gates 16-35 collectively justify
continuing with simple branch-choice policies or whether that subline should be
treated as saturated under current evidence.

## Summary

- Gates audited: `20`.
- Non-oracle gates audited: `18`.
- Complete promoted parser rules in this frontier:
  `0`.
- Partial promoted rule clues in this frontier:
  `0`.
- Clean-zero partial non-oracle rules:
  `4`.
- Closure classification: `branch_choice_frontier_closed_audit_only`.

## Closure Criteria

- Oracle repairs show the stable residual branch is available:
  `True`.
- Complete non-oracle promoted parser rules:
  `0`.
- Partial promoted rules:
  `[]`.
- Clean-zero non-oracle partial rules:
  `[{'stem': '24_contextual_mode_selector_audit', 'residual_hits': 5, 'holdout_status': 'zero_clean=1/5; cover_residual=1/5'}, {'stem': '26_hierarchical_context_backoff_audit', 'residual_hits': 5, 'holdout_status': 'zero_clean=1/5; cover_residual=1/5'}, {'stem': '27_observable_decision_tree_policy_audit', 'residual_hits': 4, 'holdout_status': 'zero_clean=5/5; cover_residual=1/5'}, {'stem': '32_phase_grid_segmentation_audit', 'residual_hits': 1, 'holdout_status': 'zero_clean=1/5; cover_residual=1/5'}]`.
- Weak-signal threshold overlap confirmed:
  `True`.
- Row0/plaintext changed: `False`.
- Compression bound changed: `False`.

## Gate Ledger

| gate | category | classification | best label | complete promoted | partial promoted | residual hits | clean false changes | holdout status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | oracle_diagnostic | single_drift_oracle_partial_path_dependency | one_or_two_stable_projection_repairs | False | False | None | None | oracle_only |
| 17 | observable_repair | observable_repair_policy_rejected | baseline_window5 | False | False | 0 | None | stable=False; matches_oracle=3/5 |
| 18 | conditional_repair | conditional_repair_classifier_partial_not_promoted | if_peak_len_le5_then_skip_to_next_peak_ge5 | False | False | 4 | None | stable=True; matches_oracle=5/5 |
| 19 | two_stage_repair | two_stage_conditional_repair_rejected | if_peak_len_le5_then_skip_to_next_peak_ge5 | False | False | 4 | None | stable=False; matches_oracle=3/5 |
| 20 | oracle_diagnostic | post_repair_oracle_localizes_residual_not_promoted | one_or_two_stable_projection_corrections | False | False | 59 | None | oracle_only |
| 21 | single_feature | post_repair_residual_feature_screen_rejected | None | False | False | None | None | zero_clean=None/5; cover_residual=1/5 |
| 22 | continuation_objective | residual_branch_continuation_objectives_rejected | None | False | False | None | None | zero_clean=0/5; cover_residual=1/5 |
| 23 | learned_ranker | branch_ranker_prequential_rejected | None | False | False | None | None | zero_clean=1/5; cover_residual=1/5 |
| 24 | context_table | contextual_mode_selector_rejected | context_combo | False | False | 5 | 0 | zero_clean=1/5; cover_residual=1/5 |
| 25 | context_stability | contextual_mode_stability_rejected | None | False | False | None | None | not_applicable |
| 26 | context_backoff | hierarchical_context_backoff_rejected | start_active_to_combo | False | False | 5 | 0 | zero_clean=1/5; cover_residual=1/5 |
| 27 | small_tree | observable_decision_tree_policy_rejected | None | False | False | 4 | 0 | zero_clean=5/5; cover_residual=1/5 |
| 28 | target_boundary | target_boundary_recurrence_policy_rejected | max_left_right_r8 | False | False | 1 | 194 | zero_clean=0/5; cover_residual=1/5 |
| 29 | future_copy | future_copy_opportunity_policy_rejected | max_copy_positions | False | False | 2 | 130 | zero_clean=0/5; cover_residual=1/5 |
| 30 | source_state_local | source_state_continuity_policy_rejected | min_source_delta | False | False | 6 | 13 | zero_clean=0/5; cover_residual=1/5 |
| 31 | source_state_global | global_source_state_continuity_policy_rejected | min_source_delta | False | False | 6 | 13 | zero_clean=0/5; cover_residual=1/5 |
| 32 | phase_grid | phase_grid_segmentation_policy_rejected | source_mod0_10 | False | False | 1 | 0 | zero_clean=1/5; cover_residual=1/5 |
| 33 | context_nearest | context_nearest_branch_policy_rejected | nearest_context_l8_r8_action_class | False | False | 0 | 8 | zero_clean=0/5; cover_residual=1/5 |
| 34 | weak_signal_consensus | structural_signal_consensus_policy_rejected | k3:source=global_min_source_delta:phase=source_mod0_10:future=max_copy_positions:boundary=max_left_right_r8 | False | False | 0 | 0 | zero_clean=4/5; cover_residual=1/5 |
| 35 | weak_signal_decomposition | structural_vote_residual_decomposition_audit_only | None | False | False | None | None | not_applicable |

## Decision

The branch-choice weak-signal frontier is closed under current evidence. The
stable branch is observable and oracle-repairable, but every tested non-oracle
family either fails residual coverage, creates clean-control changes, fails
holdout/stability, or collapses back to the active baseline.

Next progress should target a richer path/state segmentation mechanism or a
source-free explanation for the target digit stream, not another local
combination of the rejected weak signals.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
