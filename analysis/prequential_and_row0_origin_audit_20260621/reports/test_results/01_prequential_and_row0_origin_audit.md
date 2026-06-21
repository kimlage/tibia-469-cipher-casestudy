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
See [02_family_holdout_failure_audit.md](02_family_holdout_failure_audit.md).

### Component Selector Follow-Up

A train-CV component selector then asks whether those failures can be rescued
without seeing the held-out family. For every public-bookcase family, inner
training-family validation keeps all three active components. The selector
therefore leaves the same failures in place; only a heldout oracle improves the
ledger, so no component fallback is promoted.
See [03_train_cv_component_selector_audit.md](03_train_cv_component_selector_audit.md).

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
See [04_recipe_externality_audit.md](04_recipe_externality_audit.md).

### Recipe Reparse Evidence Matrix

A follow-up evidence matrix then checks whether the later deterministic
reparse audits actually reduce that fixed-recipe externality. They do:
deterministic reparse roundtrips all future suffixes at cutoffs
`10/20/35/50/60` and beats the active suffix recipe under frozen counts.
Content controls are also weaker. The boundary remains partial because
train-set controls show random same-size training inventories can match
or exceed the numeric prefix: single-cutoff `50` gives `p=0.1538`, and
the multi-cutoff control loses to the random-train mean at cutoff `60`.
See [06_recipe_reparse_evidence_matrix.md](06_recipe_reparse_evidence_matrix.md).

### Recipe Reparse Family Holdout

A public-bookcase family holdout then tests whether deterministic recipe
discovery fails on the same family axis where component-only scoring had
failures. It does not: reparse beats raw digits for `19/19` families and
for `3/3` component-failure families. It beats the active frozen recipe in
`14/19` families, so the active full-corpus recipe still has local wins and
the generation explanation remains partial.
See [08_recipe_reparse_family_holdout.md](08_recipe_reparse_family_holdout.md).

### Recipe Reparse Family Loss Decomposition

The five families where reparse does not beat the active frozen recipe
are then decomposed by charged component. All five still roundtrip and
still beat raw digits. Four losses are dominated by copy-address bits,
with identical literal/copy inventory against the active recipe; one is
an exact tie. This localizes the remaining active-recipe advantage
without promoting a new generation formula.
See [09_recipe_reparse_family_loss_decomposition.md](09_recipe_reparse_family_loss_decomposition.md).

### Family Holdout Address Space Audit

A same-coordinate address audit then checks whether those copy-address
losses are real recipe losses. They are not: when the active recipe is
rebased into the same holdout coordinate system used by the reparse,
all five families roundtrip and the mean copy-address delta falls from
`4.667` bits to approximately `0.000` bits under a `0.001` bit epsilon.
The prior active-recipe local wins were therefore an address-space
comparison artifact, not a reparse failure.
See [10_family_holdout_address_space_audit.md](10_family_holdout_address_space_audit.md).

### Address-Corrected Family Scoreboard

Applying the same correction to all public-bookcase family holdouts
changes the active comparison from `15/19` beat-or-tie families before
correction to `19/19` after correction. Reparse still beats raw digits
in `19/19` families, and the mean reparse-minus-active gap moves from
`-139.959` to `-161.381` bits. This is stronger predictive recipe
evidence, still not row0 derivation or semantics.
See [11_family_holdout_address_corrected_scoreboard.md](11_family_holdout_address_corrected_scoreboard.md).

### No-Test-Carryover Family Holdout

A stricter variant then removes cross-book carryover inside each held-out
family. Each held-out book is parsed from the training-complement
inventory alone. The result still roundtrips `19/19` families and beats
raw digit coding in `19/19`, with mean gain `1054.570` bits versus raw.
This shows the family signal does not depend on letting earlier held-out
books feed later held-out books.
See [12_family_holdout_no_test_carryover_audit.md](12_family_holdout_no_test_carryover_audit.md).

### Leave-One-Book-Out No-Self Audit

