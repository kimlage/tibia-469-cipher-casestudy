# Seed Requirement Closure Audit

Classification: `seed_primacy_requirements_closed_audit_only`
Translation delta: `NONE`

## Purpose

This gate checks whether the seed-primacy front covers the requested
baselines, metrics, controls, categories, and epistemic boundaries. It
does not add a new seed search.

## Summary

- Tasks passed: `13/13`.
- Candidate labels: `['canonical_prefix', 'greedy_coverage', 'operational_0_9', 'public_bookcase_order_prefix', 'singleton_centrality_top']`.
- Family/bookcase controls: `38`.
- Final seed classification: `AUDIT_ONLY_COMPRESSION`.
- Books `0..9` special as seed: `False`.
- Alternative k=10 seed better: `True`.
- Operational `0..9` gain survives declaration cost: `False`.
- Prequential seed generator promoted: `False`.
- Authorial seed claim: `BLOCKED_NEEDS_EXTERNAL_SOURCE`.

## Requirement Matrix

| Requirement | Status | Evidence |
|---|---|---|
| `analysis_only_front_exists` | `passed` | `analysis/seed_primacy_audit_20260621` |
| `operational_seed_0_9_baseline` | `passed` | `operational_0_9 candidate and decision books_0_9_special_as_seed=False` |
| `seed_sizes_5_10_15_20` | `passed` | `best_by_k=[5, 10, 15, 20]` |
| `random_same_size_controls` | `passed` | `random_ks=[5, 10, 15, 20]` |
| `permuted_order_prefix_controls` | `passed` | `permuted_ks=[5, 10, 15, 20]` |
| `centrality_baseline` | `passed` | `singleton_centrality_top=[5, 10, 15, 20]` |
| `metadata_bookcase_baseline` | `passed` | `public_bookcase_order_prefix=[5, 10, 15, 20]` |
| `leave_one_family_bookcase_controls` | `passed` | `family_holdout_controls=38` |
| `declaration_cost_charged` | `passed` | `seed_declaration_bits present on all candidate rows` |
| `metrics_present` | `passed` | `required metrics present` |
| `prequential_train_test_check` | `passed` | `promotes_prequential_seed_generator=False` |
| `row0_unchanged` | `passed` | `row0_origin_status unchanged_exogenous` |
| `no_translation_plaintext` | `passed` | `translation_delta=NONE, plaintext_claim=False` |

## Decision

- The seed front satisfies the requested analysis-only audit scope.
- The result remains `AUDIT_ONLY_COMPRESSION`, not a promoted seed-origin formula.
- No row0, plaintext, translation, semantic, or case-reopening claim is introduced.
