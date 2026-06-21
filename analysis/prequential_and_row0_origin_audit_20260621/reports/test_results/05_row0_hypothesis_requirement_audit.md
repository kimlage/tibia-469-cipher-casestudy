# Row0 Hypothesis Requirement Audit

Classification: `row0_origin_requirements_all_tested_no_origin_formula`
Translation delta: `NONE`

## Purpose

This follow-up forces each requested `row0` origin hypothesis through the
same falsifiable checklist: clear algorithm, descriptive cost, coverage,
contradictions, negative controls, and random/permuted comparison. It
does not search for plaintext and does not change the compression bound.

## Lookup Baselines

- Lookup cost given inventory: `160.521` bits.
- Direct symbol-alphabet cost: `209.405` bits.
- Direct observed-label alphabet cost: `214.879` bits.
- Promotion rule: a row0-origin formula must beat lookup after rule, parameters, exceptions, order, and search costs.

## Requirement Matrix

| Hypothesis | Status | Required fields | Cost | Coverage | Failure gate |
|---|---|---:|---:|---|---|
| `manual_authorial_lookup` | `accepted_as_exogenous_substrate_not_origin_formula` | `yes` | 209.405 | 55/55 by definition | `baseline_only_no_compact_origin` |
| `simple_permutation_or_group_rule` | `rejected_lookup_disguise` | `yes` | 254.408 | 55/55 hits for the best finite-group row, but it uses one group per cell | `lookup_disguise_after_rule_cost` |
| `grid_10x10_mechanism` | `rejected_as_origin_formula` | `yes` | 366.184 | 21/55 best matrix hits; 15/55 best local-2D hits | `partial_grid_signal_not_lossless_below_lookup` |
| `order_or_frequency_derivation` | `rejected_holdout_or_control` | `yes` | not promoted; tested as accuracy/control signals | 6/55 holdout same-rule hits | `holdout_and_control_failure` |
| `known_external_text_source` | `not_attested_rejected_as_source_formula` | `yes` | no promoted external source ledger | 21/55 at best when lore-word symbol orders are allowed inside matrix search | `no_primary_fixed_external_source` |
| `workbook_or_script_artifact` | `rejected_as_origin_explanation_for_in_game_table` | `yes` | provenance-preserving ingestion, not a generator | explains where the project reads row0-like tables from, not why CipSoft/game data has that table | `provenance_preservation_not_origin_generator` |

## Controls

| Hypothesis | Negative / random-permuted control interpretation |
|---|---|
| `manual_authorial_lookup` | Not applicable as a promoted generator: this is the direct lookup/null baseline that random or permuted formulas must beat. |
| `simple_permutation_or_group_rule` | Control p=1.0 in the consolidated audit: the exact finite-group row acts as one group per cell and is classified as lookup disguise. |
| `grid_10x10_mechanism` | Matrix search has an above-random partial-hit p-value, but the charged candidate is not lossless and remains costlier than lookup; local 2D/grid controls therefore do not promote an origin formula. |
| `order_or_frequency_derivation` | Usage/fill-order controls are ordinary: usage_train_p_ge_observed is 0.6534 and tape first-use Bonferroni is 1.0. |
| `known_external_text_source` | Searched lore/text orders can create partial matrix hits, but no fixed CipSoft/in-game source is attested; Avar Tar remains a negative control. |
| `workbook_or_script_artifact` | Artifact provenance is a code/path audit rather than a stochastic table generator: scripts preserve source cells and no synthesizing algorithm is found. |

## Decision

- Hypotheses checked: `6`.
- Hypotheses with all required fields: `6`.
- Promoted row0 origin formulas: `0`.
- Acceptable negative result recorded: `origin_of_row0_continues_exogenous`.
- No translation, plaintext, or case-reopening claim is introduced.