At singleton granularity, every book is then held out individually and
reparsed from the other `69` books only. All `70/70` books roundtrip and
beat raw digit coding; mean gain is `469.307` bits and the weakest gain
is still `96.055` bits. This confirms item-level mechanical redundancy,
while still not proving an authorial order because the inventory is the
full complement of other books.
See [13_leave_one_book_out_no_self_audit.md](13_leave_one_book_out_no_self_audit.md).

### Leave-One-Book-Out Source Attribution

The singleton result is then expanded into a source atlas. Across `70`
singleton reparses there are `189` copy items and `11062` copied digits.
The copied digits are attributable to concrete source books or, rarely,
the already-emitted current prefix (`8` digits, share `0.000723`). The
important caveat is explicit: `3001` copied digits (`0.271289`) cross
artificial source-book boundaries created by concatenating the complement
inventory without separators.
See [14_leave_one_book_out_source_attribution_audit.md](14_leave_one_book_out_source_attribution_audit.md).

### Book-Bounded Singleton Source Audit

The boundary caveat is then tested directly by forbidding copy sources
from crossing source-book boundaries. The singleton result survives:
`70/70` books roundtrip and beat raw digit coding, mean gain remains
`464.898` bits, and the mean penalty versus the unbounded singleton
parser is only `4.409` bits.
See [15_leave_one_book_out_book_bounded_source_audit.md](15_leave_one_book_out_book_bounded_source_audit.md).

### Family-Excluded Singleton Source Audit

The same singleton setup is then made stricter for public-bookcase
families: when a target book has a known family label, all books in that
same family are removed from both frozen train counts and copy sources.
The result still roundtrips `70/70` books, beats raw digit coding in
`70/70`, and the family-labeled subset beats raw in `46/46`. Mean gain
is `460.251` bits, minimum gain is `56.053` bits, and the maximum penalty
versus the book-bounded singleton parser is `119.076` bits. This reduces
same-family memorization as an explanation for the singleton signal,
while still not promoting a final authorial method.
See [16_leave_one_book_out_family_excluded_source_audit.md](16_leave_one_book_out_family_excluded_source_audit.md).

### Online Prefix Book Frontier Audit

Finally, the deterministic online parser is decomposed at per-book
granularity under the true numeric-prefix constraint: book `n` can use
only books `< n` as external inventory. The book-bounded variant
roundtrips `70/70`, beats raw digit coding in `69/70`, and the only
failure is book `0`, before any prior-book inventory exists. After that
bootstrap, it beats raw in `69/69` books; the cumulative book-bounded
gain crosses break-even at book `2`. Mean book-bounded online gain is
`419.761` bits. This strengthens sequential mechanical generation
evidence while keeping the bootstrap caveat explicit.
See [17_online_prefix_book_frontier_audit.md](17_online_prefix_book_frontier_audit.md).

### Online Bootstrap Seed Policy Audit

The bootstrap caveat is then tested directly as an accounting policy.
Book `0` costs `488.857` bits under the online parser and `478.358`
bits as a raw uniform seed, so the online cold start is `10.499` bits
worse than raw. Charging book `0` as one explicit raw seed leaves books
`1-69` unchanged and gives `70/70` wins-or-ties against raw, with
`69/70` strict wins and no local failures. This closes the local
bootstrap failure as a seed-policy issue, but is not promoted as a new
compression bound or authorial proof.
See [18_online_bootstrap_seed_policy_audit.md](18_online_bootstrap_seed_policy_audit.md).

### Seeded Online Formula Rescore Audit

The seed policy is then converted back into actual formula recipes and
rescored under the complete active ledger. The result rejects promotion:
the existing online formula remains `8343.062` bits, while replacing
book `0` with one literal seed gives `8344.041` bits (`+0.979`). A
book-bounded seeded variant is much worse at `8648.260` bits
(`+305.198`). The seed is therefore retained only as bootstrap
accounting, not as a new full-formula compression bound.
See [19_seeded_online_formula_rescore_audit.md](19_seeded_online_formula_rescore_audit.md).

