# Prequential and Row0 Origin Audit

Classification: `analysis_only_falsifiable_audit_row0_origin_exogenous`
Translation delta: `NONE`

## Scope

- Frozen validation compression bound: `8558.667` bits
- Later compression-only bound recorded but not used as generation evidence: `8343.062` bits
- No plaintext, translation, or case-reopening claim is made.
- Limitation: the LZ recipe is fixed from the full corpus; this audit tests learned component scoring, not recipe discovery.

## Predictive Validation

Predictive classification: `predictive_signal_partial_not_generation_method`

| Split | Train books | Test books | Train bits | Test online bits | Test frozen bits | Uniform bits | Online gain | Frozen gain | Gap/event |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `prefix_10_future_suffix` | `10` | `60` | `2082.914` | `2202.962` | `2238.160` | `2359.989` | `157.027` | `121.828` | `0.0980` |
| `prefix_20_future_suffix` | `20` | `50` | `2819.373` | `1466.502` | `1490.129` | `1553.677` | `87.175` | `63.548` | `0.1997` |
| `prefix_35_future_suffix` | `35` | `35` | `3318.021` | `967.855` | `979.305` | `1016.319` | `48.465` | `37.014` | `0.2599` |
| `prefix_50_future_suffix` | `50` | `20` | `3766.220` | `519.656` | `522.113` | `557.283` | `37.628` | `35.170` | `0.2566` |
| `prefix_60_future_suffix` | `60` | `10` | `4141.094` | `144.781` | `144.102` | `155.181` | `10.399` | `11.078` | `0.2642` |

### Baselines And Controls

- Prefix online gain summary: `{'n': 5, 'min': 10.399306435802686, 'median': 48.46459083970183, 'mean': 68.13860858248265, 'max': 157.02652180961695}`
- Prefix frozen gain summary: `{'n': 5, 'min': 11.078379023643208, 'median': 37.01410740929407, 'mean': 53.72780495219314, 'max': 121.8282395541919}`
- Contiguous block online summary: `{'n': 7, 'min': 9.226846890659033, 'median': 30.142627770213437, 'mean': 48.77399125683207, 'max': 166.10544902154516}`
- Public-bookcase family online summary: `{'n': 19, 'min': -2.965740114144694, 'median': 7.734879288532312, 'mean': 15.279535791339448, 'max': 116.89542333405711}`
- Public-bookcase family nonpositive failures: `[{'label': 'hellgate_public_bookcase_33', 'online_gain_vs_uniform_bits': -2.965740114144694, 'frozen_gain_vs_uniform_bits': -2.9397073262090743}, {'label': 'hellgate_public_bookcase_6', 'online_gain_vs_uniform_bits': 0.16108090167024613, 'frozen_gain_vs_uniform_bits': -0.3951809595302933}, {'label': 'hellgate_public_bookcase_8', 'online_gain_vs_uniform_bits': -0.1659543966254695, 'frozen_gain_vs_uniform_bits': -0.1674535755674995}]`

| Cutoff | Observed prefix online gain | Random median gain | p(random >= observed) |
|---:|---:|---:|---:|
| `10` | `157.027` | `251.748` | `1.0000` |
| `20` | `87.175` | `225.923` | `1.0000` |
| `35` | `48.465` | `172.876` | `1.0000` |
| `50` | `37.628` | `99.699` | `0.9801` |
| `60` | `10.399` | `46.332` | `0.9602` |

### Component Ablations

Values are bits saved by the learned component over replacing only that component with a uniform code on prefix holdouts.

| Component | Min | Median | Mean | Max |
|---|---:|---:|---:|---:|
| `copy_length` | `-3.040` | `4.665` | `8.443` | `27.741` |
| `literal_payload` | `2.840` | `9.512` | `19.093` | `64.278` |
| `item_type` | `10.599` | `40.330` | `40.603` | `65.008` |

### Parameter Stability

