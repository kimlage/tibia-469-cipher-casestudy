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
| `does_online_reparse_reduce_full_corpus_recipe_cost` | `passed_as_mechanical_compile_not_semantic_claim` | 8558.667 -> 8343.062 bits; gain 215.605; roundtrip 70/70 |
| `does_numeric_online_order_survive_order_controls` | `passed_against_tested_orders` | best raw `numeric`; best charged `numeric`; 6 random orders |

## Decision

- Recipe externality: `partially_reduced_by_deterministic_reparse`.
- Generation explanation: `stronger_mechanical_recipe_signal_not_final_authorial_method`.
- Numeric order: `supported_against_order_controls_but_not_unique_against_random_train_inventories`.
- Row0 origin remains exogenous.
- No plaintext, translation, or case-reopening claim is introduced.