### Seeded Rescore Loss Decomposition

The rescore rejection is then decomposed by component. The seeded
formula does save non-payload costs (`36.842` bits), but it adds a
`37.821`-bit literal-payload penalty, leaving the formula `0.979` bits
worse than online. In the book-bounded seeded variant, the largest
penalty is copy address (`136.412` bits). This explains why the seed
can close the local cold-start ledger while still failing complete
formula scoring.
See [20_seeded_rescore_loss_decomposition.md](20_seeded_rescore_loss_decomposition.md).

### Seed Exception Signal Cost Audit

The last seed fallback is tested as an exception-signaling problem. Even
the best-case zero-cost deterministic fallback is `+0.979` bits worse
than the existing online formula. A one-book exception index would make
the delta `+7.108` bits, and a bitmask would make it `+70.979` bits.
Promotion would require a negative descriptor cost (`< -0.979` bits),
so the seed exception cannot become a promoted formula under any
nonnegative signaling cost.
See [21_seed_exception_signal_cost_audit.md](21_seed_exception_signal_cost_audit.md).

### Online Order Frontier Controls

The per-book online frontier is then tested against the same order
families used by the aggregate order-control audit. Numeric order still
beats raw digit coding in `69/69` books after its first bootstrap
position, but that criterion is not unique: `10/11` tested orders have
perfect after-bootstrap raw wins, including `6/6` seeded random orders.
The best after-bootstrap mean-gain and total-gain order is `random_04`,
at `+0.549` bits versus numeric mean after-bootstrap gain and `+61.452`
bits versus numeric total gain. This keeps the online frontier as
predictive-parser evidence but rejects the stronger claim that the
per-book frontier proves numeric book order.
See [22_online_order_frontier_controls.md](22_online_order_frontier_controls.md).

### Order Frontier Promotion Gate

The non-unique order-frontier result is then checked against the
complete formula ledger. The local frontier winner, `random_04`, is
`+61.452` bits better than numeric on book-bounded frontier total, but
it is `+188.584` bits worse under the complete online formula before
order cost and `+521.038` bits worse after the arbitrary permutation
descriptor. No tested non-numeric order is promotable under a
nonnegative descriptor. The frontier metric is therefore retained as
a predictive diagnostic, not a compression-bound promotion score.
See [23_order_frontier_promotion_gate.md](23_order_frontier_promotion_gate.md).

### Recipe Representation Dependency Gate

The compact online recipe representation is then audited as a dependency
ledger. Book `length`, copy `target_start`, literal `length`, and op
`type` are derivable representation artifacts: removing `70 + 261 +
87 + 348` fields preserves `8343.062` bits and `70/70` roundtrip.
The recipe JSON shrinks from `24355` bytes to `12633` bytes. The
remaining declared operation-level dependencies are still literal
text (`87` fields / `857` digits), copy source (`261` fields), and
copy length (`261` fields).
See [30_recipe_representation_dependency_gate.md](30_recipe_representation_dependency_gate.md).

### Item Type Op Shape Boundary Gate

The item-type boundary is then separated into two layers. The
split-only forced-rule item-type model remains part of the generation
profile: it moved the old formula from `8561.792` to `8558.667` bits,
for a `3.125`-bit gain
(`2.125` bits
under the conservative extra-declaration check), and alpha `2` remains
best with alpha `1` `0.309`
bits worse. But explicit recipe op `type` fields are not a separate
compact dependency: `348`
fields are derivable from operation shape, with literal/copy-shaped
ops `87`/
`261`, zero score delta, and
`70/70` roundtrip.
See [33_item_type_op_shape_boundary_gate.md](33_item_type_op_shape_boundary_gate.md).

### Current Active Profile Boundary Gate