- Parameters identical across prefix splits: `True`
- Declared parameters: `{'copy_length_alpha': 1, 'copy_length_context': 'book_id < 35 versus book_id >= 35', 'item_type_alpha': 2.0, 'item_type_order': 0, 'item_type_split_book': 6, 'literal_payload_alpha': 1.0, 'literal_payload_order': 2}`
- Context coverage totals: `{'copy_length': {'present_context_events': 253, 'missing_context_events': 303}, 'literal_payload': {'present_context_events': 480, 'missing_context_events': 8}, 'item_type': {'present_context_events': 556, 'missing_context_events': 0}}`

Interpretation: prefix and contiguous-block tests retain positive advantage over uniform, but the family split has nonpositive failures. The result is therefore predictive signal only, not a final generation method.

### Family Failure Follow-Up

A follow-up failure audit decomposes the three public-bookcase family failures.
They are component/sample-size stress cases rather than a new row0-origin signal:
`hellgate_public_bookcase_33` and `hellgate_public_bookcase_8` are copy-only
failures dominated by copy-length underperformance, while
`hellgate_public_bookcase_6` is online-positive but frozen-negative because the
item-type component loses to uniform under frozen counts.
See [02_family_holdout_failure_audit.md](test_results/02_family_holdout_failure_audit.md).

### Component Selector Follow-Up

A train-CV component selector then asks whether those failures can be rescued
without seeing the held-out family. For every public-bookcase family, inner
training-family validation keeps all three active components. The selector
therefore leaves the same failures in place; only a heldout oracle improves the
ledger, so no component fallback is promoted.
See [03_train_cv_component_selector_audit.md](test_results/03_train_cv_component_selector_audit.md).

### Recipe Externality Follow-Up

A recipe-externality audit then quantifies the main remaining limitation of
the prequential evidence. Of the `8558.667`-bit validation scope,
`4285.876` bits (`50.076%`) are the prequentially scored copy-length,
literal-payload, and item-type components, while `4272.791` bits
(`49.924%`) remain fixed recipe or non-learned ledger: fixed bits,
literal structure without payload, and copy addresses. The code path
confirms that train/test splits score event rows extracted from the full
formula before splitting; they do not discover held-out literal/copy
segmentation or copy source addresses.
See [04_recipe_externality_audit.md](test_results/04_recipe_externality_audit.md).

### Recipe Reparse Evidence Matrix

A follow-up evidence matrix then checks whether the later deterministic
reparse audits actually reduce that fixed-recipe externality. They do:
deterministic reparse roundtrips all future suffixes at cutoffs
`10/20/35/50/60` and beats the active suffix recipe under frozen counts.
Content controls are also weaker. The boundary remains partial because
train-set controls show random same-size training inventories can match
or exceed the numeric prefix: single-cutoff `50` gives `p=0.1538`, and
the multi-cutoff control loses to the random-train mean at cutoff `60`.
See [06_recipe_reparse_evidence_matrix.md](test_results/06_recipe_reparse_evidence_matrix.md).

### Recipe Reparse Family Holdout

A public-bookcase family holdout then tests whether deterministic recipe
discovery fails on the same family axis where component-only scoring had
failures. It does not: reparse beats raw digits for `19/19` families and
for `3/3` component-failure families. It beats the active frozen recipe in
`14/19` families, so the active full-corpus recipe still has local wins and
the generation explanation remains partial.
See [08_recipe_reparse_family_holdout.md](test_results/08_recipe_reparse_family_holdout.md).

### Recipe Reparse Family Loss Decomposition

The five families where reparse does not beat the active frozen recipe
are then decomposed by charged component. All five still roundtrip and
still beat raw digits. Four losses are dominated by copy-address bits,
with identical literal/copy inventory against the active recipe; one is
an exact tie. This localizes the remaining active-recipe advantage
without promoting a new generation formula.
See [09_recipe_reparse_family_loss_decomposition.md](test_results/09_recipe_reparse_family_loss_decomposition.md).

## Row0 Origin Boundary

Row0 classification: `row0_origin_remains_exogenous`

