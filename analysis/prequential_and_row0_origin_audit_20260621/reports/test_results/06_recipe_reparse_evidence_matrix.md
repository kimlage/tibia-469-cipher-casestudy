# Recipe Reparse Evidence Matrix

Classification: `recipe_externality_reduced_but_generation_claim_still_partial`
Translation delta: `NONE`

## Purpose

Audit 04 showed that about half of the `8558.667`-bit validation scope
was still fixed recipe or non-learned ledger. This matrix checks whether
the later deterministic reparse audits actually reduce that externality,
without turning a compression result into a plaintext or authorial-intent
claim.

## Frozen Scope

- Validation scope: `8558.667` bits.
- Fixed/non-learned ledger in audit 04: `4272.791` bits.
- Fixed/non-learned share: `49.924%`.

## Evidence Matrix

| Question | Status | Key evidence |
|---|---|---|
| `does_deterministic_reparse_roundtrip_future_suffixes` | `passed` | cutoffs [10, 20, 35, 50, 60]; all roundtrip; mean reparse-active -112.720 bits |
| `does_reparse_signal_beat_content_controls` | `passed_low_trial_count` | observed beats all control means; 8 trials per control family |
| `is_numeric_prefix_training_uniquely_supported_single_cutoff` | `failed_as_authorial_order_proof` | cutoff 50; observed gain 10441.679; random max 10489.489; p=0.1538 |
| `is_numeric_prefix_training_uniquely_supported_multicutoff` | `failed_as_authorial_order_proof` | cutoffs [35, 50, 60]; mean wins 2/3; cutoff 60 observed 4467.255 vs random mean 4564.670 |
| `does_recipe_reparse_survive_public_bookcase_family_holdout` | `passed_with_active_recipe_ties` | beats raw 19/19; beats active 14/19; component failures rescued 3/3 |
| `are_family_reparse_losses_localized` | `passed_as_loss_localization_not_promotion` | 5 local losses; all roundtrip True; worst `hellgate_public_bookcase_33` 8.986 bits; loss components {'copy_address_bits': 4, 'no_positive_component': 1} |
| `do_family_copy_address_losses_survive_same_coordinate_repricing` | `failed_as_real_reparse_loss` | original losses 4/5; rebased nonpositive 5/5; mean delta 4.667 -> 0.000 bits |
| `does_family_holdout_reparse_beat_active_after_address_correction` | `passed_address_corrected_family_holdout` | beats raw 19/19; beats/ties active 15/19 -> 19/19; mean reparse-active -139.959 -> -161.381 |
| `does_family_holdout_reparse_depend_on_test_carryover` | `passed_no_test_carryover_raw_baseline` | roundtrip 19/19; no-carry beats raw 19/19; mean gain 1054.570 bits |
| `does_single_book_holdout_reparse_without_self` | `passed_singleton_complement_inventory` | roundtrip 70/70; beats raw 70/70; mean gain 469.307; min gain 96.055 |
| `where_do_singleton_holdout_copies_source_from` | `mapped_with_boundary_caveat` | 189 copy items; 11062 copied digits; boundary share 0.271; current-prefix share 0.000723 |
| `does_singleton_holdout_survive_book_bounded_sources` | `passed_book_bounded_source_constraint` | roundtrip 70/70; beats raw 70/70; mean gain 464.898; mean penalty 4.409 |
| `does_singleton_holdout_survive_same_family_source_exclusion` | `passed_family_excluded_source_constraint` | roundtrip 70/70; beats raw 70/70; family-labeled 46/46; mean gain 460.251; max penalty 119.076 |
| `does_online_reparse_reduce_full_corpus_recipe_cost` | `passed_as_mechanical_compile_not_semantic_claim` | 8558.667 -> 8343.062 bits; gain 215.605; roundtrip 70/70 |
| `where_is_the_online_prefix_per_book_frontier` | `passed_after_bootstrap_with_book0_failure` | book-bounded raw wins 69/70; after bootstrap 69/69; failures [0]; mean gain 419.761; break-even book 2 |
| `does_an_explicit_book0_seed_close_the_online_bootstrap_failure` | `passed_as_bootstrap_accounting_not_bound_promotion` | book0 online-raw 10.499 bits; seed wins/ties 70/70; strict wins 69/70; failures []; stream saving 10.499 |
| `does_book0_seed_survive_complete_formula_rescoring` | `failed_as_formula_promotion` | seeded 8344.041 vs online 8343.062; delta 0.979; book-bounded delta 305.198; promoted 0 |
| `why_does_seeded_rescore_fail` | `explained_by_literal_payload_penalty` | payload penalty 37.821; non-payload savings 36.842; net 0.979; local seed saving 10.499 |
| `can_exception_signaling_rescue_the_book0_seed` | `failed_requires_negative_descriptor_cost` | zero-cost delta 0.979; required descriptor < -0.979; nonnegative promotes False; one-book index delta 7.108 |
| `does_numeric_online_order_survive_order_controls` | `passed_against_tested_orders` | best raw `numeric`; best charged `numeric`; 6 random orders |
| `is_the_online_prefix_book_frontier_numeric_order_unique` | `failed_as_numeric_order_uniqueness_proof` | numeric after-bootstrap 69/69; perfect controls 10/11; random perfect 6/6; best mean `random_04` +0.549 bits |
| `can_order_frontier_control_orders_promote_a_formula` | `failed_no_promotable_order` | frontier best `random_04`; full raw best `numeric`; full charged best `numeric`; promotable 0; random_04 +61.452 frontier vs +521.038 charged |
| `do_simple_source_contexts_rescue_the_cross_op_near_tie` | `failed_simple_contexts_worse` | candidate +0.027; source margin +0.027; oracle -11.209; best context `book_half` +5.872; prefix losses 5/5 |
| `does_earliest_source_canonicality_remove_decoder_source` | `failed_encoder_side_only` | earliest 261/261; unique 123/261; ambiguous 138; decoder-computable False; dependency removed False; default/exception 5 defaults, 256 exceptions |

## Decision

- Recipe externality: `partially_reduced_by_deterministic_reparse`.
- Generation explanation: `stronger_mechanical_recipe_signal_not_final_authorial_method`.
- Numeric order: `frontier_not_unique_and_control_orders_not_promotable`.
- Row0 origin remains exogenous.
- No plaintext, translation, or case-reopening claim is introduced.