A current-active-profile gate then aligns the older frozen validation
scope with the latest active mechanical ledger. The active bound is
`8177.317` bits:
copy-length default/exception first moved the formula to
`8206.178`
bits, and copy-source default/exception moved it to
`8177.317`
bits. The full active learned streams cover
`87.526%`
of the bound and have positive frozen gain in every tested prefix,
block, and public-bookcase family split; the family frozen minimum is
`6.269`
bits. The gate does not prove recipe discovery: exact active reparse
requires state
`(book_pos, previous_item, previous_copy_source, previous_copy_length)`,
and the best state-free replacement is
`15.186`
bits worse.
See [34_current_active_profile_boundary_gate.md](34_current_active_profile_boundary_gate.md).

### Copy Source State Compression Gate

The source-state blocker is then sharpened. The active source
default was previously described as needing previous source and
previous length, but the cost rule only uses their sum. The gate
therefore replaces
`(book_pos, previous_item, previous_copy_source, previous_copy_length)` with
`(book_pos, previous_item, previous_copy_end)` for source-cost
classification. It preserves the same default/exception stream
(`2990.838` bits,
`5` defaults,
`256` exceptions,
`0` mismatches)
and reduces the aggregate candidate-state proxy from
`969111171` to
`26758611`
(`97.239%`).
This is a real state simplification, not a parser promotion.
See [35_copy_source_state_compression_gate.md](35_copy_source_state_compression_gate.md).

### Active Reparse Feasibility After State Compression Gate

A follow-up feasibility gate then asks whether that state compression
changes the implementation frontier for exact active reparse. It does
for the source-state dimension: every tested book-level end-state proxy
falls below one million, the worst book-level proxy is
`614250`, and cutoff `60`
has
`9`/
`10` books below `250000`.
The aggregate source-state proxy still remains
`313.5x`
the old frozen-count DP state count, and the gate does not solve the
full active objective, adaptive counts, tie-breaking, copy source
selection, copy length declaration, literal payload, or item-type
dependencies. It is a prototype frontier, not a parser promotion.
See [36_active_reparse_feasibility_after_state_compression_gate.md](36_active_reparse_feasibility_after_state_compression_gate.md).

### Cutoff 60 Source-State Reparse Prototype Gate

A cutoff-60 prototype then executes the cheaper operational step:
deterministic reparse recipes are repriced with the active
`previous_copy_end` default/exception source ledger. The result
roundtrips `10`/
`10` held-out books, beats
raw digit coding in `10`/
`10`, and is
`-10.241`
bits versus the old uniform-address reparse comparator in aggregate.
Only
`4`/
`10` books improve individually,
and no source-state recipe reoptimization is performed.
See [37_cutoff60_source_state_reparse_prototype_gate.md](37_cutoff60_source_state_reparse_prototype_gate.md).

### Multi-Cutoff Source-State Reparse Reprice Gate

The same source-state repricing then generalizes across all standard
prefix cutoffs `10/20/35/50/60`. Every cutoff roundtrips, every
held-out book remains positive against raw digit coding, and the
active `previous_copy_end` source ledger beats uniform-address reparse
in aggregate at
`5`/
`5` cutoffs. Total
aggregate delta across the five suffix evaluations is
`-112.968`
bits. This is still repricing of deterministic recipes, not
source-state-aware recipe reoptimization.
See [38_multicutoff_source_state_reparse_reprice_gate.md](38_multicutoff_source_state_reparse_reprice_gate.md).

### Multi-Cutoff Source Choice Optimizer Gate

A fixed-segmentation source-choice optimizer then tests whether the
same copied chunks can be sourced more cheaply without changing
segmentation or copy lengths. It finds no cheaper local substitutions:
`0`/
`514` sources change,
and optimized-minus-repriced cost is
`+0.000`
bits. This closes the simple source-only improvement path; future
source-state work needs segmentation, copy-length, or global path-state
optimization.
See [39_multicutoff_source_choice_optimizer_gate.md](39_multicutoff_source_choice_optimizer_gate.md).