### What Row0 Explains
- Supplies the code->symbol substrate used to reconstruct the 70 book digit strings byte-exactly.
- Supports unordered pair/mirror geometry and render-exception audits.
- Allows the book-generation formula to operate on digit strings.

### What Remains Exogenous
- Why those unordered pair labels occupy the 10x10 table cells.
- A compact lossless algorithm for the pair labels after rule/search/exception costs.
- A primary CipSoft/in-game plaintext, symbol table, or book->meaning crib.
- A derivation of row0 from the active LZ book-generation formula.

### Substrate Facts

- Books in committed digit corpus: `70`
- Row0 symbols: `14`
- Class codes represented: `99`
- Missing two-digit codes from class map: `['39']`
- Sources: [`occ_streams.json`](../../audit_20260609/homophone_channel/occ_streams.json), [`books_digits.json`](../../audit_20260609/books_digits.json)

### Origin Hypotheses

| Hypothesis | Status | Coverage | Cost | Contradictions / controls |
|---|---|---|---:|---|
| `manual_authorial_lookup` | `accepted_as_exogenous_substrate_not_origin_formula` | 55/55 by definition | 209.405 | none inside inventory; explains no compact origin; controls `not meaningful because this is the lookup baseline` |
| `simple_permutation_or_group_rule` | `rejected_lookup_disguise` | 55/55 hits for the best finite-group row, but it uses one group per cell | 254.408 | best exact row is classified lookup_disguise; hash rows are low-coverage and do not compress; controls `1.0` |
| `grid_10x10_mechanism` | `rejected_as_origin_formula` | 21/55 best matrix hits; 15/55 best local-2D hits | 366.184 | partial hits require many exceptions or posthoc overlays; no lossless compact grid algorithm; controls `{'local_2d_primary_mdl_gain_control': None, 'matrix_control_p': 2.1032806543283516e-09}` |
| `order_or_frequency_derivation` | `rejected_holdout_or_control` | 6/55 holdout same-rule hits | not promoted; tested as accuracy/control signals | train and stream signals do not survive as a controlled row0 generator; controls `{'pair_marginal_verdict': 'rejected_control', 'tape_first_use_bonferroni': 1.0, 'usage_train_p_ge_observed': 0.6534488503832055}` |
| `known_external_text_source` | `not_attested_rejected_as_source_formula` | 21/55 at best when lore-word symbol orders are allowed inside matrix search | no promoted external source ledger | lore/textual seeds behave as searched symbol orders, not primary row0 evidence; controls `0.0001999600079984003` |
| `workbook_or_script_artifact` | `rejected_as_origin_explanation_for_in_game_table` | explains where the project reads row0-like tables from, not why CipSoft/game data has that table | provenance-preserving ingestion, not a generator | export scripts preserve source cells and do not synthesize a compact row0 formula; controls `manual code inspection of ingestion scripts; no generated table algorithm found` |

### Row0 Requirement Matrix Follow-Up

A requirement-matrix follow-up forces all six requested row0-origin families
through the same checklist: algorithm, descriptive cost, coverage,
contradictions, negative controls, and random/permuted comparison. All six
families have explicit entries; promoted row0-origin formulas remain `0`.
Lookup baselines are `160.521` bits given inventory, `209.405` bits for the
direct symbol alphabet, and `214.879` bits for the direct observed-label
alphabet.
See [05_row0_hypothesis_requirement_audit.md](test_results/05_row0_hypothesis_requirement_audit.md).

## Decision

- `8558.667` bits remains a frozen validation scope here, not a final authorial method.
- The learned component signal survives prefix and block holdout but fails some family holdouts, so it is not promoted beyond partial predictive structure.
- The full-corpus fixed-recipe limitation is partially reduced by deterministic reparse evidence, including public-bookcase family holdouts; the remaining family losses localize mostly to copy-address overhead, so the generation claim remains partial.
- All requested row0-origin hypothesis families have been checklist-audited; none passes as an origin formula.
- `row0` continues exogenous: the active book generator assumes the table rather than deriving it.
- No translation, plaintext, or case reopening is introduced.
