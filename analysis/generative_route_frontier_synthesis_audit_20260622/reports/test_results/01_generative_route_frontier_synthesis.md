# Generative Route Frontier Synthesis

Classification: `GENERATION_ROUTE_FRONTIER_SYNTHESIS`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Consolidate recent operation-token generation routes before opening another gate. This synthesis asks whether the whole family should remain the main route after hidden state, schedule state, multiset/order, within-book ordering, and sequence mutation all failed promotion criteria.

## Route Matrix

| Route | Classification | Signal | Controls | Decision |
| --- | --- | --- | --- | --- |
| `latent_hmm_joint_operation_tokens` | `LATENT_NONLOCAL_STATE_PILOT_NOT_PROMOTED` | `-2138.447 bits vs factorized` | `shuffle_p05 0/5` | `not_promoted_hidden_state_distribution_signal` |
| `schedule_state_joint_operation_tokens` | `SCHEDULE_STATE_MULTISTREAM_CLUE_NOT_GENERATOR` | `-1652.574 bits vs factorized` | `shuffle_p05 0/5` | `not_promoted_schedule_distribution_signal` |
| `book_multiset_then_order` | `BOOK_MULTISET_ORDER_FACTORIZATION_AUDIT_ONLY` | `57.222 bag bits vs global` | `permuted_feature_p95 0/5` | `audit_only_bag_factorization` |
| `within_book_order_given_true_multiset` | `WITHIN_BOOK_ORDER_PROGRAM_NOT_PROMOTED` | `-19.387 bits vs uniform order` | `shuffled_train_p95 1/5; shuffled_test_p95 0/5` | `order_index_program_rejected` |
| `previous_book_sequence_mutation` | `SEQUENCE_MUTATION_PROGRAM_NOT_PROMOTED` | `-1216.694 bits vs sequence unigram` | `shuffled_train_p95 0/5; random_source_p95 2/5` | `whole_sequence_mutation_rejected_even_as_lower_bound` |

## Decision

The operation-token route family is closed as the main route under current evidence. It can still provide diagnostics, but not the next generator attempt.

Next constructive route: `digit_level_content_boundary_transducer`.

It should work at digit/content-boundary level and must not grant the operation-token sequence, book multiset, within-book order, target-conditioned copy availability, or exact internal starts.
