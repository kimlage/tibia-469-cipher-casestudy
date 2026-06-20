# 119. Row0 Origin Frontier Audit

Classification: `row0_origin_frontier_saturated_current_corpus`
Translation delta: `NONE`

## Purpose

This audit changes the unit from compressor tuning to the unresolved origin
of the `row0` / 10x10 pair table. It indexes the existing table-origin
tests and records whether any family can be promoted as a generative
formula for the pair labels.

The answer remains no. The active sequential LZ model keeps
`8561.792` bits as `compression_bound`,
but it assumes `row0`; it does not derive the pair-cell table.

## Family Ledger

| Family | Status | Key evidence |
|---|---|---|
| `matrix_generator_exhaustive` | `rejected_lookup_disguise` | 21/55 hits, -195.8 bits vs lookup, 294528 lookup-disguise candidates |
| `pair_rule_cover` | `rejected_lookup_disguise` | 34/55 hits (61.8%), -65.8 bits vs lookup |
| `digit_orbit_6_9` | `weak_signal_not_formula` | 51/55 quotient-preserved hits, fixed-swap control p=0.0152 |
| `tape_feature_pair_label` | `rejected_control` | 16/55 hits via `diff<=4` |
| `bilinear_low_rank_pair_factor` | `weak_low_rank_signal_not_formula` | 18/55 leave-one-out hits, control p=0.0260, 14.931x inventory lookup |
| `structural_exception_layer` | `supporting_render_layer_not_origin_formula` | compact_render_layer_over_lookup_not_new_matrix_formula; -18.6 bits vs unordered lookup |
| `k5_eye_pair_model` | `rejected_control` | 18/55 label hits, label-gain control p=0.4510 |
| `eye_state_5x2_model` | `rejected_control` | 20/55 label hits, label-gain control p=0.1765 |
| `hierarchical_provenance_pair_label` | `rejected_as_row0_origin` | 16/55 hits, hit control p=0.4194, -196.1 bits vs lookup |

## Decision

The row0/table-origin frontier is saturated under the current corpus.
This is not a claim that the table has no origin; it is a narrower
claim that the tested source families do not produce a charged,
controlled, holdout-capable row0 formula.

Further micro-sweeps over book compression should not be treated as
mainline progress unless they also improve generation explanation.
Further row0 work should proceed only if it satisfies at least one
of the following requirements:

- Predict pair-cell labels under holdout or prequential scoring, not after seeing the whole table.
- Beat direct unordered-pair inventory lookup after charging rule, mapping, exception, and search costs.
- Explain the special ordered-surface facts, including the {19,91} conflict and missing 39, without ad hoc posthoc overrides.
- Generalize against inventory-preserving, label-shuffle, and topology/control baselines.
- Or supply CipSoft/in-game primary evidence for a symbol table or exact book-to-plaintext crib.

## Boundary

- `compression_bound`: active best charged book-generator cost.
- `generation_explanation`: still partial; predictive for book-level
  learned components, not a derivation of `row0`.
- `row0_origin`: open but frontier-saturated on the current evidence.
- `translation_delta`: `NONE`.