### Multi-Cutoff Global Source Path Optimizer Gate

A global source-path DP then tests the stronger fixed-segmentation
hypothesis: a locally worse source may be chosen if its
`previous_copy_end` state makes later copies cheaper. This does improve
the fixed deterministic recipes. It changes
`10`/
`514` sources, beats the
repriced ledger in
`5`/
`5` cutoffs, and totals
`-42.359`
bits versus repricing. Max DP state count is only
`14`. Segmentation and copy
lengths remain fixed, so this is a partial source-path optimizer rather
than a full active parser.
See [40_multicutoff_global_source_path_optimizer_gate.md](40_multicutoff_global_source_path_optimizer_gate.md).

### Full-Corpus Source Path Formula Gate

The same source-path idea is then tested as a full-corpus fixed-recipe
formula improvement. The exact DP is used only to propose same-chunk
source substitutions; the candidate is accepted only after the real
adaptive source default/exception stream is rescored. It improves the
active formula from
`8177.317` to
`8162.412` bits, a
gain of `+14.905` bits,
by changing
`2`/
`261` sources. The
copy-source ledger drops from
`3002.838` to
`2987.933` bits.
Segmentation and copy lengths remain fixed.
See [41_full_corpus_source_path_formula_gate.md](41_full_corpus_source_path_formula_gate.md).

### Full-Corpus Source Substitution Frontier Gate

The promoted fixed-recipe source-path formula is then checked for a
local single/pair substitution frontier. Every same-chunk legal source
single and pair is rescored under the full adaptive source stream. The
best pair changes two source positions and improves the bound from
`8162.412` to
`8160.827` bits,
a gain of
`+1.585` bits.
The gate searches
`376` singles
and
`69849` pairs;
triples and higher-order substitutions remain outside this frontier.
See [42_full_corpus_source_substitution_frontier_gate.md](42_full_corpus_source_substitution_frontier_gate.md).

### Full-Corpus Source Substitution Second-Pass Gate

The same single/pair frontier is rerun on the promoted source-substitution
formula. It still finds a positive pair, but only a microscopic one:
`8160.827092` to
`8160.826421` bits,
a gain of
`+0.000671` bits.
This updates the compression bound but does not strengthen the generation
explanation; triples and higher-order substitutions remain outside this gate.
See [43_full_corpus_source_substitution_second_pass_gate.md](43_full_corpus_source_substitution_second_pass_gate.md).

### Full-Corpus Source Substitution Third-Pass Gate

A third pass over the same single/pair frontier still finds a positive
pair, but the gain shrinks again:
`8160.826421` to
`8160.825917` bits,
a gain of
`+0.000503` bits.
This reinforces that the local source frontier is entering saturation;
it remains only a compression-bound update.
See [44_full_corpus_source_substitution_third_pass_gate.md](44_full_corpus_source_substitution_third_pass_gate.md).

### Full-Corpus Source Substitution Fourth-Pass Gate

A fourth pass over the same single/pair frontier still finds a positive
pair, but the gain shrinks again:
`8160.825917` to
`8160.825608` bits,
a gain of
`+0.000310` bits.
This is compression-bound bookkeeping and local source-frontier
saturation, not new generation evidence.
See [45_full_corpus_source_substitution_fourth_pass_gate.md](45_full_corpus_source_substitution_fourth_pass_gate.md).

### Source Substitution Saturation Audit

The source-substitution series is then converted into an explicit
stop-rule audit. The last three pass gains sum to only
`0.001484` bits,
and the last pass has positive pairs in only
`0.007287`
of searched pair candidates. A minimum pair-selector floor is
`16.092`
bits, dwarfing the latest unpriced gain. The local same-chunk source
frontier is therefore saturated as a mainline path; future progress
needs structure, holdout prediction, or row0-origin evidence.
See [46_source_substitution_saturation_audit.md](46_source_substitution_saturation_audit.md).

### Source Blocker Structural Context Gate

