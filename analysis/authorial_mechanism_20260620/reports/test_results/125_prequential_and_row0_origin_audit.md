# 125. Prequential and Row0 Origin Audit

Classification: `analysis_only_predictive_component_audit_row0_origin_exogenous`
Translation delta: `NONE`

## Scope

The active `compression_bound` is confirmed at `8558.667` bits.
This audit does not search for a lower bit count. It freezes the active
recipe and tests whether the learned component streams keep predictive
advantage on held-out books. Separately, it records what `row0` explains
and why its origin remains exogenous under current evidence.

Important limitation: the LZ recipe is still fixed from the full corpus.
The predictive test covers adaptive component streams, not recipe discovery.

## Predictive Validation

| Split | Train books | Test books | Train bits | Test online bits | Test frozen bits | Uniform bits | Online gain | Frozen gain |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `prefix_10_future_suffix` | `10` | `60` | `2082.914` | `2202.962` | `2238.160` | `2359.989` | `157.027` | `121.828` |
| `prefix_20_future_suffix` | `20` | `50` | `2819.373` | `1466.502` | `1490.129` | `1553.677` | `87.175` | `63.548` |
| `prefix_35_future_suffix` | `35` | `35` | `3318.021` | `967.855` | `979.305` | `1016.319` | `48.465` | `37.014` |
| `prefix_50_future_suffix` | `50` | `20` | `3766.220` | `519.656` | `522.113` | `557.283` | `37.628` | `35.170` |
| `prefix_60_future_suffix` | `60` | `10` | `4141.094` | `144.781` | `144.102` | `155.181` | `10.399` | `11.078` |

Prefix future-suffix result:
- Online gain summary vs uniform: `{'n': 5, 'min': 10.399306435802686, 'median': 48.46459083970183, 'mean': 68.13860858248265, 'max': 157.02652180961695}`
- Frozen gain summary vs uniform: `{'n': 5, 'min': 11.078379023643208, 'median': 37.01410740929407, 'mean': 53.72780495219314, 'max': 121.8282395541919}`
- Prefix online nonpositive failures: `0`
- Prefix frozen nonpositive failures: `0`

Random train-set controls compare each numeric prefix against random
same-size train books. A low p-value would mean numeric-prefix future
prediction is unusually strong; here this is a control ledger, not a
promotion of authorial order.

| Cutoff | Observed online gain | Random median gain | p(random >= observed) |
|---:|---:|---:|---:|
| `10` | `157.027` | `251.748` | `1.0000` |
| `20` | `87.175` | `225.923` | `1.0000` |
| `35` | `48.465` | `172.876` | `1.0000` |
| `50` | `37.628` | `99.699` | `0.9801` |
| `60` | `10.399` | `46.332` | `0.9602` |

Block and public-bookcase family holdouts are included in JSON. They are
not treated as temporal future tests.

## Row0 Origin Boundary

`row0` explains the code->symbol substrate and lets the book-generation
formula operate on reconstructed digit books. It does not explain why
the 10x10 pair cells have those labels.

| Hypothesis | Status | Coverage | Cost / control note |
|---|---|---|---|
| `manual_authorial_lookup` | `accepted_as_exogenous_substrate_not_origin_formula` | 55/55 by definition | 209.40452071316824; controls `not meaningful because this is the lookup baseline` |
| `simple_permutation_or_group_rule` | `rejected_lookup_disguise` | 55/55 hits for the best finite-group row, but it uses one group per cell | 254.40822783567893; controls `1.0` |
| `grid_10x10_mechanism` | `rejected_as_origin_formula` | 21/55 best matrix hits; 15/55 best local-2D hits | 366.1843428780211; controls `{'matrix_control_p': 2.1032806543283516e-09, 'local_2d_primary_mdl_gain_control': None}` |
| `order_or_frequency_derivation` | `rejected_holdout_or_control` | 6/55 holdout same-rule hits | not promoted; tested as accuracy/control signals; controls `{'usage_train_p_ge_observed': 0.6534488503832055, 'tape_first_use_bonferroni': 1.0, 'pair_marginal_verdict': 'rejected_control'}` |
| `known_external_text_source` | `not_attested_rejected_as_source_formula` | 21/55 at best when lore-word symbol orders are allowed inside matrix search | no promoted external source ledger; controls `0.0001999600079984003` |
| `workbook_or_script_artifact` | `rejected_as_origin_explanation_for_in_game_table` | explains where the project reads row0-like tables from, not why CipSoft/game data has that table | provenance-preserving ingestion, not a generator; controls `manual code inspection of ingestion scripts; no generated table algorithm found` |

## Decision

- The current bit bound remains `compression_bound`, not an authorial method.
- Learned components retain positive prefix-holdout advantage over uniform
  baselines, but the fixed full-corpus recipe remains a posthoc dependency.
- `row0` origin remains exogenous. No tested manual/permutation/grid/
  frequency/external/workbook hypothesis becomes a promoted origin formula.
- No translation, plaintext, or reopening claim is made.