The remaining cross-op optional-literal near tie is then tested as a
source-cost blocker. The candidate is only `+0.027` bits worse than
active, and a source-free oracle would be `-11.209` bits better, but
that oracle is not decodable because it removes the required copy-source
choice. The best tested simple source context, `book_half`, is still
`+5.872` bits worse than the global source prior and loses in `5/5`
prefix-frozen splits. This localizes the next source frontier: a future
advance needs a new source derivation or representation, not a simple
declared context split.
See [24_source_blocker_structural_context_gate.md](24_source_blocker_structural_context_gate.md).

### Source Canonicality Decodability Gate

The strongest source-derivation clue is then separated from decoder
requirements. Every declared copy source is the earliest legal
occurrence of the copied chunk (`261/261`), but only `123/261` source
choices are unique at the declared length and `138/261` are ambiguous.
More importantly, the earliest-exact-chunk rule depends on the future
target chunk, which the decoder does not know until source and length
are resolved. Source canonicality is therefore retained as encoder
regularity, while the decodable default/exception source ledger remains
the valid source representation.
See [25_source_canonicality_decodability_gate.md](25_source_canonicality_decodability_gate.md).

### Source State Dependency Gate

A final source-state gate then checks whether the active previous-copy
source/length dependency can be removed by a decoder-computable
state-free default. It cannot under the tested rules. The exact active
reparse still needs state key
`(book_pos, previous_item, previous_copy_source, previous_copy_length)`,
and the best state-free rule, `state_free_back_current_length`, is
`+15.186` bits worse on the full source ledger. It also loses all
`5/5` prefix-frozen checks, with gap min/mean/max `7.652` /
`14.615` / `22.840` bits. This keeps source state as a real
generation-boundary dependency, not a removable tie-break.
See [26_source_state_dependency_gate.md](26_source_state_dependency_gate.md).

### Source Selection Derivation Boundary Gate

The source-selection boundary is then consolidated across canonicality,
negative controls, distance coding, and state-free defaults. All
`261/261` copy sources are earliest legal exact-chunk sources, while
latest source matches only `123/261`, previous source `0/261`, and
previous-source-plus-length `5/261`; random candidate choice expects
`169.473` hits. But the earliest rule depends on future target text,
so it is not decoder-computable. Backward-distance source coding is
`+25.551` bits worse and loses all prefix frozen and online splits,
and the best state-free default remains `+15.186` bits worse. Copy
source is therefore canonical but still declared.
See [31_source_selection_derivation_boundary_gate.md](31_source_selection_derivation_boundary_gate.md).

### Copy Length Midpoint Context Gate

The copy-length context is then checked as a positive generalization
case. The active natural midpoint split, `book_id < 35`, beats the
global copy-length context by `13.839` bits, ranks `2` among all
one-cut boundaries, wins all `5/5` prefix-frozen future-suffix checks,
and passes book-id permutation controls (`p=0.0033`). The best searched
cutoff, `37`, is only `0.256` bits better than midpoint, so it is not
promoted as a new boundary. This strengthens one learned mechanical
component while leaving the full recipe and row0 origin unchanged.
See [27_copy_length_midpoint_context_gate.md](27_copy_length_midpoint_context_gate.md).

### Copy Length Derivation Boundary Gate

The copy-length dependency is then separated into encoder-only and
decoder-valid pieces. The high-coverage target-max rule matches
`238/261` copy lengths, but it is not decodable because it needs
future target text. The retained decoder-valid model is
`decoder_max_possible` default plus adaptive exceptions: `60`
defaults and `201` exceptions, with `136.884` bits of upstream gain.
The midpoint context is supported, but the compact recipe still
declares `261` copy-length fields covering `10406` copied digits.
See [32_copy_length_derivation_boundary_gate.md](32_copy_length_derivation_boundary_gate.md).

### Literal Copy Availability Gate

The literal payload is then separated into forced literals and residual
parser choices. Most literal operations are forced by copy
unavailability: `73/87` literal starts and `760/857` literal digits
have no legal `min_len` copy candidate. The optional frontier is
localized to `14` starts and `97` digits. Simple in-literal copy
repairs score `74` candidates and remain at least `+1.180` bits worse;
cross-op repairs score `465` candidates and the best is still
`+0.027` bits worse. The near tie saves literal/item bits but pays
`+11.237` copy-source and `+1.639` copy-length bits, so literal
externality is reduced but not removed.
See [28_literal_copy_availability_gate.md](28_literal_copy_availability_gate.md).

### Literal Payload Model Gate

After forced literal availability is separated, the residual literal
payload model still cannot be simplified under the tested controls.
The current order-2 previous-emitted-digit categorical model costs
`2613.661` bits over `857` literal digits. Order-1 wins some
intermediate frozen splits, but is `+95.968` bits worse on the full
corpus, `+47.346` bits worse in aggregate online prefix totals, and
`+28.609` bits worse in aggregate frozen prefix totals. The best
modal default/exception candidate is `+38.049` bits worse, and the
best non-active structural context is `+19.159` bits worse. The
payload dependency is therefore retained, not removed.
See [29_literal_payload_model_gate.md](29_literal_payload_model_gate.md).

### Current Formula Dependency Scoreboard

The current formula dependency scoreboard then re-counts the latest
local-source-bound formula directly. It roundtrips `70/70` books with
`348` ops:
`87` literals and
`261` copies. It still
declares literal payload, copy source, and copy length. Copy-source
selection is encoder-canonical but decoder-declared; copy length is
partly decodable but still carries exceptions; literal payload is
mostly forced and downstream of source/length choices. The next
mainline mechanical test should therefore be a structural
decoder-known source/length parser or objective, not another local
same-chunk source edit.
See [48_current_formula_dependency_scoreboard.md](48_current_formula_dependency_scoreboard.md).

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
- Sources: [`occ_streams.json`](../../../audit_20260609/homophone_channel/occ_streams.json), [`books_digits.json`](../../../audit_20260609/books_digits.json)

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
See [05_row0_hypothesis_requirement_audit.md](05_row0_hypothesis_requirement_audit.md).

### Row0 Parallel Provenance Bridge

The independent row0-origin parallel front is then bridged back into
this audit. It traces local project provenance through workbook, import,
reconstruction, and audit layers, but still leaves CipSoft/authorial
origin untraced. Its paid-anchor gate confirms the boundary: all
worksheet anchors have a nominal
`54.178`
bit reduction, but after explicit pair+label costs they are
`-11.852`
bits versus lookup. Rare singleton anchors have nominal signal
`28.637`
bits but net to
`0.000`
after paying label data. Ordered-surface asymmetry remains a real
mechanical clue, not a label-origin formula.
See [47_row0_parallel_provenance_bridge_audit.md](47_row0_parallel_provenance_bridge_audit.md).

## Decision

- `8558.667` bits remains a frozen validation scope here, not a final authorial method.
- The learned component signal survives prefix and block holdout but fails some family holdouts, so it is not promoted beyond partial predictive structure.
- The full-corpus fixed-recipe limitation is partially reduced by deterministic reparse evidence; after same-coordinate address correction, public-bookcase family reparse beats or ties the active family recipe in `19/19` families, a no-test-carryover variant still beats raw in `19/19`, singleton leave-one-book-out reparsing beats raw in `70/70`, singleton copy sources are attributed, the signal survives book-bounded and same-family-excluded source constraints, the online previous-books-only frontier is positive after the bootstrap book, and a raw book-0 seed policy closes the remaining local failure but fails complete-formula promotion because literal-payload cost dominates and any exception signal would require negative cost.
- Source-state simplification is rejected: canonicality is encoder-side only, and state-free source defaults lose to the active previous-copy source/length default in the full ledger and every tested prefix-frozen split.
- Copy-source selection is encoder-canonical but not decoder-derived: earliest-source hits `261/261`, while distance and state-free replacements lose.
- Copy-length midpoint context is retained as a generalizing natural split; the searched cutoff `37` is rejected as ad-hoc for only `0.256` bits over midpoint.
- Copy length is partly remodeled but not derived: target-max is encoder-only, and the compact recipe still declares all `261` copy lengths.
- Literal externality is reduced but not removed: most literal payload is forced by copy unavailability, and the residual local repair families are worse under the active ledger.
- The literal payload model remains order-2 previous-emitted-digit context: order-1, modal default/exception coding, and simple structural contexts all fail as replacements.
- The current formula dependency scoreboard maps the retained declarations on the latest formula: `87` literal payload fields, `261` copy-source fields, and `261` copy-length fields; it prioritizes a structural source/length parser before more literal or item-type work.
- Recipe representation artifacts are removed without changing the score: book length, copy target start, literal length, and op type are derivable; literal text, copy source, and copy length remain declared.
- Item-type split-only remains a retained generation-profile stream, while compact recipe op `type` fields are derivable from operation shape.
- The current active `8177.317`-bit profile has positive frozen gain on every tested prefix, block, and public-bookcase family split, but recipe discovery remains blocked by path-dependent copy-source state.
- Copy-source state is compressed from previous `(source, length)` to `previous_copy_end`, preserving the active default/exception ledger and reducing the candidate-state proxy, but no active parser is promoted.
- After that compression, every tested book-level source-state proxy is below one million and the late-cutoff frontier is smaller, so a book-local active-source prototype is now plausible by proxy; the complete active parser is still unpromoted.
- Cutoff-60 deterministic reparse recipes can be repriced with the active `previous_copy_end` source ledger: `10/10` roundtrip, `10/10` raw wins, and `-10.241` aggregate bits versus uniform-address reparse, but only `4/10` books improve individually and no recipe is reoptimized.
- Multi-cutoff source-state repricing generalizes that aggregate signal across cutoffs `10/20/35/50/60`: `5/5` cutoffs improve versus uniform-address reparse, totaling `-112.968` bits, while still not reoptimizing recipes.
- Fixed-segmentation source-choice optimization finds `0/514` cheaper source substitutions, so the simple source-only improvement path is closed under the immediate `previous_copy_end` cost.
- Global fixed-segmentation source-path optimization improves the repriced ledger by `-42.359` bits, changing `10/514` sources with max DP state count `14`; segmentation and copy lengths remain fixed.
- Full-corpus fixed-recipe source-path optimization survives adaptive rescore and lowers the active bound from `8177.317` to `8162.412` bits by changing `2/261` source positions; segmentation and copy lengths remain fixed.
- Full-corpus single/pair source-substitution frontier search lowers the active bound from `8162.412` to `8160.827` bits; triples and higher-order substitutions remain unsearched.
- A second single/pair source-substitution pass finds only a microscopic `+0.000671` bit gain, lowering the active bound to `8160.826421`; this is a compression-bound update, not stronger generation evidence.
- A third single/pair source-substitution pass finds another microscopic `+0.000503` bit gain, lowering the active bound to `8160.825917`; local source substitutions are saturating.
- A fourth single/pair source-substitution pass finds another microscopic `+0.000310` bit gain, lowering the active bound to `8160.825608`; local source substitutions are saturating.
- The source-substitution saturation audit freezes repeated same-chunk local source edits as no longer mainline: the last three gains sum to `0.001484` bits and are dwarfed by selector-cost sanity checks.
- All requested row0-origin hypothesis families have been checklist-audited; none passes as an origin formula.
- The row0 parallel provenance bridge traces workbook/import/reconstruction/audit layers but leaves CipSoft origin untraced; paid worksheet anchors do not beat lookup once pair and label costs are charged.
- `row0` continues exogenous: the active book generator assumes the table rather than deriving it.
- No translation, plaintext, or case reopening is introduced.
