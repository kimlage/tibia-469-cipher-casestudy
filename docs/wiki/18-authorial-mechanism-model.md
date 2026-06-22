---
page_id: authorial-mechanism-model
page_type: finding
context: bonelord-469
visibility: public_candidate
status: frozen
updated_at: 2026-06-22
moc_parent: README.md
source_refs:
  - analysis/authorial_mechanism_20260620
  - analysis/prequential_and_row0_origin_audit_20260621
  - analysis/authorial_provenance_audit_20260621
  - analysis/segmentation_decision_audit_20260621
  - analysis/target_digit_boundary_threshold_audit_20260621
  - analysis/target_digit_boundary_peak_audit_20260621
  - analysis/target_digit_boundary_island_audit_20260621
  - analysis/target_digit_boundary_miss_residual_audit_20260621
  - analysis/target_digit_boundary_miss_transition_audit_20260621
  - analysis/skeleton_generation_route_review_20260622
  - analysis/joint_target_stream_parser_audit_20260622
  - analysis/composition_index_structure_audit_20260622
  - analysis/minimal_external_tape_program_audit_20260622
  - analysis/source_tape_removal_program_audit_20260622
  - analysis/book_level_controller_program_integration_audit_20260622
  - analysis/executable_program_frontier_synthesis_audit_20260622
  - analysis/joint_chunk_origin_route_audit_20260622
  - analysis/joint_chunk_origin_beam_pilot_audit_20260622
  - analysis/chunk_length_prior_integration_audit_20260622
  - analysis/markov_chunk_content_prior_audit_20260622
  - analysis/latent_state_route_synthesis_audit_20260622
  - analysis/latent_nonlocal_state_program_pilot_audit_20260622
  - analysis/schedule_state_multistream_pilot_audit_20260622
  - analysis/book_multiset_order_factorization_audit_20260622
  - analysis/within_book_order_program_audit_20260622
  - analysis/sequence_mutation_program_audit_20260622
  - analysis/generative_route_frontier_synthesis_audit_20260622
  - analysis/digit_content_boundary_transducer_audit_20260622
  - analysis/physical_topology_control_signal_audit_20260622
  - analysis/book_residual_mode_coupling_audit_20260622
  - analysis/latent_book_mode_program_audit_20260622
  - analysis/residual_mode_header_codec_audit_20260622
  - analysis/residual_burden_cross_prediction_audit_20260622
  - analysis/paid_control_context_payload_codec_audit_20260622
  - analysis/parser_decoder_frontier_synthesis_audit_20260622
  - analysis/target_free_internal_start_program_audit_20260622
  - analysis/internal_start_beam_capacity_audit_20260622
  - analysis/internal_start_beam_control_audit_20260622
  - analysis/internal_start_beam_paid_control_audit_20260622
  - analysis/online_x64_coarse_control_program_audit_20260622
  - analysis/executable_v2_residual_coupling_audit_20260622
  - analysis/executable_v2_remaining_tape_coupling_audit_20260622
  - analysis/content_addressed_event_program_audit_20260622
  - analysis/event_aligned_chunk_library_audit_20260622
  - analysis/source_boundary_candidate_program_audit_20260622
  - analysis/executable_v3_source_boundary_program_audit_20260622
  - analysis/executable_v3_source_boundary_robustness_audit_20260622
  - analysis/boundary_mark_propagation_program_audit_20260622
  - analysis/one_sided_source_boundary_program_audit_20260622
  - analysis/executable_v4_one_sided_boundary_program_audit_20260622
  - analysis/executable_v5_source_endpoint_memory_audit_20260622
  - analysis/v5_external_dependency_frontier_synthesis_audit_20260622
  - analysis/joint_content_origin_program_audit_20260622
  - analysis/executable_v6_literal_span_origin_audit_20260622
  - analysis/causal_event_graph_program_audit_20260622
  - analysis/innovation_lineage_basis_audit_20260622
  - analysis/lineage_signature_library_audit_20260622
  - analysis/residual_content_basis_program_audit_20260622
  - analysis/residual_content_fingerprint_program_audit_20260622
  - analysis/seed_bootstrap_copy_surface_audit_20260622
  - analysis/seed_bootstrap_transducer_program_audit_20260622
  - analysis/seed_bootstrap_decision_policy_audit_20260622
---

# 18. Authorial Mechanism Model

[<- Physical Library Topology](17-physical-library-topology.md) . [Wiki home](README.md)

---

## Verdict

The first-principles/Knightmare report is incorporated as a mechanism-search
prior, not as proof of private authorial intent. Its useful conclusion is that
the best working model remains:

```text
limited phrase-code layer
+ mechanically fabricated book layer
+ lore/math atmosphere
```

Translation delta: `NONE`.

Round result: `MECHANICAL IMPROVEMENT / semantic plateau unchanged`.

## What Changed Mechanically

The new search found a small but real improvement to the current tape formula.
Remaining literal strings in the tape recipe were checked against existing tape
components. When a literal could be replaced by a cheaper
`component_id/start/length` reference, the compiler emitted a new recipe item.

Result:

| Metric | Value |
|---|---:|
| New book-recipe formula | `literal_reference_formula_469.json` |
| New hierarchical formula | `hierarchical_reference_formula_469.json` |
| Reference items | `36` |
| Referenced literal digits | `579` |
| Kept literal items | `67` |
| Kept literal digits | `1397` |
| Rough saved bits | `1167.4` |
| Book roundtrip | `70/70` |
| Controlled benchmark verdict | `controlled_mechanical_improvement_no_semantics` |

This improves the mechanical generation method. It does not explain the
10x10 pair-table origin and does not translate the books.

The follow-up benchmark compares the cost ladder directly:

| Model | Rough total bits | Gain vs previous |
|---|---:|---:|
| `mechanical_formula_469` | `24350.7` | `0.0` |
| `tape_based_formula_469` | `17753.5` | `6597.1` |
| `literal_reference_formula_469` | `16586.1` | `1167.4` |
| `hierarchical_reference_formula_469` | `13858.5` | `2727.7` |
| `sequential_lz_book_formula_469` | `10190.0` | `3668.5` |
| `sequential_lz_run_literal_formula_469` | `9944.0` | `246.0` |
| `sequential_lz_dp_parse_formula_469` | `9823.3` | `120.7` |
| `sequential_lz_rice_length_formula_469` | `9596.5` | `226.8` |
| `sequential_lz_rice_literal_length_formula_469` | `9545.5` | `51.0` |
| `sequential_lz_literal_payload_formula_469` | `9538.0` | `7.5` |
| `sequential_lz_literal_copy_repair_formula_469` | `9537.3` | `0.7` |
| `sequential_lz_length_ledger_formula_469` | `9073.3` | `464.0` |
| `sequential_lz_digit_address_formula_469` | `9070.8` | `2.4` |
| `sequential_lz_digit_address_literal_repair_formula_469` | `9070.1` | `0.8` |
| `sequential_lz_digit_address_type_coded_formula_469` | `8996.2` | `73.8` |
| `sequential_lz_digit_address_markov_type_formula_469` | `8977.6` | `18.6` |
| `sequential_lz_digit_address_book_start_type_formula_469` | `8972.2` | `5.3` |
| `sequential_lz_digit_address_literal_force_type_formula_469` | `8966.7` | `5.5` |
| `sequential_lz_digit_address_remaining_force_type_formula_469` | `8953.9` | `12.8` |
| `sequential_lz_digit_address_forced_literal_length_formula_469` | `8922.9` | `31.0` |
| `sequential_lz_digit_address_forced_length_literal_repair_formula_469` | `8922.8` | `0.1` |
| `sequential_lz_digit_address_forced_length_literal_context_formula_469` | `8842.0` | `80.8` |
| `sequential_lz_digit_address_forced_length_literal_context_order_formula_469` | `8805.7` | `36.3` |
| `sequential_lz_digit_address_forced_length_literal_context_order_type_context_formula_469` | `8803.5` | `2.2` |
| `sequential_lz_digit_address_contextual_copy_to_literal_formula_469` | `8803.1` | `0.4` |
| `sequential_lz_digit_address_contextual_bounded_copy_length_formula_469` | `8614.1` | `189.0` |
| `sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_formula_469` | `8613.1` | `1.1` |
| `sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair_formula_469` | `8611.4` | `1.7` |
| `sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_formula_469` | `8609.8` | `1.6` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_formula_469` | `8576.0` | `33.8` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_minaddr_repair2_formula_469` | `8574.4` | `1.6` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_formula_469` | `8572.3` | `2.1` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_minaddr_repair2_formula_469` | `8569.7` | `2.6` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_formula_469` | `8561.8` | `7.9` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_param_minaddr_repair2_formula_469` | `8558.7` | `3.1` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_formula_469` | `8343.1` | `215.6` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_default_exception_formula_469` | `8206.2` | `136.9` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469` | `8177.3` | `28.9` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_path_optimized_formula_469` | `8162.4` | `14.9` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_frontier_formula_469` | `8160.8` | `1.6` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_second_pass_formula_469` | `8160.826` | `0.001` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_third_pass_formula_469` | `8160.8259` | `0.0005` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469` | `8160.8256` | `0.0003` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_formula_469` | `8158.7661` | `2.0595` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_second_pass_formula_469` | `8157.0657` | `1.7004` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_saturated_formula_469` | `8156.0504` | `1.0153` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_formula_469` | `8156.0502` | `0.0002` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_formula_469` | `8156.0500` | `0.0002` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_formula_469` | `8155.2610` | `0.7889` |
| `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_second_pass_formula_469` | `8154.6763` | `0.5848` |

The `8154.6763` row is the current `compression_bound`, not a final authorial
method. From this point, mainline progress requires holdout behavior,
structural mechanism, simplification, or row0/table-origin evidence rather than
more small post-hoc component sweeps.

A row0 compatibility audit checked the later partial-boundary promotions
against the independent row0 front. They remain compatible but do not move
row0: no recent formula gate predicts row0 labels under holdout, beats lookup
after paid anchor/rule costs, explains `39`/`93`/`19/91`, or adds
CipSoft/authorial provenance. The result is `row0 unchanged`.

The Chayenne provenance audit adds one narrow public-surface clue, not a new
generator. In the PortalTibia interview, the numeric answer appears as two
blocks separated by a visible marker; concatenating them yields no corpus hit,
while the published split at boundary `36` is the unique full split whose two
sides are both attested book substrings. Shuffle controls find no comparable
block/join or full-split hits. This supports reuse of existing 469 numeric
modules in that public answer, but it does not derive row0, choose parser
`(source,length)` fields, change `compression_bound`, or create plaintext.

The final dependency refresh adds the mechanical boundary for the current
formula: the `8154.6763`-bit bound still retains `609` operation dependency
fields, with source/length derivation unchanged at declared-source+decoder-max
`60/261`, unique-source+decoder-max `28/261`, and previous-end+decoder-max
`1/261`. The next real formula work remains source/length parser derivation,
not another local boundary-shift pass.

The follow-up parser feasibility audit makes that next step concrete. On the
final formula, previous-end state compression keeps every tested book-level
end-state proxy below `1,000,000`, but the copy-transition proxy is still
`1,966,897,365` total transitions (`23045.1x` the old frozen-count DP).
The parser should therefore be built as a pruned/cached per-book source+length
DP, starting with the hard books `53`, `51`, `35`, and `58`.

The first book-local probe confirms that this parser path is executable, not
just theoretical: cutoff-60 books `67` and `60` both roundtrip under the active
source/length DP and beat raw digit coding. The result does not promote a new
bound because it ties the same-policy reprice comparator, and book `66` remains
the immediate hard case by transition proxy.

The sparse hard-book gate removes that immediate implementation blocker. Using
Dijkstra over reachable `(position, previous_item, previous_copy_end)` states
instead of dense dynamic programming, book `66` roundtrips in `0.033s` with
`41,832` transition evaluations instead of the `26,096,904` transition proxy.
This moves the source/length parser toward a real generator, but still does not
promote a corpus-wide parser or a new compression bound.

The post-parser row0 compatibility audit checks the dependency refresh,
parser-feasibility audit, two-book parser probe, and sparse hard-book gate
against the independent row0 provenance front. None of those advances predicts
row0 labels under holdout, beats paid lookup, explains `39`/`93`/`19/91`
beyond the existing surface clue, or adds CipSoft/authorial provenance. The
row0 conclusion is therefore unchanged: parser progress belongs to the book
formula, not to the origin of the 10x10 table.

The cutoff-60 sparse suffix parser gate then carries that parser through the
entire held-out suffix. Books `60..69` roundtrip in sequence with
`previous_copy_end` carried between books; all `10/10` beat raw digit uniform,
the parser totals `368.531807` bits, and it ties the same-policy reprice across
all books with `383,548` transition evaluations. This is stronger evidence
that the source/length parser is executable as a mechanism, but it is still a
single-cutoff suffix gate with frozen train counts, so it does not promote a
new compression bound or final authorial method.

The multi-cutoff validation repeats the sparse suffix parse at cutoffs
`10/20/35/50/60`, freezing train counts at each prefix. All `175/175` suffix
book evaluations roundtrip and beat raw digit uniform; against the same-policy
reprice, the parser is better/tie/worse in `12/163/0` cells and improves the
overlapping validation total by `12.180052` bits. This is the strongest parser
execution evidence so far because it survives several train/test boundaries,
but it remains validation evidence rather than a new corpus bound: the rows
overlap and do not constitute one charged 70-book recipe.

The path-stability audit adds the missing caution. Replaying the same `175`
evaluations with exact operation signatures shows that `38/50` books observed
under multiple cutoffs keep a single exact parser path, while `12/50` change
path as the frozen prefix changes; book `65` is the worst case with `4`
distinct signatures. This supports the parser as a reusable mechanism, but it
also localizes the remaining non-authorial-looking dependency: some paths are
still controlled by learned stream weights and tie-breaking rather than a
prefix-invariant recipe.

The unstable-path decomposition then identifies what kind of instability
remains. Of the `12` prefix-sensitive books, `9` are same-shape boundary shifts
and `3` are larger segmentation-shape changes; `0` are pure source-address
swaps. The next structural mechanism question is therefore not which source
address model to try, but how copy boundaries are selected and stabilized,
with book `65` as the clearest stress case.

A boundary-policy stability gate then tests the cheap version of that
hypothesis. Fixed invariant policies such as front-loaded copy lengths,
back-loaded copy lengths, earliest/latest sources, source-default preference,
and literal/copy mass are repriced over the `12` unstable books and `37` cutoff
observations. The best structural policy reaches only `16/37` exact matches
with `8.984788` regret bits, and even an audit-only oracle that chooses the
lowest average repriced observed variant reaches only `18/37`. Simple boundary
rules are therefore rejected; boundary selection remains an exogenous parser
cost choice rather than a closed authorial mechanism.

The follow-up cost decomposition localizes that exogenous choice. Across `47`
losing observed variants compared against their per-cutoff parser winners,
the dominant positive component is `copy_length` in `30` comparisons,
`copy_source_exception` in `12`, `literal_payload` in `4`, and
`copy_source_flag` in `1`. This makes the next parser question narrower:
stabilize learned copy-length and source-exception choices under frozen
prefixes, with literal-payload pressure mostly confined to the larger
segmentation-shape changes.

A component-neutralized stability gate tests the natural simplification: replace
the learned copy-length and source-exception priors with uniform decodable
costs and rerun the same multi-cutoff parser. Exact path stability improves
from `38/50` to `48/50`, and all `175/175` suffix evaluations still roundtrip
and beat raw digit-uniform cost. The tradeoff is explicit: the mode costs
`+67.605622` parser bits versus active learned scoring and still leaves books
`26` and `34` unstable. This is therefore a structural simplification candidate
for the generator explanation, not a compression-bound promotion.

The residual tradeoff audit clarifies the candidate boundary. The best
neutralized mode resolves `11` of the `12` active learned-path instabilities,
but it does not simply dominate the active parser: book `34` remains unstable
and book `26` becomes newly unstable. Uniformizing the entire source model
changes the residual pair to books `35` and `45`, but costs an additional
`367.448154` parser bits over the best neutralized mode. The source flag is
therefore not promoted; the remaining structural question is a narrow residual
mechanism for books `26` and `34`.

A residual literal-payload neutralization gate then tests that narrow question.
Adding uniform digit payload cost on top of the uniform copy-length and
source-exception parser resolves both books `26` and `34`, improves exact
multi-cutoff path stability to `49/50`, and preserves `175/175`
roundtrip/raw-positive evaluations. It also pays `+170.606311` parser bits over
the previous neutralized mode and introduces book `49` as the sole residual.
So the residual frontier moves from `26`/`34` to `49`; it does not disappear.

The book `49` residual split audit localizes the remaining instability. Under
the payload-neutralized scorer, cutoffs `10` and `20` split the initial literal
area into `literal 11 + copy 7 + literal 7`, while cutoff `35` keeps it as one
`25`-digit literal. Local controls show that removing either the `literal_length`
charge or the `item_type` charge makes the split-prefix variant win in all
three cutoffs. This explains the residual as a prefix split/coalescence
decision, but it is not yet a corpus-wide generator rule.

A global item/literal-length control gate then tests those local controls across
the full multi-cutoff parser set. Removing `item_type` charge closes exact path
stability at `50/50`; removing both `item_type` and `literal_length` also reaches
`50/50` and gives the best parser-bit delta (`-770.657134` versus the
payload-uniform baseline), while preserving `175/175` roundtrip/raw-positive
evaluations. This is a parser-stability simplification: it does not change the
`8154.676268` compression bound, explain `row0`, or add plaintext evidence.

A stable path projection boundary audit then blocks the strongest possible
overclaim. The best stable no-item/no-literal-length mode covers `11263/11263`
digits after treating books `0..9` as seed material, with `208` canonical copy
items, `54` literal runs, and `265` parsed literal digits; this reduces
materialized operation dependency fields by `139` versus the active formula. But
the projection is still chosen with the target book text available: copy
candidates, literal payload, and literal endpoints are target-dependent. So this
is an encoder-side stable projection, not a promoted decoder-side generator.

A decoder-side rule coverage audit then tests the obvious promotion path. Simple
rules fail to explain the stable projection: the best decoder-side source rule
is `source_is_previous_copy_end` at `6/208`, the best length rule is
`length_is_decoder_max` at `58/208`, and the best joint rule reaches only
`2/208`. The decoder-max length signal is nonrandom against shuffled lengths
(`p=0.0000`), but `265` literal payload digits are still materialized and source
choice remains almost entirely target-dependent. The result is
`decoder_side_rule_coverage_insufficient`.

A source tie-break artifact audit then tests the strongest skeptical reading of
the `208/208` earliest-target-match source signal. It reruns the stable
projection under `earliest_source`, `latest_source`, and
`prefer_previous_end_then_earliest` tie policies. All three keep the same primary
cost (`11459.765681`) and `50/50` path stability, but the selected source sums do
not move (`source_sum_span=0`). So the signal is not explained as a simple parser
tie-break artifact. It remains target-dependent, however, because
earliest-target-match cannot be chosen without the target chunk.

That reading is then corrected by a source candidate collapse audit.
`precompute_matches` does not expose all same-length sources to the parser: it
stores one source per length and chooses the lower `source_pos`. As a result, the
heap in gate 89 could not switch to later same-length matches. The `208/208`
earliest-target-match count is therefore induced by candidate generation, not
independent source evidence. In the stable projection, `130/208` copy events have
hidden alternate sources, with up to `13` hidden alternatives for a single event.

A full source exposure audit then tests the corrected frontier on the cutoff-60
slice. Exposing every same-length source candidate preserves roundtrip and
stability for all three tie policies over the `10` target books. The
`latest_source` policy selects `10` non-earliest sources and costs only
`+0.017676` primary bits versus the collapsed frontier; the earliest and
previous-end-preferred policies match collapsed cost exactly. This is local
parser robustness, not a source-generation rule, because the exposed candidates
are still target-chunk matches.

A full-source latest multi-cutoff probe then expands the same correction to
cutoffs `50` and `60` for the most disruptive tie policy. It roundtrips and beats
raw in `30/30` book evaluations, and books `60..69` remain exact-path stable
across both cutoffs (`10/10`). The parser selects `35` non-earliest sources while
exposing `1246561` hidden candidates. This is stronger partial stability evidence
for the parser, but still not a formula promotion: source candidates remain
target-chunk matches.
A full-source all-policy multi-cutoff probe then checks whether that partial
stability depends on the `latest_source` policy. It does not at cutoffs `50/60`:
`earliest_source`, `latest_source`, and `prefer_previous_end_then_earliest` each
roundtrip and beat raw in `30/30` book evaluations, and each keeps books `60..69`
stable across both cutoffs (`10/10`). This is still an exposed-source parser
robustness result, not a source-generation rule; `row0` and the `8154.676268`-bit
bound remain unchanged.
A full-source all-policy five-cutoff probe then closes the open cutoff-grid
question. Across cutoffs `10/20/35/50/60`, all three tie policies roundtrip and
beat raw in `175/175` book evaluations per policy, each has `50/50`
multi-cutoff-stable books, and the aggregate unstable policy-book count is
`0/150`. This materially strengthens parser robustness under source-candidate
exposure, but still does not derive source choice during decoding or alter row0.
A source-policy invariance boundary then tests the stronger claim that all-policy
stability might demote source choice itself. It does not. Across `175`
`(cutoff, book)` cases, operation shape is invariant in `175/175`, but exact
source-bearing signatures are invariant in only `48/175`; the other `127/175`
are pure source-choice variants. The parser shape is robust, while source choice
remains a retained declared dependency.
A canonical source-policy boundary then tests whether the remaining tie-policy
choice can at least be frozen globally. It cannot without a cost or selector:
`earliest_source` and `prefer_previous_end_then_earliest` are min-cost in
`170/175` cases, but `latest_source` is cheaper in five book-`63` cases; no
static policy has zero extra bits versus the per-case minimum. This rejects
static tie-policy promotion and keeps source choice declared.
A source-policy selector boundary then tests the obvious workaround: use
`latest_source` only for book `63` and `earliest_source` otherwise. The selector
matches the per-case policy minimum and has a positive lower-bound balance after
charging a simple book+policy selector floor, but it is still a book-specific
switch over a source-dependent parser. It is therefore audit-only compression
bookkeeping, not a generation explanation.
An exact source-free skeleton invariance audit then extracts the part that does
survive. Removing source addresses and source-default flags leaves operation
type, target start, length, and forced flag invariant across `175/175`
policy-cutoff cases and `60/60` books. The canonical exposed-source skeleton has
`261` ops, `208` copy items, `53` literal runs, `266` literal digits, and `9301`
copied digits. This is real segmentation evidence, but still only an atlas:
literal payload and copy-source choices remain external to the decoder.
An exact skeleton dependency ledger then makes that boundary quantitative.
Compared with `609` active external dependency fields, the skeleton atlas leaves
`208` copy-source fields and `53` literal payload chunks external (`261` fields),
while the atlas itself has `261` stable operation skeleton records. Total
materialized atlas+external records are therefore `522`: a real dependency-ledger
improvement, but not a compression-bound change or generator promotion.
A skeleton decoder ambiguity audit then prices the same boundary from the
decoder side. Even after granting the exact skeleton, legal copy-source
branching contributes `2550.594` bits and literal payload contributes
`883.633` bits, leaving a combined lower-bound ambiguity of `3434.227` bits
(`10^1033.805` choices). The target-oracle matching-source residual is only
diagnostic because it grants the future copied chunk.
A generation boundary closure audit then consolidates the current post-gate
state across book order, book lengths, operation skeleton, copy sources, and
literal payload. No dependency has a promoted generator (`0/5`), and the
materialized-unit floor is `593`: `1` order, `70` lengths, `261` skeleton
records, `208` source fields, and `53` literal chunks. This is the cleanest
current summary of the boundary: robust parser/atlas, not source-free generator.
An operation count generation audit then tests the first skeleton field before
cutpoints are chosen. The best source-free model,
`context_book_mod10_x_length_bucket`, hits `40/60` books and gives a small
audit-only full-fit reduction from `60` exact op-count records to `55` paid
records. It is not promoted: it still misses `20` books and has `0/5`
prefix/holdout cells that cover all books or beat random p95.
An operation shape-count generation audit then broadens that test to
`(op_count, literal_count)`. The same context is again best but weaker:
`37/60` exact shapes, `58` paid records versus a `60`-record exact shape atlas,
`23` missed books, and `0/5` prefix/holdout cells that cover all books or beat
random p95. Coarse operation shape remains retained.
An operation type-sequence generation audit then grants those counts and tests
the literal/copy order directly. A paid template map,
`template_book_mod5_x_shape`, can reproduce `60/60` books and `261/261` type
positions full-fit, but it carries `235` template records, is only `-26` versus
the exact type-field atlas, and has `0/5` prefix/holdout cells beating random
p95. This is posthoc materialization, not a generator.
A type-weighted operation-length audit then grants book length and the full
literal/copy sequence. Simple source-free weighted allocation still fails:
the best `learned_by_shape_x_type_x_position` model reaches only `14/60`
exact books and `74/261` row hits, costs `363` paid records versus `261`
exact length fields, and has `0/5` cover-all holdout cells. The length
sequence remains a retained dependency for the joint parser.
An operation-length Markov audit then tests the skeleton blocker directly under
generous assumptions: book lengths and operation types are granted, and only the
`261` operation lengths must be generated. The best of `11` Markov/context
families (`op_index_x_type`) produces only `9/60` exact books, `43/261`
generated row hits, and `52/261` rowwise hits, with `0/5` cover-all holdout
cells. The operation-length atlas remains retained.
An operation-length motif audit then tests a non-Markov structural alternative:
reusable sub-book length motifs. This also fails as a generator. The best
full-fit library has only `2` motifs, saves `2` records, and still leaves
`249` residual singleton lengths; prefix/holdout motif libraries cover `0`
future books without residuals. The motif family is therefore not promoted.
An operation cutpoint scaling audit then tests whether normalized operation
cutpoints, scaled to each granted book length, replace the length atlas. They
do not. The best full-fit `book_mod10_x_op_count` family reaches `42/60`
exact books and `206/261` row hits, but carries `45` templates plus `181`
payload records, is `+35` records worse than the exact atlas, and has `0/5`
cover-all holdout cells. The proportional-cutpoint signal is descriptive, not
a generator.
An operation cutpoint lattice audit then removes the learned-template part and
tests a stricter source-free hypothesis: the `201` internal boundaries should
fall on small proportional grids after granting book length and op count. They
do not. The best denominator, `128`, reaches `41/60` exact books and `159/201`
hits, below the same-shape random-control mean `161.357`, and prefix-selected
denominators beat held-out random p95 in `0/5` cells.
An operation recursive partition audit then tests a different source-free
geometry: recursively splitting the book interval by bisection, thirds,
fourths, fifths, or golden-ratio cuts. It also fails. The best policy,
`latest:half`, reaches only `2/48` exact nontrivial books and `11/201`
cutpoint hits, below random p95 `14`, with `0/5` holdout cells beating random
p95.
A book order generation audit then consolidates the scattered order controls
against the current boundary. Numeric order remains the compact canonical order
used by the formula: full-formula and descriptor-cost gates promote no
non-numeric order, and online reparse random controls never beat numeric. But
numeric order is not derived: prequential prefix evidence has `0` order-specific
cutoffs and the online frontier criterion is shared by `10` tested orders,
including `6` random orders. Book order stays canonical, not generated.
A book length generation audit then closes a dependency that the skeleton gates
had been granting. The prior signed-Rice length ledger is reproduced as
`1030 -> 566` bits (`anchor=151`, `k=5`), but that is residual compression, not
length generation. Simple source-free policies reach only `14/70` exact lengths
at best; exact `70/70` requires a book-index lookup with `70` length payloads,
and prefix/holdout has `0/6` cover-all cells. Book length remains declared.
A source-free skeleton grammar audit then tests the direct next step: derive the
`261`-operation atlas from grammar contexts over operation index, prior
operation, book length, remaining length, phase, and book-mod/order features.
It rejects that path: the best full-fit context gets only `3/60` exact books
and `14/261` operation hits, costs `+660.028` bits versus a label-atlas lower
bound after corrections, and has `0/5` cover-all holdout cells.
A literal payload generation audit then tests the next dependency after granting
that exact skeleton. The remaining `53` literal chunks / `266` literal digits
do not follow from simple source-free contexts: the best full-fit context
matches `39/53` chunks but carries `222` payload digits in its table, costs
`+44.588` bits versus raw uniform literal payload after paid corrections, and
has `0/5` prefix/holdout cells with any exact chunk. The payload remains
external rather than generated.
A literal payload reference subcodec audit then tests a narrower constructive
possibility: replace already-seen whole chunks with declared prior references.
The recurrence is genuine (`38` chunks / `103` digits occurred before), and
`11` chunks / `48` digits save `30.001` bits before mode cost. Once mode and
source costs are paid, the subcodec is `+22.999` bits worse than raw payload,
so prior occurrence remains a clue rather than a promoted payload mechanism.
A copy-source generation audit then tests the other residual external field
after granting exact skeleton and literal payload. The ledger has `208` copy
events, with the canonical source equal to earliest matching in `200/208`, but
that signal is target-aware because it requires knowing the copied chunk. The
best decoder-visible policy reaches only `8/208` chunk hits and `1/60` exact
books; the best source-bearing context reaches `173/208` full-fit hits but is
`+199.919` bits worse than raw source declaration and has `0/5` cover-all
holdout cells. Copy source remains declared.
A target-conditioned source-collapse audit then asks whether source choice is
really primary once the copied chunk is known. Under that granted target-stream
condition, `200/208` copies choose the earliest matching source and the
remaining `8` exceptions cost only `58.085` bits, `-174.817` versus oracle
rank bits, with random rank controls never reaching the observed earliest-hit
count. This promotes a target-conditioned mechanical clue, but not a decoder
generator: the missing condition is still generation of the target chunk.
A target-chunk dictionary audit then tests the most direct target-stream
account: exact operation chunks as a reusable library. It fails sharply.
Overall `256/261` chunks are unique and copy chunks are `207/208` unique; an
all-chunk dictionary is `+32442.167` bits worse than the target-conditioned
baseline. The target stream therefore needs a richer latent/state mechanism,
not a literal dictionary of copied chunks.
A target-chunk signature audit then tests the next shallow abstraction:
coarse signatures instead of exact chunks. It also fails as a generator.
The best non-payload family (`kind_x_book_mod10_x_length_bucket`) has `85`
signatures and `495.649` exact-selector bits, but only because it leaves the
target digits unresolved. Payload-derived signatures become nearly exact
(`251/261` singleton rows under first2/last2), and same-length random controls
show that this specificity is ordinary payload leakage rather than a
source-free target-stream rule.
A target digit process audit then tests the broader source-free digit-stream
question directly. This produces a real but narrow clue: a second-order digit
process (`prev2_digits`) is strongly predictive in prefix/suffix validation
over both all `11263` book digits and the `9567` derived-book target digits.
It reaches `2.068621` bits/digit on all70 and `2.108869` bits/digit on
derived60, beating same-book-histogram shuffled controls in both scopes.
This is not promoted as a generator: it still requires residual arithmetic
bits to emit the exact books and says nothing by itself about operation
chunk endpoints.
A target digit boundary audit then connects that clue to segmentation rather
than only payload coding. Training `prev2_digits` on prior books, internal
operation cutpoints have mean right-surprisal `3.808645`, far above random
same-book cutpoint p95 `2.293949`; `88/201` cutpoints fall in their book's top
right-surprisal decile. This is promoted as a boundary clue. It is not an
endpoint generator: selecting each book's top-k surprisal positions recovers
only `57/201` internal cutpoints and `0/48` nontrivial books exactly.
A target digit boundary pruning audit then prices the same clue as a dependency
reduction rather than only an enrichment statistic. Taking the top `0.1`
right-surprisal band per book covers `86/201` internal cutpoints and reduces
the paid cutpoint atlas from `1137.308` bits to `1031.362` bits after charging
the q choice, a `105.946` bit reduction. Random same-size candidate bands have
p95 saving `-37.498` bits. Prefix-selected suffix checks stay positive in
`5/5` cells before the global q-choice charge and `4/5` after it. This promotes
a boundary-pruning clue, not an endpoint generator, because `115` cutpoints
remain outside the band and still need declarations.
A target digit boundary rank-code audit then tests whether the full rank
distribution strengthens the same clue. In full fit, `top5_10_20_50` rank bins
save `118.400` bits after scheme charge and beat random p95. It is not
promoted, because prefix-selected suffix validation is positive in only `4/5`
cells. This records a useful promotion boundary: rank bins are a stronger
descriptive full-fit code, but the promoted result remains the simpler
boundary-pruning clue.
A target digit boundary type audit then checks whether this same signal also
explains operation type after a cutpoint. It does not. The copy-majority
baseline is `161/201`, while the best surprisal/rank predicate reaches only
`131/201`; prefix/suffix context tables have `0/20` positive-delta cells.
The `prev2` boundary clue is therefore scoped to endpoint candidate pruning,
not copy/literal type selection.
A skeleton dependency refresh then charges the number of cutpoints per book
explicitly. Op-count declaration costs `432.765` bits under a uniform
book-length code. The exact full cutpoint atlas is therefore `1570.073` bits,
and the pruned full atlas is `1464.127` bits. The promoted dependency
reduction remains `105.946` bits, but the result is still not a skeleton
generator: op-counts, `115` missed cutpoints, and copy/literal type remain
external.
A stricter target digit boundary threshold audit then removes the op-count
grant from the predictor itself. The best global threshold, `right_ge:4`,
predicts `935` candidate boundaries, hits `94/201` true cutpoints, and reduces
the `1570.073`-bit full cutpoint atlas to `924.379` correction bits after
policy charge, a `645.694`-bit dependency reduction. It also beats random p95
and stays positive in `5/5` prefix-selected suffix cells. This still is not a
generator: precision is only `0.100535`, the code pays `948` FP/FN corrections,
and exact books remain `0/60`.
A target digit boundary peak audit then asks whether the broad high-surprisal
regions should be sharpened to local peaks or non-maximum-suppressed rank
peaks. The best policy, `nms_rank:top=0.05:gap=3`, is diagnostically cleaner:
it reduces predicted boundaries from `935` to `417` and correction events from
`948` to `504`. It is still not a better code or a generator. It saves
`615.947` bits after policy charge, `29.746` bits worse than the threshold
gate, and does so by adding `37` missed true cutpoints; exact books remain
`0/60`.
A target digit boundary island audit then tests a more regional interpretation:
describe contiguous high-surprisal islands and offsets inside them. This keeps
the best policy at `right_ge:4`; the occupied islands are clean singletons
(`94` occupied, `0` multi-hit), so the diagnostic is real. The code is still
worse: island correction costs `941.005` bits after policy charge, `16.625`
bits more than the flat threshold candidate-set code, and prefix-selected
island coding beats same-policy threshold coding in only `2/5` cells.
A target digit boundary miss-residual audit then asks whether the `107`
cutpoints outside `right_ge:4` have a second-stage rule. Full fit is promising:
the best residual policy, `near_primary:1`, improves the paid ledger by
`69.462` bits over the threshold gate and beats random p95. It is not promoted,
because the policy selects `1452` residual candidates for only `38` true missed
cutpoints, precision is `0.026171`, exact outside books remain `0/60`, and
prefix-selected validation is positive in only `4/5` cells.
A target digit boundary miss-transition audit then takes a step back and asks
whether those misses are simply a skeleton-transition or chunk-recurrence
class. The apparent best feature is operation `shape`, saving `35.900` bits
after feature charge and staying positive in `5/5` prefix-selected cells. But
this is not promoted: random relabel controls with the same category sizes
reach p95 `44.763` bits before feature charge, above the observed `39.806`,
and chunk-recurrence features are sparse. This rejects transition/chunk class
labels as a reliable explanation for the missed endpoints.
A skeleton generation route review then consolidates the current strategic
state instead of adding another local sweep. Across `8` route families, there
are `0` promoted generator routes, `2` promoted clue/dependency routes, and
`5` rejected, weak, or deferred routes. This changes the recommended path:
boundary-frontier work is saturated as a main route. The next aligned work is
not another local cutpoint/length/miss-label policy, but a joint
target-stream/parser or explicit latent-state account that emits digits and
boundaries together instead of choosing endpoints after the target text is
known.
A first joint target-stream parser gate then tests the simplest version of
that route: emit `(boundary flag, digit)` pairs under prefix-trained contexts.
It fails. The best nontrivial model, `joint_pair_context_order0`, is
`-29.950` aggregate bits versus the factorized digit+global-boundary baseline
and is positive in only `2/5` prefix cells. This rejects the simple pair-token
model, not the broader latent-state route; a future parser needs real state,
not just coupling the current boundary flag to the current digit.
A boundary hazard state gate then tests a minimal real parser state: age since
the last emitted boundary, plus related sequential state features. This is the
first positive result on the joint-parser route. The best feature,
`age_bucket`, reduces boundary-flag coding by `170.175` bits after feature
charge, is positive in `5/5` prefix cells, and beats same-count random boundary
p95 (`167.705` bits before feature charge). It is still not an exact parser:
it emits a boundary probability distribution and does not derive exact
endpoints. A follow-up endpoint decoder grants the true per-book internal
cutpoint count and still fails: it recovers only `9/343` cutpoints, beats
same-count random endpoint p95 in `0/5` cells, and decodes `0` nontrivial books
exactly. The hazard is therefore a coding prior, not an endpoint selector.
A combined endpoint decoder then adds the promoted target-digit surprisal clue
to the same hazard state. This is a real dependency clue but still not a
generator: the best prefix-trained family, additive `age_bucket` plus
`surprisal_bin`, recovers `74/343` held-out cutpoints and beats same-count
random endpoint p95 in `5/5` cells, but still decodes `0` nontrivial books
exactly.
A latent transducer beam gate then changes the unit of test. Instead of
selecting endpoints after the fact, it trains mode, length, boundary, and digit
costs on prefix books and decodes future books with one beam where literal
spans, copy spans, copy sources, and boundaries compete together. This is the
right structural route, but the first gate is not promoted: it remains
teacher-forced by the target digit stream, recovers `224/343` held-out
cutpoints, beats random cutpoint p95 in `5/5` cells, and saves `675.669` paid
cutpoint-correction bits versus the cutpoint atlas, but reaches `0` nontrivial
exact books and only `131/421` source+length hits.
A closed-loop digit survival gate then removes within-book target teacher
forcing. It still grants book length and true prior material, so this is a
generous survival test rather than a complete corpus generator. Under the
current beam, the true book is never top-1 or present in the finished beam
(`0/150`), true-prefix survival is also `0/150`, and the mean maximum true
prefix fraction is only `0.007754`. This rejects the current model as a
closed-loop digit generator: the teacher-forced parser clue does not yet become
a self-generating process.
A closed-loop rescue ledger then asks whether the miss is at least close enough
for a compact latent steering state. On a fixed first/middle/last suffix-book
sample per cutoff (`15` book instances), oracle rescues can force all books
exact but require `1732` rescues, `21403.967` rescue bits, and `3.069669x` the
raw digit cost; no sampled book needs zero rescues, and the first rescue happens
near the first `1.5%` of each book. This is high external control, not a
near-miss beam-width artifact.
A rescue surface audit then maps those rescue events back onto the canonical
skeleton after decoding. It classifies `1732` rescue events: `1721` fall inside
canonical copy spans, only `5` inside literal spans, and `6` at book end. Exact
internal cutpoints account for only `27/1732` events, near-cutpoints for
`82/1732`, and operation starts for `27/1732`. So the missing state is not a
simple visible-boundary trigger; it is a decoder-visible copy-state/content
control problem.
A copy-state rescue diagnostic then separates missing source material from
candidate pruning/ranking. In the same rescue trace, only `16/1721` copy-span
rescues arrive via a copy emission, while `1705/1721` arrive by single literal
steps. On the sampled canonical copy ops, the declared source payload matches
the target in `32/32`, and some correct prefix exists in the raw copy inventory
for `32/32`, covering `1063/1240` copy digits. But the pruned candidate set
contains a correct prefix for `0/32` copy ops. This does not promote a
generator, but it sharply locates the next constructive route: copy candidate
ranking/pruning or a copy-continuation state, not another boundary detector.
A copy-candidate ranking frontier then tests the simplest target-free rescue at
the same top-80 budget. The current source-penalty pruning keeps only `6/1240`
copy prefix digits on the unique sampled ops. The best simple policy,
`longest_recent`, improves that to `56/1240` and barely beats random top-80
digit p95 (`55`), but this is only `0.045161` of the copy digits. Simple chunk
ranking is therefore not a generator component; the constructive route now
needs richer copy-control state or a paid copy hint stream.
A copy hint stream lower-bound then prices that route after granting op start,
copy type, copy length, and exact prior material. Under those grants, the hint
only chooses the same-length chunk. The best rank-coded policy,
`frequent_longest`, costs `1873.768` bits for `208` copy ops and `9301` copied
digits, versus `2550.594` raw source-address bits and `2366.891` uniform
same-length chunk bits. This promotes a useful lower bound for a paid
copy-control stream (`676.826` bits saved versus source addressing), but not a
generator: starts, types, and lengths are still external.
A copy hint stream structure gate then tests whether that paid rank stream has
simple prequential structure. It does not. Across prefix/suffix cutoffs, direct
rank coding costs `3998.858` bits, while the best bucket-plus-offset feature
code costs `5162.759` bits, for `-1163.901` bits of saving. Shuffled bucket
controls are less bad at p95 (`-1048.351`). So the lower-bound stream remains a
valid dependency-reduction target, but simple rank buckets over length,
occurrence, candidate count, op index, or target-start context do not explain
it.
A unified control program audit then stops opening local gates and consolidates
the residuals in one ledger. The ledger covers `261` ops, `208` copies, `53`
literal runs, and `266` innovation digits; target starts are derived in
`261/261` rows from prior lengths. Replacing raw source addresses with copy
hints and a joint `type:length` control stream organizes the residual from
`5289.866` to `3532.404` bits, but the holdout generator still produces `0`
exact books and `0` exact ops without the atlas/control streams. Only
`previous_op_to_next_control_symbol` is promoted as a non-tautological coupling
clue. This is a partial synchronization clue, not a unified authorial control
program; `row0`, plaintext, and the compression bound remain unchanged.
A stateful control program audit then tests the direct constructive follow-up:
turn that `previous_op` clue into an exact `type:length` generator using only
book id, book length, remaining length, and previous emitted control. This
shortcut fails. The best model, `remaining_prev_bucket`, costs `4600.432` bits
over prefix/suffix cutoffs, `1001.211` bits worse than independent exact
type+length declaration, and worse than shuffled-control p95 (`-850.701`).
Greedy generation gets `0` exact books; Beam20 exact hits occur only for
trivial one-operation books under a rejected codec. Exact `type:length` remains
an external stream, and the next route needs a different length-innovation or
joint latent-state representation rather than another observable Markov/context
program.
A length innovation factor audit then changes the representation rather than
the local context. It splits each exact length into a coarse
`type:length_bucket` control stream plus a within-bucket residual. This is a
useful dependency factorization: independent `op_type + exact_length` costs
`1855.639` bits, while `type:length_bucket` plus uniform residual costs
`1741.641`, saving `113.998` bits after paying the coarse stream. But the fine
residual is not generated: the best residual context, `type_bucket`, is still
`117.997` bits worse than uniform residual declaration, and no residual feature
is promoted. The blocker is therefore narrower but still external:
within-bucket length innovation.
A coarse control program audit then tests the other side of that factorization:
the `type:length_bucket` stream alone, with per-book operation count granted.
This is the first positive result on the control-program route after the exact
stateful model failed. The best model uses `op_count_bucket`, costs `1512.974`
bits across prefix/suffix cutoffs, saves `254.413` bits versus uniform coarse
control, and beats same-multiset shuffled p95 (`116.843`). Beam20 recovers
nontrivial held-out coarse sequences in every cutoff. This promotes a
coarse-control program candidate only: op-count, exact within-bucket residuals,
literal innovation, copy hints, seed books, and row0 remain external.
A book-level coarse length controller audit then removes that op-count grant
inside an integrated book-level test. Given `book_length`, the decoder scores
latent op-count candidates, generates coarse `type:length_bucket` sequences,
filters by bucket-sum feasibility, and represents exact residual lengths as a
composition index. This promotes the strongest current generation candidate:
true op-count survives in beam `120/150` times, true coarse sequence survives
`56/150` times (`13` nontrivial), above same-multiset p95 `37`, and residual
coding improves from `1031.010` independent bits to `665.782` composition-index
bits. Integrated latent beam plus residual composition costs `3146.578` bits
versus `4478.440` for separated op-count/coarse/residual declaration. It is
still not a complete generator: coarse-sequence corrections, composition index,
literal innovation, copy hints, seeds, and row0 remain external.
A composition-index structure audit then tests that residual field directly.
The best prefix-holdout model, `count_x_length__quantile10`, is not promoted:
uniform composition-index coding over repeated holdouts costs `1198.420` bits,
while the model costs `1211.748` bits (`-13.327` saving), essentially at
random-rank p95 (`-13.273`). Edge ranks are rare (`2/48` nontrivial books) and
low-half ranks are balanced (`24/48`). The composition-index codec remains a
valid structural reduction, but the exact index stays external payload.
A minimal external tape program audit then consolidates the residual into an
executable decoder contract rather than another field-local search. With seed
books `0..9`, coarse `type:length_bucket`, book-level composition indexes,
literal payload tape, and copy-hint/source tape paid explicitly, the decoder
roundtrips `70/70` books and `261` derived operations. The unified tape ledger
charges `9992.848` bits including seed payload (`5633.990` seed,
`935.675` coarse control, `665.782` composition index, `883.633` literal
payload, `1873.768` copy-hint rank). The tested macro/template program is not
promoted: after grammar/correction charges it is `-4942.611` bits worse than
separated coarse+composition declaration, with only `1` nontrivial exact book
generated without a sequence atlas. This gives a cleaner blocker ledger, not a
new generator.
A source-tape removal audit then tests the largest non-seed tape inside that
executable decoder. Granting seed, coarse controls, exact lengths, and literal
payloads, decoder-visible source policies try to choose copy sources online and
pay uniform source-address exceptions on misses. The best policy,
`previous_source_end`, hits only `22/537` holdout copy ops, gives `0` exact
unrepaired books, and costs `6672.081` bits versus `5062.568` copy-hint
baseline (`-1609.513` saving; random visible-source p95 `-8.288`). The
copy source/hint tape therefore remains external under decoder-visible policy
tests.
A book-level controller program integration audit then tries to convert the
strongest positive coarse-control clue into an actual executable decoder
component. The frozen `book_length__op_count` controller is inserted into the
minimal external tape program and compared directly against the paid
`coarse_control + composition_index` ledger. It is not promoted: across
prefix/family holdouts, the baseline costs `3824.176` bits, while controller
plus beam-rank/full-sequence corrections costs `4069.056` bits (`-244.881`
saving), even with `0.000` model/grammar descriptor bits charged. The true
sequence is in beam `66/186` times (`16` nontrivial), but top-1 exact books are
all trivial (`38` books, `0` nontrivial). The book-level controller therefore
remains a predictive clue, not an executable program component.
An executable program frontier synthesis then consolidates the pre-x64 state:
the explicit decoder still roundtrips `70/70`, but the representation now has
`0` promoted executable tape reductions. External tape cost remains
`4358.858` bits excluding seed and `9992.848` including seed. The rejected
routes are macro/template program (`-4942.611` bits), decoder-visible source
tape removal (`-1609.513` bits), and book-level controller integration
(`-244.881` bits). The conclusion is methodological: the current tape-ledger
representation is useful for accounting, but the next real generator route
needs a representation change, most likely a joint chunk-origin program, not
another local field codec.
This frontier is later superseded for one field only: the online x64
coarse-control program below reduces the executable coarse-control tape. The
older conclusion still applies to macro/templates, source tape removal, and the
other residual tapes.
A joint chunk-origin route audit then makes that representation change
explicit. Exact target-chunk dictionaries are rejected (`256/261` operation
chunks unique; all-chunk dictionary `+32442.167` bits versus the
target-conditioned baseline), shallow chunk signatures are rejected, the
current external-tape program remains a frontier ledger, and
target-conditioned source collapse remains lower-bound-only because it grants
the missing target chunk. The selected next gate is
`joint_chunk_origin_beam_pilot`, which must propose chunk-origin hypotheses
jointly with source choice, length, and literal innovation; no generator is
promoted by this route-selection audit.
A bucket-level chunk-origin beam pilot then executes the first constrained
version of that route. Granting op start, copy type, previous material, and
only the coarse length bucket, the best prior-chunk ranking policy costs
`2649.756` bits for `208` copy ops. That is a real signal against uniform
bucket candidates (`507.351` bits saved; `5/5` prefix holdouts beat random
p05), but it is still worse than the exact-length copy hint (`1873.768` bits)
and raw source address (`2550.594` bits), with only `5/208` top-80 hits. This
keeps joint chunk-origin open as a representation route, but not as an
executable program component; the next blocker is a sharper target-free
length/chunk prior.
A chunk length-prior integration audit then tests that direct rescue as a
two-stage program: pay a prefix-trained copy-length prior inside the coarse
bucket, then use the same-length copy hint. Full-fit, `bucket_opcount_pos`
looks attractive (`562.273` length-prior bits; `2436.040` with copy hint,
`-103.509` bits versus composition-index + copy-hint), but it does not
generalize: prefix holdout gives `0/5` positive-saving cells against uniform
feasible length. The length-prior rescue is therefore posthoc under current
evidence and not an executable generator component.
A Markov chunk-content prior audit then tests the other obvious rescue:
use the promoted `prev2` digit model as a content prior for same-length copy
chunks. It also fails as a chunk-origin selector. Content-first Markov policies
beat frequency/recency in `0/5` prefix holdouts and cost `4244.687` aggregate
bits versus `3998.858` for frequency/recency (`+245.829`). Markov as a
frequency/recency tie-breaker gives no improvement. The `prev2` clue therefore
remains scoped to digit/boundary statistics, not chunk selection.
A latent-state route synthesis then consolidates the local route failures. The
current executable tape program is still only a ledger, bucket chunk-origin is
too broad, copy-length prior is posthoc, `prev2` content is not a chunk
selector, observable previous/remaining state is rejected, and unified coupling
still gives `0` exact books/ops without atlas. The next aligned route is
`latent_nonlocal_state_program_pilot`: a hidden/nonlocal state program that
jointly accounts for control, length/chunk origin, literal innovation, and copy
availability. Isolated length/content/source priors are closed as the main
route unless they are embedded in that joint state program.
A latent nonlocal state program pilot then tests the first small hidden-state
version of that route: prefix-frozen HMMs over joint operation tokens. The
model captures multistream coupling (`3204.220` bits versus `5342.667`
factorized and `3747.315` unigram), but it fails the order/nonlocal control:
it beats same-multiset shuffled p05 in `0/5` prefix cells. This is retained as
a multistream coupling clue, not a promoted nonlocal state generator.
A schedule-state multistream pilot then asks whether that HMM clue can be tied
to visible book/operation schedule states instead of hidden state. The
train-selected decoder-visible schedule models cost `3559.712` bits versus
`5212.286` factorized bits (`-1652.574`) and beat factorized streams in `5/5`
prefix cells, but they beat same-book shuffled p05 in `0/5` cells. Diagnostic
remaining/target-position states are cheaper but grant skeleton information.
So this remains a schedule/multistream clue, not an executable generator.
A book multiset/order factorization audit then decomposes that schedule signal.
The same `3559.712` bits split into `2972.334` per-book joint-token bag bits
plus `587.378` exact within-book order-index bits. The bag saves only `57.222`
bits versus the global joint-token bag and beats permuted-feature p95 in `0/5`
prefix cells. This confirms that the schedule/HMM clue is mostly distributional
and order-index external, not a promoted book-composition program.
A within-book order program gate then attacks the order-index field directly:
given the true per-book multiset, prefix-trained no-replacement policies try to
emit the exact token order. They cost `606.765` bits versus `587.378` uniform
order bits (`+19.387`), beat shuffled-train p95 in only `1/5` cells, and beat
shuffled-test p95 in `0/5`. Beam20 keeps some short/nontrivial true sequences,
but the charged order field is not reduced, so this route is not promoted.
A sequence mutation program audit then tests the joint alternative: derive a
held-out book's operation-token sequence as an edit script from a previous
training-book sequence. Even as an optimistic lower bound, the selected policies
cost `4742.368` bits versus `3525.674` sequence-unigram bits (`+1216.694`
worse), beat shuffled-train p95 in `0/5` cells, and the oracle source lower
bound with paid source index is still `+832.040` bits worse than unigram. So
book-sequence mutation is rejected as the next generator route.
A generative route frontier synthesis then closes the recent operation-token
route family as the main path. Hidden HMM state, visible schedule state,
book-multiset factorization, within-book ordering, and previous-book sequence
mutation all produce `0` promoted generators under controls. The next aligned
route is therefore not another operation-token decomposition, but a
`digit_level_content_boundary_transducer` that pays an innovation tape and tries
to derive internal operation starts and copy/literal triggers without granting
target-conditioned copy availability, exact internal starts, book multisets, or
operation-token order.
The first digit/content-boundary transducer gate then labels every internal
digit position as `nonstart`, `literal`, or `copy` using only decoder-visible
prefix/content features. The selected feature (`suffix4_seen`) beats
shuffled-label p05 in `4/5` prefix cells and saves `31.030` bits versus a global
label model, but it predicts `0` start labels and costs `3075.566` bits versus
`2160.605` true-count composition bits (`+914.961`). This is a weak content
clue, not an internal-start generator.
A start-candidate ranking gate then asks the less brittle question: can the
same prefix/content signal rank a candidate set for starts, with missed starts
paid as corrections? It reduces the binary start-position ledger from
`2063.661` to `1941.433` bits (`-122.227`) and captures `37/343` starts, but it
beats random top-K p05 in only `2/5` prefix cells and leaves `306` missed-start
corrections. The candidate route is therefore not promoted yet; the current
gain may still be explained by candidate-set size rather than a robust boundary
state.
A surprisal start-candidate gate then checks whether the older digit-boundary
surprisal clue repairs that weakness. The decoder-visible version, which uses
only already-emitted digits, costs `1922.243` bits versus `2063.661`
composition bits and captures `71/343` starts, but beats random top-K p05 in
`0/5` prefix cells. The target-conditioned right-surprisal diagnostic is much
stronger (`1665.114` bits, `171/343` starts, `4/5` cells), but it looks at the
next digit and is not promotable as an executable generator. This closes the
surprisal shortcut: useful alignment clue, not a decoder-visible start program.
A lagged-surprisal boundary contract gate then tests the charitable
reinterpretation: let the generator emit the first digit of a new segment, then
mark the boundary one digit late. That makes right-surprisal less oracle-like,
but it has to pay for copied first digits that are externalized before the copy
can begin. The lagged contract costs `2153.437` bits versus `2063.661` exact
composition bits (`+89.777`), because `147` recovered copy starts add
`488.323` bits of lag tax, and it beats random top-K p05 in `0/5` cells. The
right-surprisal signal is therefore not rescued as an executable boundary
program.
A book residual-mode coupling audit then steps above individual fields and
tests whether the remaining external burdens synchronize at book level. This is
the first positive result after the boundary/topology closures: the primary
no-derived-shape joint mode costs `938.211` bits versus `2055.480` independent
field bits (`1117.269` saved), is positive in `20/20` prefix/family splits, and
beats shuffled-within-stream p95 (`755.429`). The stricter burden-only variant
also survives (`357.235` saved versus p95 `132.102`). This does not generate
exact `type:length`, literal payload, or copy hints, but it promotes a new
representation target: a latent book-mode program over residual burdens rather
than more local endpoint/source selectors.
A latent book-mode program gate then tests that exact next step and demotes the
simple version. Features available to the decoder (`book_length` bucket,
numeric phase, and previous decoded mode) do not predict the residual mode well
enough: the selected program costs `945.479` bits versus `891.772` global mode
bits (`-53.707` saving), has only `2/20` positive splits, and does not beat
shuffled-mode p95. The coupling remains useful evidence that residual burdens
are synchronized, but the mode is still a paid compact label under current
features, not a generated book controller.
A residual-mode header codec gate then tests whether the mode is at least
useful as a paid external header for exact decoder tapes. It is not. The header
codec saves only `110.682` bits on coarse control, loses `7.887` bits on
literal payload, and pays `891.772` mode-header bits, ending at `10950.680`
bits versus `10161.703` baseline (`-788.977`) with `0/20` positive splits. The
real modes are less bad than shuffled modes, but they still do not reduce the
executable ledger after header cost. The residual mode therefore remains a
structural coupling clue, not a paid codec or generator.
A residual burden cross-prediction audit then checks whether cheaper
leave-one-field-out modes can at least predict each burden class. They can, but
only before header cost: literal-digit, copy-hint, and composition burden save
`68.293`, `160.010`, and `166.167` bits conditionally, all above shuffled
controls; after paying the mode headers they become `-787.181`, `-639.919`,
and `-703.874`. This keeps the residual-mode result as a real synchronization
clue while blocking promotion as ledger reduction.
A paid-control context payload codec gate then removes the new-header cost by
using only already-paid or derived fields: coarse `type:length_bucket`,
operation-position bucket, book-length bucket, and op-count bucket. That route
also fails to reduce the executable residual: literal payload digits save
`-61.049` bits, copy-hint rank buckets save `-61.147`, and composition-index
quantile buckets save `-60.345`, with no shuffled-target p95 win. The current
paid/derived control fields therefore do not explain the payload residual
streams.
A parser/decoder frontier synthesis then consolidates the current representation
state. It closes the executable external-tape program, paid-control context
codec, local branch-choice residual selector, and beam-rank/Markov selector
routes under current evidence. It retains only weak clues: width-5 stable-branch
survival, innovation-tape shape, and length/joint `type:length` control
structure. The next aligned route is therefore not another isolated selector,
but a target-free internal-operation-start program with missed-start and rank
corrections paid explicitly.
A target-free internal-start gate then tests that route directly by interpreting
the promoted book-level `type:length_bucket` controller as a start generator:
book length is granted, op-count/coarse sequence are decoded in prefix-trained
beam, and exact starts are recovered only after paying a residual-composition
index. The true coarse sequence is in beam above the previous same-multiset
control (`56/150` versus p95 `37`), but this generates only `13/343` internal
starts before corrections and costs `3146.578` bits versus `2811.673` for
explicit opcount+cutpoint+type declaration. It is therefore a weak clue, not a
promoted internal-start program.
An internal-start beam-capacity gate then tests whether that failure is merely
beam width. Wider beams improve coverage monotonically: x64 reaches `109/150`
true coarse sequences and `98/343` internal starts before correction. After
charging width choice, rank, residual composition, and corrections, it costs
`2750.345` bits versus `2811.673` for explicit opcount+cutpoint+type
declaration (`+61.328` bits). This promotes only an internal-start
capacity-ledger reduction candidate, not an exact generator: `41/150` coarse
sequences still miss the beam and most internal starts still require residual
correction.
The follow-up same-multiset control audit validates that the x64 result is not
just generic beam capacity. Under the same decoded beams, the real payload gets
`109` sequence hits and `98` generated internal starts, above shuffled-payload
p95 values of `63` and `56`. This upgrades the x64 route to a controlled
capacity-ledger candidate, but still not to an executable generation formula:
missed coarse sequences, residual composition indices, and correction fields
remain paid.
A stricter paid-control gate then verifies that the same result also survives
as a cost reduction, not merely as higher hit count. The real x64 coarse-control
tape pays `1549.117` bits and saves `818.269` bits against direct declaration;
same-multiset shuffled controls reach only `466.838` bits saving at p95 and
`1900.549` paid bits at p05. This promotes a controlled coarse-control tape
reduction candidate. It still leaves the fine residual composition index,
literal payload, copy/source hints, seed payload, and `row0` outside the
generator.
An online executable follow-up then runs the x64 controller once over books
`10..69`, training only on previous decoded/corrected books. This is the first
promoted executable tape reduction in the current decoder contract: `37/60`
coarse sequences and `78/261` ops are generated without coarse correction,
`41/201` internal starts are generated, and paid coarse-control cost falls to
`876.412` bits versus the current minimal coarse ledger at `935.675`
(`+59.263` bits). Same-multiset controls are negative at p95 against the minimal
ledger (`-51.784`), and coarse+composition falls from `1601.457` to `1542.194`
bits. This is real generation-program progress, but still only for the coarse
control tape: fine residual composition, literal payload, copy/source hints,
seed payload, and `row0` remain external.
The executable v2 residual coupling audit then makes that state the new ledger:
uniform coarse control is replaced by the online x64 rank/correction tape, so
external bits excluding seed fall from `4358.858` to `4299.595` and including
seed from `9992.848` to `9933.585`. The same audit tests whether the online x64
state also predicts the exact composition index. It does not: the best
`op_count` context costs `1300.041` bits versus `1198.420` uniform composition
bits, with shuffled-train p95 saving only `-9.046`. The v2 ledger is promoted;
the fine composition index remains external.
The remaining-tape coupling gate then tests the broader possibility that the
online x64 state is a latent residual state for the other tapes. It is not under
current evidence: composition quantile is `-20.918` bits versus global, copy-hint
rank bucket is `-37.807`, and literal payload digits are `-35.665`; none beats
shuffled controls and no weak target remains. The x64 result is therefore a
localized executable coarse-control improvement, not a shared generator for
composition, copy hints, or literal innovation.
The content-addressed event audit then tests a representation change instead of
another local context codec. Copy events choose prior content chunks inside the
online-x64 coarse bucket, so exact length and canonical source derive from the
selected chunk. This derives a canonical source for all `208/208` copy events
and matches the raw source in `200/208`, but it pays for a much larger content
rank tape: the residual costs `3686.781` bits versus the v2 residual
`3423.183`, with `0/5` prefix holdout splits improving v2. The route is
therefore `content_addressed_event_program_not_promoted`; the blocker has moved
to origin/content rather than coarse control.
The event-aligned chunk library audit then tests a narrower constructive route:
copy events may choose only prior operation-boundary spans, including short
concatenations of earlier event chunks. This sharply reduces candidate sets for
the rare aligned hits, but it explains only `6/208` copy chunks. The residual
cost is `3322.129` bits versus `3423.183` for v2, yet shuffled completed-book
boundaries still save `51.361` bits and the aligned-hit rank does not beat the
random p05 control. The route is therefore
`event_aligned_chunk_library_not_promoted`; most copy content remains subchunk
material whose origin is not explained by previous event boundaries.
The source-boundary candidate audit then targets that subchunk blocker directly.
Instead of choosing arbitrary content, it chooses intervals between
decoder-visible boundaries in previous material: book/event boundaries,
source-side `prev2` surprisal boundaries, and their unions. The best system,
`event_plus_surprisal_top20` with `long_recent` interval ranking, derives
`29/208` copy source intervals, reduces the v2 residual from `3423.183` to
`3280.192` bits (`-142.991`), improves all `5/5` prefix holdouts, and beats the
random-boundary p95 hit count (`29` versus `15`). This is promoted only as a
partial source-boundary program: `179` copy intervals still require fallback
copy hints, and the result does not touch row0, plaintext, or semantics.
The executable v3 integration then folds that partial program back into the
decoder contract. Roundtrip remains `70/70`; external bits excluding seed fall
from `4299.595` in v2 to `4156.604`, exactly preserving the `142.991` bit
source-boundary reduction inside the executable ledger. The new breakdown is
`876.412` online-x64 coarse bits, `275.077` source-boundary interval-rank bits,
`1609.521` fallback copy-hint bits, `511.961` residual composition bits, and
`883.633` literal payload bits, plus the unchanged `5633.990` seed payload.
This is real generation-program progress, but still not a complete formula:
`179/208` copy intervals, literal innovation, seed payload, and row0 remain
external.
The v3 robustness audit then checks the most important risk: whether that route
was only a full-corpus selected winner. It pays `4.392` bits to declare one of
`7` boundary systems and one of `3` policies, leaving the full-fit v3 gain still
positive at `-138.598` bits. More importantly, when system and policy are
selected using only prefix books and frozen for the suffix, all `5/5` suffix
splits remain positive with aggregate delta `-226.100` bits; the selected system
is `event_plus_surprisal_top20` in `4/5` splits and `surprisal_top20` in the
earliest split. This keeps v3 promoted as a robust partial executable-program
reduction, while preserving the same external blockers.
A boundary-mark propagation audit then tests whether the v3 boundary system can
become a persistent copied state. Source-side marks inside a paid or derived
copy interval are mapped into the target interval and made available to future
copy events. This raises derived intervals from `29/208` to `34/208`, but the
larger candidate sets make the ledger slightly worse: `3280.551` bits versus
v3 at `3280.192` (`+0.359`). A shuffled-propagation control gets even more hits
(`48/208`) while also worsening cost. Mark propagation is therefore not promoted
as the next generator route; v3 remains the active partial boundary program.
The one-sided source-boundary audit then finds a more useful extension. Instead
of requiring both source endpoints, it allows exactly one anchored endpoint and
leaves exact length in the book-level residual composition. Coverage decomposes
as `29` both-endpoint hits, `40` start-only, `56` end-only, and `83` intervals
with neither endpoint in the promoted boundary set. A fixed `end_first` policy
reduces the v3 residual by `49.465` bits before a `2.000` bit policy
declaration; after declaration the gain remains `47.465`, and prefix-only
policy selection is positive in `5/5` splits. The executable v4 integration
then preserves `70/70` roundtrip and lowers external bits excluding seed from
v3 `4156.604` to `4109.138`. This is promoted as another partial executable
dependency reduction, not a complete generator: `123` copy hints still fall back
and `83` intervals have neither endpoint anchored.
A shared innovation tape audit then tests whether that fine length residual can
reuse the already-paid literal innovation tape. The sizes make the hypothesis
worth testing (`266` literal-tape digits versus `261` length-residual events),
but the one-digit-per-op policies do not replace the residual tape. The real
tape is less bad than shuffled same-multiset controls after prefix selection
(`-36.755` bits versus p95 `-56.770`), yet it is still worse than uniform
residual declaration and hits only `53/493` suffix residuals. This is retained
only as a weak shared-innovation clue; the within-bucket residual tape remains
external.
An innovation stream transducer audit then reframes the problem more
constructively: instead of demanding free digit generation, treat the `266`
literal-payload digits as one external innovation tape. The first replay gate
does not promote a generator: the best target-conditioned policy gets `22/60`
exact books but does not beat shuffled-tape p95 (`23`), and blind replay gets
`0/60`. The second gate does open a live clue, however. The tape itself has
structure beyond same-multiset shuffles: seed coverage at minlen `3/4/5`
covers `231`, `153`, and `87` digits versus shuffled p95 `187`, `71`, and
`20`, and prequential Markov order `2` costs `879.609` bits versus shuffled
p05 `898.869`. This promotes tape structure, not a complete transducer; the
remaining blocker is the state/rule that decides when to consume the tape.
A tape-synchronized closed-loop gate then tests that blocker directly under a
generous setup: book length, canonical tape start, and true prior material are
granted, while target digits inside the book are not. It still does not promote
a generator: exact books in the finished beam remain `0/60`. But the canonical
tape is not interchangeable with a shuffled tape at the first-prefix level:
true-prefix survival is `19/60` versus shuffled p95 `7.45`, and mean true-prefix
max fraction is `0.002495` versus shuffled p95 `0.001134`. This is only a weak
sync clue because the surviving prefix is tiny; it opens a state-search route
without solving the transducer.
A seed-derived tape subcodec gate then prices the seed-coverage clue directly.
It does not promote a dependency reduction yet: the best paid seed-reference
codec, minlen `5`, costs `1063.761` bits versus `883.633` raw tape bits
(`+180.128`). But it remains a weak clue rather than a rejection of the route:
the observed copy coverage is `87/266` digits versus shuffled p95 `20.05`, and
its paid score beats shuffled subcodec p95 even though it does not beat raw
tape. The next constructive route is therefore a cheaper seed/tape reference
model or a state rule that makes these references less costly, not a claim that
the tape is already derived.
A seed-walk source model gate then tests the most obvious way to make those
references cheaper: replace absolute seed source positions with signed deltas.
That route is rejected. The best walk model costs `1106.842` bits, worse than
the absolute-source subcodec at `1063.761` bits and still worse than the raw
tape. The observed coverage remains a weak clue, but the specific source-walk
mechanism does not reduce dependency.
An innovation tape schedule gate then tests whether the per-book number of
innovation digits can be predicted from mechanical features. After correcting
for the global-majority baseline, no feature is promoted: the best result is
simply predicting the sparse majority count, giving `33/50` exact books at
cutoff `20` and saving `221.844` count bits, while the best real feature is
`5.585` bits worse and adds `0` exact books. This keeps schedule sparsity as a
weak clue but leaves the actual consume/copy state unresolved.
A tape trigger policy gate then tests the consume/copy state at a narrower,
explicitly conditional level: known operation starts are granted, and copy
availability is measured against the true target under the true prefix. Under
those grants, `copy_available` is promoted as a dependency-reduction clue: at
cutoff `20` it gets `172/182` holdout ops right, hits `17/27` literal ops, and
saves `48.262` bits versus literal-site lookup after table/correction cost.
This explains `36/53` literal ops as places where no copy is available, but it
still does not derive operation starts, copy source, copy length, or a
closed-loop digit stream.
A decoder-visible trigger policy gate then removes that target-conditioned
availability while still granting known operation starts, true prior prefix, and
true tape state. The clue collapses: the best decoder-visible feature is
`next_digit_seen`, but it gets the same `155/182` ops as the global copy-majority
baseline, hits `0/27` literals, and costs `-4.807` bits after feature charge.
The target-conditioning gap is therefore the full `48.262` bits from the
conditional trigger gate.
A boundary-candidate trigger gate then composes the promoted `right_ge:4`
boundary candidate set with the trigger question, replacing exact operation
starts with a three-way candidate label problem: `nonstart`, `literal`, or
`copy`. This recovers a useful conditional clue under prefix holdout. The best
feature, `book_start_x_copy_available`, gets `745/819` candidate labels right at
cutoff `20`, recovers `46/120` actual starts (`4` literal and `42` copy), and
saves `116.856` bits versus three-way lookup, `169.492` bits better than the
same-cutoff nonstart-majority baseline. This is still not a generator: the
candidate set misses `107` canonical starts, and the best feature still depends
on target-conditioned copy availability.
A decoder-visible boundary-candidate trigger gate then removes that
target-conditioned copy availability from the same `right_ge:4` candidate-label
problem. A target-free clue remains, but it is narrow: `book_start` gets
`635/695` candidate labels right at cutoff `30`, recovers `34/94` actual starts,
and saves `87.064` bits versus three-way lookup. The internal-only decomposition
does not promote: after removing book starts, the best row hits `0/3` internal
starts and is `-5.044` bits versus the global baseline. So this is a book-start
invariance clue, not an internal skeleton parser.
An internal boundary-candidate trigger decomposition then runs the stricter
version of that same check while retaining target-conditioned copy availability.
It also rejects the internal route: after removing book-start candidates, the
best non-global row hits `0/70` internal starts at cutoff `20` and is `-5.285`
bits versus the internal nonstart-majority baseline. The full `169.492` bit
all-candidate trigger delta is therefore book-start dominated, not evidence of
an internal operation-start parser.
A book-start mode gate then tests whether that book-start clue can be refined
into a target-free first-operation mode rule. It cannot. The `60` derived book
starts split into `13` literal starts and `47` copy starts, but no non-global
feature beats the majority baseline after table/correction cost: the best
non-global row is `book_decade` at cutoff `20`, still `-4.000` bits versus
global majority, with `0` positive feature cells. So the first operation's
existence is structural; its literal/copy mode remains declared.
A generation dependency frontier ledger then consolidates the route. The
remaining shape frontier is explicit: `261` canonical ops split into `60`
book-start ops and `201` internal ops; the `right_ge:4` candidate set contains
`154` starts but misses `107` internal starts; internal candidate-trigger tests
do not promote even with target-conditioned copy availability. The next aligned
route is therefore internal operation-start generation without a target-future
oracle, not more book-start or mode selectors.
A length-control tape gate then tests whether those internal starts can be
reframed as a smaller external control stream: if book lengths and operation
lengths are granted, starts follow by cumulative sum. This opens a real clue but
not a generator. The length stream beats shuffled paid controls in `4/5`
prefix-holdout cutoffs, but the best paid feature requires the operation type
stream in `4/5` cutoffs and beats fixed-op-count cutpoint composition in `0/5`.
So the length tape has predictive structure, while cutpoint replacement and
source-free skeleton generation remain rejected.
A joint type-length control tape gate then removes the type grant by encoding
each operation as one `type:length` symbol. This also finds structure beyond
shuffled paid controls in `4/5` prefix-holdout cutoffs, but the pair alphabet
has `97` symbols and the paid model beats fixed-op-count cutpoint+type
composition in `0/5` cutoffs. The control stream is therefore structured, but
the direct skeleton-replacement route is rejected under the current features.
A hybrid innovation-tape subcodec gate then tests whether the literal payload
itself can be reduced by references to both seed text and prior emitted tape.
It cannot under paid costs: the best hybrid is `max_cover` at minlen `5`,
copies `90` digits, but costs `1075.983` bits versus `883.633` raw tape bits
(`-192.350` saving). So tape structure remains a clue, while the literal tape
payload remains external.
A book-control header gate then tests whether `op_count`, literal-op count, and
tape consumption can be generated as one per-book controller. It is rejected as
a predictive clue: the best feature is always global and beats shuffled
predictive controls in `0/5` cutoffs. The joint header is cheaper than separate
field coding in `5/5` cutoffs, but that is packaging, not generation.
A skeleton rule coverage audit then tests whether that atlas can be replaced by
simple decoder-visible rules. It cannot: the best op-type rule is just
`always_copy` at `208/261`, the best length rule reaches `116/261`, literal
length coverage is only `5/53`, and even the target-dependent copy-availability
control reaches only `208/261`. The exact skeleton remains materialized.
A skeleton template reuse audit then checks whether the materialized atlas can
be reduced to a small library of repeated templates. It cannot: exact
length/target skeletons have `58` unique templates across `60` books, with only
two repeated pairs (`43/50` and `47/62`). Type-sequence motifs repeat across
`39` books, but those motifs do not carry the length-bearing skeleton.
A type motif library ledger then prices the tempting partial reuse directly. A
type library has `193` type entries plus `60` book assignments and saves only
`8` records before residuals. After paying the remaining `261` length/target
records, the full representation is `514` records, `+253` versus the exact
skeleton atlas. The motifs remain descriptive; they are not a generator or
promoted library.
A copy-availability type exception ledger then tests the stronger
target-dependent clue. Min-length copy availability contains every copy event
(`208/208`) and forces `36` literal rows, leaving only `17` available-copy
literal exceptions; shuffled controls do not match that error level. The clue is
still `AUDIT_ONLY`: it depends on target text/copy availability and the
conditioned skeleton ledger is `278` records, `+17` versus the exact atlas.
A target-position derivation ledger then removes one possible overcount:
`target_start`, `remaining`, and operation index are all deterministic in
`261/261` rows from the cumulative length sequence and book length. That
sharpens the skeleton description from type/target/length to type/length with
derived positions. It does not change the `261` atlas rows or derive operation
types, lengths, copy sources, or literal payload.
An optional-literal exception rule audit then tests the remaining exception
surface. Among available-copy rows, `length <= 5 and remaining >= 10` catches
all `17` optional literal exceptions and leaves only `3` false-positive copy
rows; shuffled-label controls have best-error minimum `12`. This is a real
structural clue, but still not a generator because it depends on target copy
availability and on the external length atlas.
A prequential optional-literal validation then checks the clue without retuning
on suffix rows. Prefix-selected rules beat the no-exception baseline in `4/4`
suffix splits, and the fixed full-corpus rule also beats baseline in `4/4`.
But train-selected rules trail suffix-oracle rules by up to `1` error, and the
family still depends on target copy availability plus the length atlas. This is
predictive support, not promotion.
An operation-type dependency ledger then separates the real gain from the
remaining blocker. If target copy availability and the length atlas are allowed,
explicit `op_type` dependency falls conceptually from `261` fields to `3`
residual type errors. But the retained `261` length rows mean the type+length
ledger is still `264` records, `+3` versus the exact skeleton atlas, and source
choices plus literal payload remain external. This clarifies dependency; it
does not promote a generator or change the bound.

An operation-length dependency ledger then freezes the sharper blocker. Target
positions are derived once the length sequence is known, and most operation type
decisions become downstream of length plus copy availability. The length
sequence itself is still not generated: source-free rules cover only `116/261`
operation lengths, copy-specific source-free rules cover `55/208`, literal
length rules cover `5/53`, and all `261` copy-length fields remain retained.
So the next generator question is length selection, not another op-type or
target-position ledger.

A decoder length candidate ambiguity audit makes that blocker harder to dismiss.
Even under generous assumptions where operation type is granted and copy source
is granted for copy rows, only `5/261` operation lengths are forced by syntax
and remaining capacity. The other `256/261` remain ambiguous, with median
candidate count `89` and roughly `1555.548` log2 candidate-space bits. That
means length selection still needs a real rule or parser objective; it is not
just a redundant field-ordering artifact.

A decoder length policy audit then rejects the simplest version of that rule.
Fixed min/max/quartile/median/previous-length policies over the candidate sets
do not recover the declared sequence. The best policy is `max_candidate`, but it
hits only `63/261` rows (`58/208` copies and `5/53` literals). Declared lengths
are spread across candidate sets, so a promoted generator would need a richer
length objective than a fixed candidate policy.

A recent-gates row0 compatibility refresh then checks gates `76..107` as one
unit against the independent row0 provenance front. The result is unchanged:
parser validation, path-stability controls, decoder/source-policy controls,
skeleton ledgers, and operation-type derivation improve or clarify the book
formula only. They do not predict row0 labels under holdout, beat the paid row0
lookup baseline, explain `39`/`93`/`19/91` beyond the existing surface clue, or
add CipSoft/authorial provenance.

A seed primacy audit then tests whether the usual operational seed assumption
itself has mechanical privilege. Under seed-only exact-copy coverage, books
`0..9` cover `8664/9567` non-seed digits and sit below the random k=10 median
(`9005` copied digits; percentile `0.21`). A posthoc greedy k=10 set
`[7, 8, 9, 13, 17, 20, 25, 39, 54, 67]` covers `9734` digits, but it is chosen
after seeing the corpus and still leaves source choice, literal payload, and
seed selection external. The result is `AUDIT_ONLY_COMPRESSION`, not seed-origin
promotion.
A prequential seed-selection audit then asks whether that posthoc signal
generalizes when seeds are selected using only prefix books. Train-greedy seeds
beat the random median in `7/7` prefix/k cells and p95 random train seeds in
`6/7`, so there is partial predictive structure. But operational prefixes beat
random median in only `1/7`, and train-greedy seeds still trail suffix-oracle
posthoc seeds. Seed selection remains audit-only rather than a promoted
generator.
A seed requirement closure audit then checks the front against the requested
baselines and controls. It closes `13/13` requirements, including centrality,
metadata/bookcase, random/permuted controls, declaration cost, family holdouts,
and prequential checks. This strengthens the audit boundary but does not promote
a seed-origin formula.

A segmentation decision audit then changes the unit from simple length policy
to parser trace. On the stable copy projection, `choose the longest previous
target match; break source ties by earliest source` recovers `207/208` copy
pairs, compared with random global-max source expectation `119.739/208`. This
is promoted only as a mechanical segmentation clue for target-text-aware
parsing: it reduces declared copy `(source,length)` dependence under that
parser view, but it does not generate the target digit stream source-free and
does not replace the full skeleton/literal ledger.
A parser dependency reduction ledger quantifies that boundary. Against the
exact skeleton ledger, the conditional target-text parser projection reduces
materialized records from `522` to `318` and removes `414` copy
`(source,length)` fields. The source-free greedy control is exact for only
`39/60` non-seed books, so the operation-start atlas remains retained.
A literal gap boundary audit then isolates why first-match greedy parsing
fails. Within each declared literal window, the stable stop maximizes
literal-offset plus next-copy length in `54/54` gaps; first available match
explains only `23/54`, and full-suffix best advance explains only `11/49`
followed-by-copy gaps. The local boundary clue is real, but the literal window
itself remains retained.
An online literal stop rule audit then removes part of that retained window:
the first confirmed local peak in available copy length, using confirmation
window `6`, predicts `45/49` followed-by-copy literal stops and `50/54` gaps
with the book-end default. Prefix selection chooses the same policy/window in
`5/5` cells, but the rule still has four followed-by-copy exceptions and is not
a source-free generator.
A literal-stop exception topology audit then maps those four misses. They split
into four classes, and the best source-free exception flag reaches recall
`0.750` with `9` false positives. No exception rule is promoted; the residual
four stops remain retained.
The integrated online parser audit then freezes the same stop rule and runs it
end-to-end, without declared literal windows or copy starts. It improves exact
books from the full-greedy control's `39/60` to `46/60`, but still drifts in
`14` books and over-literalizes the projection (`329` predicted literal digits
versus stable `265`). This is a partial parser improvement, not a promoted
source-free generator.
The integrated parser policy frontier then retunes only that same local-peak
family. `max_copy_length:window5` is selected in `5/5` prefix cells and matches
the suffix oracle in all of them, improving exact books to `48/60`. The
remaining `12` mismatches include missed book-start copies, missed internal
copies, literal understops, and one copy-length drift, so the policy is a
prefix-stable partial parser rather than a complete segmentation mechanism.
An immediate-copy override audit then rejects the natural missed-copy rescue.
Book-start, internal, and any-position overrides over thresholds `5..20` do not
beat `window5:no_override`; train-selected book-start overrides overfit in the
middle prefix cells and lose held-out suffix books. The remaining drifts are
therefore not explained by a simple "copy immediately when a strong match
exists" rule.
A peak-strength control tests the opposite rescue: wait for a stronger local
peak before ending a literal run. Thresholds `min_peak_len 5..30` do not improve
on `48/60`; `min_peak_len6` ties the total but increases literal digits and
trades some understops for missed-copy/overstop failures. The remaining drift
is therefore not just weak early peak acceptance either.
A residual-context audit then tests `64` observable parser-state predicates as
candidate correction flags. The best, `peak_len_le5`, reaches only TP/FP/FN
`4/3/8` over the `12` residual drifts, with precision `0.571` and recall
`0.333`; prefix-selected predicates match the suffix oracle in only `2/5`
cells. The residual frontier is therefore not closed by a single simple local
context flag.
A global-objective parser audit then tests the broader path-state shortcut:
book-local dynamic programming under six simple objectives over operation
count, literal mass, and copy mass. The objectives are stable under prefix
selection but wrong; the best reaches only `23/60`, far below the `48/60`
window5 parser. This rejects crude global optimization as the missing
segmentation rule.
A feature-weighted global parser audit then tests a slightly richer DP cost
family: literal mass, copy base cost, copy reward, short-copy penalty, and
book-start-copy penalty. The best of `16` profiles reaches only `26/60`, still
far below `48/60`, so a small linear cost over obvious copy/literal features is
also rejected.
The next structural shortcut, source-side block reuse, is also rejected.
Declared copy sources start on prior operation boundaries only `28/208` times,
end on them `29/208` times, and equal one prior operation chunk `0/208` times.
Boundary-aware source tie-breakers are worse than the existing earliest-source
global-max rule (`206/208` vs `207/208`), so operation chunking is not the
missing segmentation mechanism.
A single-drift repair oracle then localizes the remaining parser blocker. If
the first divergent operation in each residual book is replaced by the stable
projection and the same `window5` parser resumes, `11/12` residual books become
exact; allowing two such oracle repairs reaches `60/60`. This is strong
diagnostic evidence that most residual drift is a first-decision classifier
problem, but no rule is promoted because the repair is selected from the stable
projection.
The first non-oracle replacement attempt is negative. Across `36` observable
repair templates, including immediate-copy forcing, next-peak literal delay,
short-copy literal substitution, and copy shortening by one, the best policy
remains the unmodified `window5` parser at `48/60`; prefix selection matches
the suffix oracle in only `3/5` cells. The gate-16 oracle therefore localizes
the problem, but simple observable repair templates do not solve it.
A restricted conditional classifier then produces a genuine partial repair:
`if_peak_len_le5_then_skip_to_next_peak_ge5` improves the integrated parser from
`48/60` to `50/60`, applies only `4` repairs, and is selected in all `5/5`
prefix/holdout cells. This is the first non-oracle parser repair in the
segmentation front that survives prequential selection. It is not promoted as a
complete mechanism because ten mixed drift books remain.
A two-stage follow-up then keeps that repair as stage one and tests whether one
more observable predicate-action rule can close the remaining drift. It cannot:
the best pipeline remains the single gate-18 classifier at `50/60`, and
second-stage train selection matches the suffix oracle in only `3/5` cells.
The next blocker is therefore not another simple additive repair layer.
A post-repair oracle map then shows that the remaining drift is still mostly
local under an oracle view: with the `50/60` parser active, one stable-projection
correction repairs `9/10` residual books and two corrections reach `60/60`.
Book `20` is the only residual requiring two oracle corrections. This narrows
the next target but remains oracle-only, not a promoted parser.
A residual feature screen then tests whether that oracle map has a simple
non-oracle signature. It does not: the best overall feature predicate captures
only `6/10` residuals while firing on `13` clean control decisions, and the best
zero-false-positive predicate captures only `1/10`. The next segmentation
blocker is therefore not a single missed-copy/understop feature flag, but a
richer path/state account.
A residual branch continuation audit then tests a first version of that
path-state idea. The observable branch grammar can express all `10/10` stable
residual operations, and an oracle stable-prefix score chooses all of them, but
the best non-oracle continuation objective (`balanced_ops_literals`) chooses
only `6/10` while changing `20` clean controls. Simple branch consequences over
operation count, literal mass, or copied mass are therefore rejected.
A branch-ranker prequential audit then tests whether the same path choice can be
learned from prefix books. It cannot: the active-branch baseline is `224/234`
with `0/10` residual hits, while the best full-fit ranker is worse at `223/234`
and still hits `0/10` residuals. A residual-only mode can hit `7/10`, but only by
changing `221` clean controls. No learned branch ranker is promoted.
A contextual mode selector then tests a finite observable state table. It finds
a weak full-fit clue: the best context family (`context_combo`) reaches
`229/234`, resolving `5/10` residuals with `0` clean-control changes. It is not
promoted because prefix/holdout keeps only `1/5` zero-false-control cells and
only `1/5` all-residual-covered cells.
A contextual stability audit then stress-tests that clue. The full-fit
`5/10` drops to `1/10` under leave-one-book retraining and to `0/10` under
leave-context-out; support pruning also collapses most of the gain. The context
table is therefore weak post-hoc evidence, not a stable parser rule.
A hierarchical context backoff audit then checks whether the failure was merely
sparsity. It preserves the same full-fit ceiling (`5/10` residuals, `0` false
controls), but prefix/holdout still has only `1/5` zero-false-control cells and
held-out residual gains come with false clean-control changes. Backoff is not
promoted.
An observable decision-tree policy audit then tests the stronger small
finite-state version of that idea. The best tree reaches `228/234` total hits
and `4/10` residual hits with `0` clean-control changes in full fit, but
prefix/holdout recovers `0` held-out residuals in every split that contains
residuals. The branch choice is therefore not explained by a small observable
decision tree over the current branch/position predicates.
A target-boundary recurrence audit then tests the chunk-boundary version of the
same segmentation question. If the stable branch preserved a recurrent
target-side boundary, raw context recurrence around `target_start + length`
should prefer it. It does not: the best recurrence policy reaches only
`31/234`, catches `1/10` residuals, changes `194` clean controls, and is worse
than random-boundary controls on total hits.
A future copy opportunity audit then tests the complementary local consequence:
maybe the stable branch is chosen because it creates or preserves copy
availability in the next few target positions. That also fails. The best
opportunity policy reaches `96/234`, catches `2/10` residuals, and changes
`130` clean controls; randomized opportunity features are stronger on total
hits.
A source-state continuity audit then tests the remaining cheap path-state idea:
maybe the stable branch keeps continuity with the previous copy source,
source-end, or length in the accepted book-local prefix. This is also rejected.
The best policy, `min_source_delta`, catches `6/10` residuals and is stronger
than shuffled source-state controls, but it changes `13` clean controls and
has `0/5` zero-clean-false-change holdout cells. This does not change row0,
plaintext, translation, or the `8154.676268` compression bound.
A global carryover version then grants the full stable-projection history as
previous-copy state across books. This favorable upper bound still does not
promote: `min_source_delta` again catches `6/10` residuals, changes `13` clean
controls, and has `0/5` zero-clean-false-change holdout cells. Carryover source
state is therefore not the missing segmentation rule.
A phase/grid segmentation audit then tests short cycles
`2/3/4/5/8/10/16/20` over target boundary, length, source, source end, and
source-target phase. The best `source_mod0_10/20` clue catches only `1/10`
residual with `0` clean false changes, and prefix/holdout recovers no held-out
residuals. This is recorded as a weak full-fit clue, not a parser rule.
A context nearest-branch audit then tests whether raw target digit context
recurs with stable branch actions. It does not: the best leave-one-book nearest
policy is worse than the active baseline (`216/234` vs `224/234`), recovers
`0/10` residuals, changes `8` clean controls, and is matched or exceeded by
shuffled training labels.
A structural-signal consensus audit then asks whether the weak clues only work
when they agree. Four families vote: source-state, phase/grid, near-future
copy, and recurrent boundary. Precision comes only by refusing to move: the
best consensus ties the active baseline at `224/234`, recovers `0/10`
residuals, and changes `0` clean controls. Lower-threshold variants can move,
but introduce false clean-control changes.
A residual vote decomposition closes that weak-signal front. Threshold `3`
would correctly flag only books `16` and `39`, but also moves `18` clean
controls; threshold `4` leaves only book `39` and still has `1` clean false
move. The structural vote family therefore has no hidden clean cutoff.
A branch-choice frontier closure audit then compiles gates `16-35` as one
ledger. It audits `20` gates, including oracle repairs, observable repairs,
finite context tables, source-state rules, phase/grid rules, recurrence,
consensus, and vote decomposition. It promotes `0` complete parser rules:
the stable residual branch is oracle-repairable, but the tested non-oracle
weak-signal families do not justify another local branch-choice combination.
This is a closure result, not a new generator; the next blocker remains a
richer path/state segmentation mechanism or a source-free target digit account.
A path-template reuse audit then tests the next structural shortcut. It builds
a library of exact source-free operation-length templates of width `1..3` from
the `50` books already parsed exactly by the active parser, keyed by observable
state. The library explains `0/10` residual first-drift corrections
deterministically, so simple reuse of a seen multi-op path shape is rejected.
This leaves the blocker at richer latent path/state, not another local
branch-choice feature.
A trajectory-neighbor parser audit then tests that richer shortcut directly:
nearest cumulative parser-state trajectories over trajectory-only, context-only,
and combined vectors, with `k=1/3/5`. Every tested policy explains `0/10`
residual first-drift corrections, while shuffled labels average `0.190` hits.
Nearest trajectory reuse is therefore rejected as the missing segmentation
mechanism.
An observable-state support audit then decomposes that failure. In the best
exposed state family, only `4/10` residuals have support in exact parser books,
`6/10` are out of support, and `0/10` have deterministic exact-label matches.
The supported cases are ambiguous or contradictory. The next requirement is
therefore genuinely latent state or a source-free target stream, not another
reuse rule over the current exposed features.
A latent-state requirement audit then tests whether simple observable splits
can serve as that latent state: book parity/modulo/decade/half, operation
bucket/parity, target half, and active operation splits across the current
state families. Across `33` split tests, the best still gives `0/10`
deterministic residual matches. All `10` residual distinctions, covering `9`
distinct stable labels, still need a real latent/source-free explanation.
A latent-state lookup cost gate then prices the ad hoc fallback. Selecting the
`10` first-drift residual sites and ordering their stable labels costs at least
`79.361` bits before any human-readable rule is charged; a per-site dictionary
variant costs `90.269` bits. The full post-repair oracle needs at least `11`
correction events, so even this lookup is not a full parser. A latent state is
therefore useful only if it supplies a compact rule, not merely a name.
A compact latent rule frontier then tests that requirement directly. It charges
`6276` single/two-rule residual-visible rule sets against the `79.361`-bit
lookup. The only apparent MDL win has a false positive; the best
zero-false-positive rule is `+1.773` bits worse than lookup and gets `0/4`
held-out hits. Compact residual-visible latent rules are therefore rejected.
A stricter source-free residual rule gate then removes target-dependent active
parser features and tests only book/op ordinal predicates. The apparent
structural win again needs a false positive; the best clean rule hits only
`1/10` residuals, costs `+1.651` bits versus lookup, and prefix-selected rules
get `0/4` held-out hits. This rejects the source-free ordinal selector path
and leaves the blocker at a richer latent path/state mechanism or an actual
source-free account for the target digit stream.
An operation n-gram grammar gate then tests a different path-state hypothesis:
train unigram, op-bucket, previous-type, previous-label, and previous-label
plus op-bucket grammars on the `50` exact parser books, then predict the
`10` residual first-drift choices. Every family gets `0/10` hits. Richer
contexts become unsupported; the lowest-net unigram has `10` false positives.
This rejects a compact operation-sequence grammar as the missing latent state.
A residual exception transfer gate then asks whether the `10` residual
corrections at least predict each other. They do not: `6` observable feature
families with `k=1/3/5` nearest-residual transfer all get `0/10` hits, and
prefix/holdout has `0/4` cells with any held-out hit. The residual set still
looks like unresolved latent state, not a reusable exception class.
A branch-rank position audit then checks whether the stable branch is simply
near the top under observable branch orderings. The best top-1 ranker,
`balanced_ops_literals`, recovers `6/10` residuals but changes `20` clean
controls; best top-3 coverage is `8/10`. This is a weak diagnostic signal, not
a promoted parser rule.
A branch-rank exception cost gate then prices that weak signal. Applied
globally, `balanced_ops_literals` plus corrections costs `+96.497` bits versus
the explicit residual lookup. A residual-gated version is `-4.684` bits only
after the residual sites are already granted, so it remains audit-only rather
than a source-free parser improvement.
A residual-site detector gate then tests whether that granted condition can be
made observable. It cannot: the best branch-ambiguity rule is `6/10` residuals
with `6` false positives, the best zero-FP rule covers only `3/10`, and
prefix/holdout covers all held-out residuals in `0/4` cells.
A book-skeleton alignment gate then tests the broader path hypothesis that
whole-book operation skeletons from the `50` exact parser books select the
remaining residual operations. This is rejected more sharply: `27`
configurations get `0/10` residual unique-branch hits and `0/10` residual
type/length hits under the best full-fit alignment, with `211` clean false
changes. The residual `(source,length)` dependency is not removed by book-level
skeleton similarity.
A source-interval context gate then tests a narrower content-structure clue:
payload recurrence and source-target start/end neighborhood similarity. This
does find a real but destructive signal. The best source-target start-distance
policy catches `5/10` residuals with random-control `p=0.002`, but changes
`189` clean controls and has `0/4` cover-all holdout cells. It is retained as a
weak clue, not a parser rule.
A source-interval precision gate then asks whether that clue can fire only
where it is safe. Predicate gating improves the false-positive profile, but
does not promote a rule: the best full-fit repair still has `4` clean false
changes, and the best zero-FP rule covers only `3/10` residuals.
An observable-only correction then removes the diagnostic `drift_class`
predicate from that screen. The best zero-FP rule drops to `2/10` residuals;
the `5/10` full-fit signal remains, but still with `4` clean false changes and
no holdout promotion.
A source-interval cost gate then prices that weak clue against the explicit
residual lookup. The full-fit rule is `+3.410` bits worse after clean rollbacks
and misses. The zero-FP rule is only `-0.131` bits better before holdout and
covers only `2/10` residuals, so it stays audit-only.
A book-start copy subclass gate then isolates the tempting diagnostic subclass
without using `drift_class`. It catches all `3/3` book-start copy residuals
only with `6` clean false changes and `+32.421` bits versus lookup; the best
zero-FP rule catches just `1/3`, remains `+8.670` bits worse than lookup, and
has `0/4` clean oracle-cover holdout cells. The pattern is a weak clue, not a
segmentation rule.
An observable signature support gate then tests whether the exposed candidate
state itself is reusable. Across `6` decision/candidate signature families and
`3` label modes, the best full-fit signature has `0/10` deterministic residual
matches: `7/10` residuals are out of support, `2/10` are contradicted, and
only `1/10` is ambiguously supported. Prefix/holdout has `0/4` cells with any
deterministic residual match. This rejects the exposed candidate profile as the
missing parser state.
A sequential signature support gate then adds previous one/two operation shapes
and prior copy/literal counts to those signatures. This does not recover a
path rule: across `10` sequential families and `3` label modes, every residual
query is out of support, so the best result remains `0/10` deterministic
matches and `0/10` supported residuals.
A latent path-state budget gate then prices the fallback directly. A valid
latent account still pays `58.570` site bits plus `20.791` label-order bits,
so the best valid model is exactly the existing `79.361`-bit residual lookup.
Rows that look cheaper require a residual-site oracle, so they do not explain
generation.
A beam survival budget gate then asks a weaker path-state question: even if a
rule cannot select the stable branch directly, does a small observable beam at
least keep it alive? Under `max_suffix_copy_digits`, width `5` contains the
stable branch for the whole tested decision universe and survives all `5/5`
prefix/holdout cells. This is a real weak clue for path-state structure, but
not a promoted parser: top-1 still gets only `5/10` residuals, the fixed-width
paid model is `+4.750` bits worse than lookup, and the apparent rank lower-bound
saving assumes site/rank knowledge instead of a downstream selector.
A beam rank selector gate then tests that downstream selector directly. Inside
the width-5 beam, the full-fit `beam_context_combo` table resolves `10/10`
residual choices, but it also changes `4` clean controls. Prefix/holdout covers
all held-out decisions in `0/5` cells, and charging the `73` context-to-rank
entries makes the selector `+129.872` bits worse than the residual lookup. This
promotes only a full-fit selector clue, not a generation rule.
A beam selector stability gate then stress-tests that clue. It remains best
only at support threshold `1`, which means the decisive contexts are mostly
singletons. Leave-one-book retraining keeps only `4/10` residual hits,
leave-context-out keeps `5/10`, and prefix/holdout still has `0/5` cover-all
cells. The observable beam selector is therefore not stable enough to promote.
A beam hierarchical backoff gate then tests whether the failure is merely
over-specific context granularity. It is not: the best hierarchy,
`global_to_beam_combo`, ties the unstable full-fit row only at support `1`,
grows the paid table to `88` contexts, costs `+166.286` bits versus lookup, and
still has `0/5` cover-all holdout cells.
A residual patch program gate then decomposes the remaining choices rather than
trying another selector. The ten residuals do compress to five macro patch
classes, but the site cost alone is `56.631` bits, the cheapest paid macro
program is still `+2.490` bits worse than lookup, the best zero-false-positive
detector hits only `1/10`, and prefix/holdout exact detector cells are `0/5`.
This is a useful blocker decomposition, not a promoted parser rule.
A beam Markov state selector then tests a richer sequential-state variant over
the surviving width-5 beam. Free-run state reaches `230/234`, including `9/10`
residuals with `3` clean false changes, so there is a real full-fit state clue.
It still costs `+159.472` bits versus lookup and has `0/5` cover-all
prefix/holdout cells, so the selector is not promoted.

A seed-primacy integration audit incorporates that final report into the main
prequential/row0 boundary. The operational `0..9` seed hypothesis is rejected,
the better posthoc cores are recorded as compression/redundancy clues only, and
the prequential seed signal is kept as partial validation rather than a
generation formula. It changes neither row0 nor the `8154.676268` compression
bound.

Negative controls separate this from random substring opportunity: component
digit shuffles and random length-matched literals both saved `0.0` bits in 400
runs (`p=0.0025`). A stricter same-book component exclusion still saved `646.3`
bits, but shuffled book exclusions were not worse, so the controlled claim is
exact tape-substring reuse, not physical topology.

The later tape-inventory self-reference search compresses the 16 tape component
payloads themselves. It reconstructs 16/16 components, saves roughly `2727.7`
bits over literal tape storage, and beats component digit-shuffle/random
same-length controls (`p=0.0033`). Component-order shuffles are not worse
(`p=0.1561`), so the result promotes inventory reuse, not original tape order.
Combined with the literal-reference book recipes, the hierarchical formula
roundtrips 70/70 books at roughly `13858.5` bits.

The strongest book-generator upper bound in this front is now the sequential
LZ formula. It emits the 70 raw digit books in numeric order as literal runs
plus references to already emitted prior-book/current-prefix digits. It
roundtrips 70/70 books at roughly `10190.0` bits, with `812` literal digits,
`279` copy items, and `10451` copied digits. Controls are much worse for
within-book digit shuffles and random same-length books (`p=0.0062` each);
book-order shuffles are also usually worse (`p=0.0311`). This is a stronger
copy/reference fabrication upper bound, not a row0 origin.

The order-search follow-up does not promote an arbitrary non-numeric order.
The best of 800 sampled orders reaches `10004.0` bits, a gross `186.0` bit
gain over numeric order, but storing an arbitrary 70-book permutation costs
about `332.5` bits (`log2(70!)`). Net gain is therefore `-146.5` bits. Numeric
order remains the default unless a physical/source order supplies the order
without charging it as a searched permutation.

The cost-model refinement keeps the same sequential copy/reference generator
but charges literal runs as runs rather than as one flag per literal digit. It
roundtrips 70/70 books at `9944.0` bits, a further `246.0` bit gain over
sequential LZ v1, with `85` literal runs, `812` literal digits, `279` copy
items, and `10451` copied digits. Within-book digit shuffles, random
same-length books, and book-order shuffles remain worse than the observed
corpus (`p=0.0062` each). This tightens the fabrication-cost upper bound; it
does not explain row0 or add plaintext.

The dynamic-parse refinement keeps that same vocabulary and fixed `min_len=6`
but replaces the greedy parse with a dynamic-programming parse under the
run-literal cost. It roundtrips 70/70 books at `9823.3` bits, a further
`120.7` bit gain, with `84` literal runs, `795` literal digits, `281` copy
items, and `10468` copied digits. Digit-shuffle and random same-length controls
remain much worse (`p=0.0099`); book-order shuffles are only moderately worse
(`p=0.0396`), so this promotes a tighter copy/reference fabrication bound, not
an original-order claim.

The follow-up address search rejects a tempting refinement from the generation
formula report: back-distance, delta, and book-relative source addresses are
not cheaper under the fixed DP parse. Absolute `source_pos` remains the best
ledger at `9823.3` bits; the next-best tested address model costs `11507.9`
bits. The copy-graph audit is therefore diagnostic rather than compressive: it
materializes `281` copy edges, only `5` same-book copies, `32` source books,
and `52/84` literal runs reused later as source material. That atlas is useful
for future structured-order or seed-provenance tests, not a new formula.

The structured-order test closes the next public-topology variant for this
front. Numeric order remains best at `9823.3` bits. The partial public
Hellgate/bookcase orders cost at least `9993.1` bits (`+169.8`), and candidate
orders that fill ambiguous public rows cost still more. Because the manifest
has only `64` resolved unique books, `6` ambiguous rows, one duplicate resolved
row, and no fine tile/slot/orientation/read-order layer, no physical or
authorial order is promoted.

A later physical topology control-signal audit tests a narrower generator
variant: use partial public bookcase/order metadata to predict residual control
streams in the executable decoder. It also fails. On resolved unique topology
coverage, topology-conditioned coding is worse than global coding for coarse
control (`-107.149` bits), copy-hint rank bucket (`-102.873` bits), and op type
(`-46.439` bits), with `0/20` positive splits for each stream and no
permutation-p95 wins. This closes public macro-topology as a current control
program unless finer authoritative tile/slot topology appears.

Literal-seed addressing is also only an optimistic clue. If copy sources are
allowed to address prior literal runs without paying a source-mode cost, the
ledger reaches `9752.8` bits. That ledger is not a decodable mixed address
model. Once mode bits are charged, the same refinement costs `10033.8` bits,
worse than the previous `9823.3` gamma-length absolute `source_pos` formula, so
H-GEN3L is not promoted.

The grouped-mode follow-up closes the obvious objection to that rejection. A
sparse seed-run list is the best seed-using decodable grouped ledger, but it
still costs `9830.0` bits (`+6.7`). A seed-required RLE mask costs `9843.0`
bits (`+19.7`). Source-mode grouping therefore reduces the penalty versus
per-copy mode bits, but does not rescue literal-seed addressing.

The copy-hub macro follow-up is also rejected. Declaring source-book hubs or
target-default source books makes the address ledger larger, not smaller. The
optimistic target-default source lower bound costs `10326.9` bits (`+503.6`),
and the best decodable default-source model costs `10430.2` bits (`+606.9`).
The current absolute `source_pos` ledger remains the compact baseline.

The restricted hybrid-vocabulary reparse closes the next obvious route:
declare a small repeated digit-motif dictionary, then parse with literal runs,
prior-copy LZ references, and motif references. It roundtrips 70/70, but still
does not beat the DP LZ baseline. The nearest dictionary-using model is an
optimistic non-decodable `K=4` filtered motif set at `9840.7` bits (`+17.4`);
the nearest decodable dictionary model costs `10123.2` bits (`+299.9`).

The DP `min_len` sweep keeps the same conclusion. Varying `min_len` from `3`
through `12` leaves `min_len=6` as the best setting at `9823.3` bits; the
nearest alternate is `min_len=5` at `9827.7` bits (`+4.4`). Order-shuffle gross
wins remain order-search diagnostics, not promoted formula changes, unless an
external zero-cost order appears.

The copy-length code reparse improves this front. Replacing gamma length
coding with Rice coding (`k=4`) and reparsing at `min_len=5` yields a new 70/70
roundtrip formula at `9596.5` bits, a `226.8` bit gain over the previous
`9823.3` DP baseline even after charging `5` bits for the Rice parameter. This
is a mechanical generation improvement only; it does not alter row0 or add
plaintext.

The broader length-code grid keeps that formula. Testing `min_len=3..12`,
gamma, delta, unary, and Rice `k=0..10` leaves `rice_k4` / `min_len=5` best at
`9596.5` bits. The nearest non-current model is `rice_k4` / `min_len=4` at
`9600.0` bits (`+3.5`).

Retesting copy-source address ledgers on the Rice-length parse keeps absolute
`source_pos` as the best decodable ledger at `9596.5` bits. Literal-seed
addressing reaches `9549.5` bits only as an undecodable optimistic no-mode
ledger; the best decodable sparse seed-run ledger costs `9607.1` bits, so it
remains an optimistic clue rather than a promoted formula change.

The literal-run length reparse improves the current mechanical frontier.
Keeping copy lengths at Rice `k=4`, source addresses absolute, and `min_len=5`,
but coding literal-run lengths with Rice `k=3`, yields a 70/70 roundtrip
formula at `9545.5` bits. This saves `51.0` bits after charging both Rice
parameters. Digit-shuffle controls remain far worse and sampled book-order
controls do not beat the observed formula.

The joint length-code grid keeps that frontier. Testing `605` combinations of
`min_len=3..7`, copy gamma/delta/Rice `k=0..8`, and literal gamma/delta/Rice
`k=0..8` leaves `rice_k4` copy lengths, `rice_k3` literal-run lengths, and
`min_len=5` best at `9545.5` bits. The nearest alternate is `rice_k4` copy /
`rice_k2` literal at `9552.2` bits (`+6.7`).

The literal-payload model search improves the formula again without changing
the recipe. Replacing uniform decimal payload cost for literal digits with a
decodable adaptive Dirichlet model (`alpha=14`, charged at `7` declaration
bits) yields `9538.0` bits, a `7.5` bit improvement. A static literal histogram
oracle reaches `9513.9` bits but is not promoted because it omits a decodable
table; the charged static table is worse.

Retesting copy-source address ledgers on that current formula keeps absolute
`source_pos` as the best decodable address ledger. Literal-seed addressing
reaches `9478.6` bits only as a no-mode lower bound; the best decodable sparse
seed-run ledger is `9548.7` bits (`+10.7`), so this remains an optimistic clue
rather than a formula promotion.

The literal-to-copy repair search then changes the recipe itself by one local
operation. A literal `972783` in book `8` can be replaced by a prior copy from
source position `370`, reducing the exact current formula from `9538.0` to
`9537.3` bits. A follow-up one-step repair search after applying it finds no
second local improvement.

The post-repair payload alpha sweep keeps the payload parameter unchanged.
After the repair, `alpha=14` remains the best adaptive literal-payload value at
`2608.9` payload-plus-model bits; the nearest alternate, `alpha=13`, costs
`2609.0` bits. No formula is promoted by this parameter sweep.

The post-repair address retest also keeps the formula unchanged. Absolute
`source_pos` remains the best decodable copy-address ledger at `9537.3` bits.
Literal-seed addressing reaches `9472.4` bits only as an undecodable no-mode
lower bound; the best decodable sparse seed-run ledger costs `9548.0` bits.
That preserves literal-seed provenance as an optimistic clue, not a formula.

The compatible pair-repair search closes the immediate combinatorial objection
to the one-step repair. There are `25` single literal-to-copy repair candidates
and `293` compatible pairs. The best pair costs `9538.2` bits, which is `+0.9`
bits worse than the one-step repaired formula, so no two-repair recipe is
promoted.

The book-length ledger search improves the cost accounting without changing the
recipe. Instead of charging each of the 70 book lengths independently with
`gamma(length+1)`, the promoted ledger stores signed Rice residuals from a
declared `anchor=151`, `k=5`. Book-length cost drops from `1030.0` to `566.0`
bits, and the total bound drops from `9537.3` to `9073.3` bits with 70/70
roundtrip. This is a ledger improvement, not a new semantic channel.

The multi-anchor length follow-up rejects the obvious mixture extension. The
best decodable multi-anchor ledger uses `2` clusters at `k=4`, but costs
`581.0` book-length bits after mode and anchor charges. That is `+15.0` bits
worse than the single-anchor `anchor=151`, `k=5` ledger, so no newer length
model is promoted.

The digit-only address compile then uses the new length ledger to remove book
separators from the absolute copy-address space. Copy operations now point into
the previously emitted digit stream rather than the digit-plus-separator stream,
reducing copy-address cost from `3257.3` to `3254.9` bits. The total bound
drops from `9073.3` to `9070.8` bits with 70/70 roundtrip.

The digit-only address-model follow-up keeps that result. Absolute
`source_digit_pos` remains the best decodable ledger at `9070.8` bits.
Literal-seed addressing reaches `9006.2` bits only as an undecodable lower
bound; the best decodable sparse seed-run ledger costs `9081.5` bits.

Retesting local repairs under the digit-only address cost yields one more small
recipe improvement. Literal `57928` in book `13` can be replaced by a prior copy
from digit position `1976`, lowering the bound from `9070.8` to `9070.1` bits.
A follow-up one-step search after applying it finds no second improvement.

The post-repair payload alpha sweep keeps the payload parameter unchanged.
After the digit-address repair, `alpha=14` remains best at `2592.0`
payload-plus-model bits; the nearest alternate, `alpha=13`, costs `2592.1`
bits. No formula is promoted by this parameter sweep.

The post-repair address-model follow-up also keeps the formula unchanged.
Absolute `source_digit_pos` remains the best decodable ledger at `9070.1` bits.
Literal-seed addressing reaches `9005.5` bits only as an undecodable lower
bound; the best decodable sparse seed-run ledger costs `9080.8` bits.

The item-type ledger compile improves the current mechanical bound without
changing the recipe. The previous formula charged one fixed bit for each
literal/copy item tag. Encoding the same `84` literal tags and `281` copy tags
with a declared two-symbol adaptive ledger (`alpha=2`) costs `291.2` bits
instead of `365.0`, lowering the 70/70 roundtrip bound from `9070.1` to
`8996.2` bits. This is a decodable ledger improvement, not a new text channel.

The Markov item-type ledger tightens that same tag stream again. Conditioning
the next item tag on the previous tag, with declared `alpha=1` and one bit for
the first item, costs `272.5` bits instead of the adaptive iid ledger's
`291.2` bits. The total 70/70 roundtrip bound drops from `8996.2` to `8977.6`
bits. The transition counts (`copy->copy=200`, `copy->literal=80`,
`literal->copy=81`, `literal->literal=3`) explain the gain as local item-type
persistence/alternation, not semantics.

The book-start item-type ledger uses the already-declared 70 book boundaries as
a `BOS` context in that same Markov ledger. Books start with copy items much
more often than literal items (`56` versus `14`), and inside-book transitions
remain copy-heavy. This lowers the item-type cost from `272.5` to `267.2` bits
and the total 70/70 bound from `8977.6` to `8972.2` bits without adding a new
order or text channel.

The literal-forces-copy item-type ledger then charges a one-bit deterministic
rule: after a literal item, if the declared book length is not complete, the
next item type is copy. The rule has `71` applications and `0` violations in
the fixed recipe. After charging the rule and `alpha=2`, item-type cost drops
from `267.2` to `261.7` bits, lowering the total bound from `8972.2` to
`8966.7` bits.

The remaining-short item-type ledger adds one more charged deterministic rule:
if fewer than `min_len=5` digits remain in the declared book, a copy item cannot
legally fit, so the type is forced to literal. This rule applies `8` times with
`0` violations. After charging both rules and `alpha=2`, item-type cost drops
from `261.7` to `248.9` bits, lowering the total bound from `8966.7` to
`8953.9` bits.

The remaining-short literal-length compile then removes redundant length bits
from those same `8` forced suffix literals. Because book lengths and `min_len`
are already declared, a forced short suffix literal must consume the remaining
book digits. After charging a one-bit length rule, literal length cost drops by
`31.0` net bits and the total 70/70 bound moves from `8953.9` to `8922.9` bits.

The forced-length literal repair search then retests local literal-to-copy
repairs under that updated cost model. One further repair replaces `65128` in
book `12` with a valid prior copy from digit position `50`, lowering the bound
from `8922.9` to `8922.8` bits. This is a marginal recipe improvement only; the
follow-up one-step repair search after applying it is worse.

The post-forced-repair payload alpha sweep then checks whether that final
payload-stream change requires retuning the adaptive Dirichlet parameter. It
does not: `alpha=14` remains best at `2575.7` payload-plus-model bits, with
`alpha=13` next at `+0.1` bit. No newer formula is promoted.

The post-forced-repair address-model search then retests copy source ledgers on
the active recipe. Literal-seed addressing reaches `8855.5` bits only as an
undecodable no-mode lower bound. The best decodable sparse seed-run ledger
costs `8933.5` bits (`+10.7`), so absolute digit-only `source_digit_pos`
remains the active address ledger.

The post-forced-repair pair search then checks whether two compatible
literal-to-copy repairs improve together even though no single follow-up repair
does. They do not: `22` single candidates yield `227` compatible pairs, and the
best pair remains `+1.6` bits worse than the active formula. The local
literal-to-copy frontier is therefore closed under compatible pairs for this
cost model.

The post-forced-repair triple search extends that local check to three
compatible repairs. It tests `1462` compatible triples from the same `22`
single candidates, and the best triple remains `+2.7` bits worse than the
active formula. No triple recipe is promoted.

The post-forced-repair quad search extends the same local frontier to four
compatible repairs. It tests `6596` compatible quartets, and the best quartet
remains `+3.9` bits worse than the active formula. No quartet recipe is
promoted.

The post-forced-repair quint search extends the local frontier to five
compatible repairs. It tests `22168` compatible quintets, and the best quintet
remains `+5.5` bits worse than the active formula. No quintet recipe is
promoted.

The post-forced-repair sext search extends the local frontier to six
compatible repairs. It tests `57596` compatible sextets, and the best sextet
remains `+7.3` bits worse than the active formula. No sextet recipe is
promoted.

The post-forced-repair sept search extends the local frontier to seven
compatible repairs. It tests `118456` compatible septets, and the best septet
remains `+9.0` bits worse than the active formula. No septet recipe is
promoted.

The post-forced-repair oct search extends the local frontier to eight
compatible repairs. It tests `195806` compatible octets, and the best octet
remains `+11.0` bits worse than the active formula. No octet recipe is
promoted.

The post-forced-repair nonet search extends the local frontier to nine
compatible repairs. It tests `262548` compatible nonets, and the best nonet
remains `+12.9` bits worse than the active formula. No nonet recipe is
promoted.

The post-forced-repair decet search extends the local frontier to ten
compatible repairs. It tests `286858` compatible decets, and the best decet
remains `+15.1` bits worse than the active formula. No decet recipe is
promoted.

The post-forced-repair eleven-repair search extends the local frontier to
eleven compatible repairs. It tests `255476` compatible eleven-repair sets, and
the best set remains `+17.8` bits worse than the active formula. No
eleven-repair recipe is promoted.

The post-forced-repair twelve-repair search extends the local frontier to
twelve compatible repairs. It tests `184756` compatible twelve-repair sets, and
the best set remains `+20.6` bits worse than the active formula. No
twelve-repair recipe is promoted.

The high-order exhaustion pass closes the remaining local frontier under this
cost model. It exactly rescores compatible set sizes `13..19`, checks sizes
`20..22`, and finds no improvement: the best remaining set is size `13` at
`+23.7` bits worse than the active formula, while sizes `20..22` have no
compatible sets.

The literal payload context search then shifts from recipe repair to payload
coding. With the recipe and all ledgers fixed, an adaptive context model that
conditions each literal digit on the previously emitted digit is decodable from
the generated stream and improves the 70/70 bound from `8922.8` to `8842.0`
bits after charged alpha and context-family bits. This is the new strongest
mechanical book-layer generator, with `translation_delta: NONE`.

The context-order sweep then tests longer deterministic previous-emitted-digit
contexts. Order `2` with `alpha=1` is promoted after charged order bits,
lowering the bound again from `8842.0` to `8805.7` bits. Orders `3..5` are
worse after sparsity and declaration cost. This is still payload coding only,
not a semantic or row0-origin claim.

The item-type context-order sweep then retests only the literal/copy item-type
ledger. It preserves the deterministic forced-copy and forced-short-suffix
rules, keeps forced emissions in context history, and codes only unforced item
types. Order `3` with `alpha=2` improves the bound from `8805.7` to `8803.5`
bits after charged order bits. This is a small mechanical ledger improvement
only.

The contextual repair pass then retests local recipe edits under the updated
payload and item-type ledgers. Literal-to-copy repairs do not promote: `22`
candidates are tested and the best remains `+1.0` bit worse. The reverse
direction does promote once: an existing length-`5` copy of `45765` in book
`34` is cheaper as an explicit literal, lowering the bound from `8803.5` to
`8803.1` bits. This is still an exact 70/70 mechanical recipe refinement only.

The post-copy-to-literal local frontier then checks whether another immediate
local edit remains. It does not: after applying the copy-to-literal repair, the
best literal-to-copy edit is `+0.4` bits worse, the best copy-to-literal edit
is `+1.5` bits worse, and the best of `13530` copy-to-literal pairs is `+3.5`
bits worse.

The contextual address-model retest then revisits the largest remaining copy
cost block. Absolute digit-only `source_digit_pos` remains the best decodable
ledger at `8803.1` bits. Literal-seed addressing reaches `8739.3` bits only as
an optimistic no-mode lower bound; once decodable sparse seed-run mode bits are
charged, it costs `8813.8` bits and does not promote.

The post-contextual parameter resweep then retests the declared parameters
after the copy-to-literal repair changes the recipe. Copy length Rice `k=4`,
literal-run length Rice `k=3`, literal-payload context order `2` / `alpha=1`,
and item-type context order `3` / `alpha=2` all remain best after charged
declarations. The current `8803.1` bit formula is therefore retained.

The bounded copy-length compile then improves the cost ledger without changing
the recipe. After a copy source address is decoded, the legal copy length range
is already bounded by the declared remaining book length and the number of
emitted digits available after that source. Coding copy lengths with canonical
truncated binary over that range reduces copy-length bits from `1860.0` to
`1671.0`, lowering the active 70/70 formula from `8803.1` to `8614.1` bits.

The min_len-bounded address compile then applies a smaller bound to absolute
source addresses. Because every copy source must have at least `min_len`
emitted digits available after it, the final `min_len - 1` emitted positions
cannot be legal source starts. Excluding them reduces copy-address bits from
`3264.817` to `3263.751`, lowering the active formula from `8614.133` to
`8613.067` bits.

The minaddr local-frontier pass then retests one-step recipe edits under the
new cost model. A single literal-to-copy edit promotes: literal `11216` in book
`2` becomes a copy from source digit position `225`, lowering the active
formula from `8613.067` to `8611.408` bits. This is still a mechanical recipe
repair only.

The post-minaddr-repair local frontier then repeats the one-step repair test
after `11216` changes the stream. A second literal-to-copy edit promotes:
`45765` in book `34` becomes a copy from source digit position `183`, lowering
the active formula from `8611.408` to `8609.773` bits. This restores that local
copy only under the updated cost model.

The post-repair2 local-frontier pass then closes the immediate one-step edit
space under this cost model. It tests `21` literal-to-copy and `283`
copy-to-literal candidates; the best candidate is copy-to-literal `94343` in
book `26`, still `+0.121` bits worse than the active formula.

The post-repair2 parameter resweep then checks whether the two minaddr local
repairs changed the best declared parameters. They do not: literal Rice `k=3`,
literal-payload context order `2` / `alpha=1`, and item-type context order `3`
/ `alpha=2` all remain best under full rescoring.

The compatible-pair frontier then checks whether two local edits improve
together after the one-step frontier closes. It scores `17663` valid compatible
pairs; the best pair, copy-to-literal `71288` plus `94343`, remains `+0.692`
bits worse than the active formula. This closes the immediate pair frontier
under the current cost model.

The post-repair2 address model search then retests relative, delta, per-book,
mixed same-book, and literal-seed address ledgers against the active
min_len-bounded absolute source address model. The active address ledger remains
the best decodable row at `8609.8` bits. Literal-seed no-mode reaches `8540.4`
bits, but that row is not decodable without source-mode bits, while the sparse
decodable seed-run version costs `8618.8` bits.

The post-repair2 copy-order search then checks whether copy length should be
coded before source address. Pure length-first coding is `+18.295` bits worse.
Picking the cheaper order per copy would be `-3.539` bits cheaper only if the
mode were free, so it remains an optimistic lower bound. The tested decodable
mode ledgers do not beat the active source-address-then-length order.

The post-repair2 adaptive copy-length compile then replaces the uniform
truncated-binary length index with an adaptive global length-index ledger,
restricted to the currently legal length range after the source address is
decoded. With charged declaration bits, `alpha=2` lowers the active mechanical
bound from `8609.773` to `8575.986` bits. This is a copy-length cost refinement
only: recipe, addresses, payload model, item-type model, row0, and semantic
verdict are unchanged.

The post-adaptive-copy-length local frontier then checks whether that new cost
model reopens one-step recipe edits. It does not: the best candidate is
copy-to-literal `45765` in book `34`, still `+1.084` bits worse than the active
adaptive formula. The immediate local recipe frontier is closed again under
the adaptive scorer.

The post-adaptive parameter resweep then checks whether the adaptive copy-length
improvement changes the best declared parameters. It does not: copy-length
`alpha=2`, literal Rice `k=3`, literal-payload context order `2` / `alpha=1`,
and item-type context order `3` / `alpha=2` all remain best under full rescoring.

The post-adaptive pair frontier then tests whether two local recipe edits
improve together after the adaptive scorer closes the one-step frontier. It
scores `17663` valid compatible pairs; the best pair, copy-to-literal `71288`
plus `45765`, remains `+2.516` bits worse than the active adaptive formula.

The post-adaptive address model search retests relative, delta, per-book, mixed
same-book, and literal-seed address ledgers after adaptive copy lengths. The
active min_len-bounded absolute source address ledger remains the best decodable
row at `8576.0` bits. Literal-seed no-mode reaches `8506.6` bits, but it is
still not decodable without source-mode bits.

The post-adaptive copy-order search then retests whether adaptive length should
be coded before source address. Pure length-first adaptive coding is `+13.664`
bits worse. Choosing the cheaper order per copy would be `-3.539` bits cheaper
only if mode bits were free, so it remains an optimistic lower bound. The
decodable mode ledgers do not beat source-address-then-adaptive-length.

The post-adaptive copy-length context search then tests whether the adaptive
length-index prior should be split by simple contexts available before length
decoding. A fixed book-midpoint context is decodable from the declared numeric
book order and lowers the bound from `8575.986` to `8574.407` bits after
charged context declaration bits. Exhaustive single-split search finds larger
component savings, but those rows are not promoted once the split index is
charged.

The post-midpoint local frontier then checks whether the new length context
reopens one-step recipe edits. It does not: the best literal-to-copy repair,
`477090` in book `17`, is still `+1.537` bits worse than the active midpoint
formula. The immediate local literal/copy frontier is closed again.

The post-midpoint parameter resweep then checks whether the new midpoint
context changes the declared parameter frontier. It does: copy-length `alpha=1`
beats the previous `alpha=2`, lowering the active bound from `8574.407` to
`8572.267` bits. Literal-run Rice `k=3`, literal-payload order `2` /
`alpha=1`, and item-type order `3` / `alpha=2` remain fixed.

The post-midpoint alpha1 local frontier then retests one-step recipe edits
again under the promoted `alpha=1` cost. It still closes: the best
literal-to-copy repair, again `477090` in book `17`, is `+0.971` bits worse
than the active formula.

The post-midpoint alpha1 pair frontier then tests whether two compatible local
edits improve together after the one-step frontier closes. It scores `17663`
valid pairs; the best pair, literal-to-copy `60199` in book `3` plus `477090`
in book `17`, is still `+2.501` bits worse. Compatible pairs do not improve the
active formula.

The post-midpoint alpha1 address-model search then revalidates the external
next-formula report's address-ledger recommendation against the current
formula. Literal-seed addressing reaches `8502.9` bits only as an undecodable
no-mode lower bound. The best decodable row remains the active min_len-bounded
absolute source-address ledger at `8572.267` bits.

The post-midpoint alpha1 copy-order search then retests whether decoding copy
length before source address can exploit tighter length-specific address
bounds. It cannot under a decodable ledger: pure length-first is `+12.194`
bits worse, the best no-mode mixed order is `-3.539` bits optimistic-only, and
the best sparse decodable mixed-order ledger is still `+8.979` bits worse.
Source-address-then-length remains active.

The post-midpoint alpha1 copy-length context resweep then checks whether the
midpoint context still holds after `alpha=1` is active. It does. Book quartiles
save only `0.059` component bits and are `+1.941` bits worse after declaration.
The best searched split, book `18`, saves `6.704` component bits but is still
`+2.296` bits worse after charging the split index.

The post-midpoint alpha-by-context grid then checks whether the two midpoint
halves need separate smoothing parameters. The best split-alpha row keeps
first-half `alpha=1` and sets second-half `alpha=2`, saving `1.611` component
bits, but the extra declarations make it `+1.389` bits worse overall. The
shared `alpha=1` midpoint model remains active.

The post-midpoint alpha1 literal-payload context search then checks whether the
remaining literal digits need a book-level payload prior instead of the global
previous-emitted-digit model. They do not under full MDL: book-midpoint payload
context saves `2.251` component bits but is `+1.749` bits worse after
declaration, and the best searched split, book `39`, is `+11.613` bits worse.

The post-midpoint alpha1 top60 triple probe then checks a bounded higher-order
repair surface. It rescored `33588` valid compatible triples among the top
`60` local single-edit candidates. The best bounded triple is still `+3.914`
bits worse. This is evidence against the most plausible triple combinations,
not exhaustive closure of all triples over the `189` local candidates.

The post-midpoint alpha1 item-type context search then finds the next
controlled mechanical improvement. A context based on the current item length
is cheaper but is not decodable before the item contract is known, so it is
recorded only as a lower bound. The best decodable row declares a searched
book split at `6` for the item-type prior, reducing item-type bits from
`238.887` to `227.272` and lowering the full bound from `8572.267` to
`8569.652` bits.

The post-itemctx parameter resweep then retests declared parameters after that
split context is active. Item-type extra-context order `1` with `alpha=2`
reduces item-type bits again to `223.412`, lowering the full bound from
`8569.652` to `8561.792` bits. Literal-run length Rice `k=3`, literal-payload
context order `2` / `alpha=1`, and midpoint copy-length `alpha=1` remain
unchanged.

The post-itemctx_param local frontier then checks whether the changed item-type
prior reopens one-step recipe edits. It does not: `21` literal-to-copy and
`283` copy-to-literal candidates are tested, and the best candidate,
literal-to-copy `60199` in book `3`, is still `+0.957` bits worse. The
post-itemctx_param pair frontier then checks compatible pairs: `17663` valid
pairs are rescored and the best pair remains `+1.809` bits worse.

The post-itemctx_param address-model retest then keeps min_len-bounded absolute
source addresses as the best decodable ledger at `8561.792` bits. Literal-seed
addressing still has the same shape: it reaches `8492.396` bits only as a
no-mode lower bound, while the best sparse decodable seed-run ledger is
`+9.060` bits worse. The post-itemctx_param copy-order retest likewise keeps
source-address-then-length order as the best decodable contract; pure
length-first is `+12.194` bits worse, and the best mixed no-mode row is
`-3.539` bits optimistic-only.

The post-itemctx_param copy-length context resweep then checks whether the
midpoint copy-length context still holds after the item-type parameter change.
It does: the active fixed book-midpoint context remains best at `8561.792`
bits. Book quartiles are `+1.941` bits worse, and the best searched split,
book `18`, is `+2.296` bits worse after charging the split declaration. The
post-itemctx_param context alpha grid also retains shared `alpha=1`; first-half
`alpha=1` plus second-half `alpha=2` saves `1.611` component bits but is still
`+1.389` bits worse after extra alpha declarations.

The post-itemctx_param literal-payload context search then checks whether the
remaining literal digits need a book-level payload prior after the item-type
parameter change. They still do not under full MDL: book-midpoint payload
context saves `2.251` component bits but is `+1.749` bits worse after
declaration, and the best searched split, book `39`, is `+11.613` bits worse.

The broader post-itemctx_param item-type context family search then rescored
`17024` family/order/alpha candidates across global, fixed book buckets,
op-index, remaining-length, and searched single-book split contexts. The active
searched split at book `6`, order `1`, alpha `2` remains best at `8561.792`
bits. The nearest alternate, searched split `9` with the same order and alpha,
is still `+1.335` bits worse.

The joint post-itemctx_param payload/item-type pair sweep then combines the
`77` literal-payload context candidates with the `17024` item-type candidates,
for `1310848` total pairs. The active global payload plus searched item-type
split at book `6`, order `1`, alpha `2` remains best at `8561.792` bits. The
best changed pair is item-type alpha `1` under the same split and global
payload, still `+0.415` bits worse. The best pair with both components changed
uses book-midpoint payload context plus that item-type alpha `1` row and is
`+2.164` bits worse.

The joint post-itemctx_param copy-length/item-type pair sweep then combines
the `79` copy-length context candidates with the `17024` item-type candidates,
for `1344896` total pairs. The active book-midpoint copy-length context plus
searched item-type split at book `6`, order `1`, alpha `2` remains best at
`8561.792` bits. The best changed pair is again item-type alpha `1` under the
same active copy-length context and item-type split, still `+0.415` bits worse.
The best pair with both components changed uses fixed book-quartile copy-length
context plus that item-type alpha `1` row and is `+2.357` bits worse.

The post-itemctx_param payload/copy-length/item-type triple sweep then combines
the `77` literal-payload contexts, `79` copy-length contexts, and `17024`
item-type candidates into `103556992` implied triples. Since all three complete
component frontiers have non-negative minima, the active global payload,
book-midpoint copy-length context, and searched item-type split at book `6`,
order `1`, alpha `2` remains best at `8561.792` bits. The best changed triple
is still the item-type alpha `1` row at `+0.415` bits, and the best triple with
all three components changed is `+4.106` bits worse.

The post-itemctx_param copy-length alpha/item-type pair sweep then combines
the `4097` midpoint alpha-by-context rows with the `17024` item-type candidates,
for `69747328` implied pairs. The active shared copy-length alpha `1` plus
searched item-type split at book `6`, order `1`, alpha `2` remains best at
`8561.792` bits. The best changed pair is still the item-type alpha `1` row at
`+0.415` bits. The best pair with both components changed uses copy-length
alpha `{'first_half': 1, 'second_half': 2}` plus that item-type alpha `1` row
and is `+1.804` bits worse.

The post-itemctx_param copy-length alpha/payload pair sweep then combines the
`4097` midpoint alpha-by-context rows with the `77` literal-payload context
candidates, for `315469` implied pairs. The active shared copy-length alpha `1`
plus global literal-payload model remains best at `8561.792` bits. The best
changed pair is copy-length alpha `{'first_half': 1, 'second_half': 2}` with
global payload, still `+1.389` bits worse. The best pair with both components
changed adds book-midpoint payload context and is `+3.138` bits worse.

The post-itemctx_param copy-alpha/payload/item-type triple sweep then combines
the `4097` midpoint alpha-by-context rows, `77` literal-payload contexts, and
`17024` item-type candidates into `5370544256` implied triples. The active
shared copy-length alpha `1`, global literal-payload model, and searched
item-type split at book `6`, order `1`, alpha `2` remains best at `8561.792`
bits. The best changed triple is still the item-type alpha `1` row at
`+0.415` bits. The best triple with all three components changed uses
copy-length alpha `{'first_half': 1, 'second_half': 2}`, book-midpoint payload,
and item-type alpha `1`, and is `+3.553` bits worse.

The post-itemctx_param copy-length context/shared-alpha resweep then tests the
same `79` copy-length context candidates with each shared `alpha=1..64`, for
`5056` context/alpha rows. The active fixed book-midpoint context with shared
`alpha=1` remains best at `8561.792` bits. The best context change is
book-quartile context with `alpha=1`, still `+1.941` bits worse, and the best
alpha change on the active context is `alpha=2`, `+2.140` bits worse.

The post-itemctx_param literal-payload context/shared-alpha resweep then tests
the same `77` literal-payload context candidates with each shared
`alpha=1..64`, for `4928` context/alpha rows. The active global
previous-emitted-digit payload model with shared `alpha=1` remains best at
`8561.792` bits. The best context change is book-midpoint payload context with
`alpha=1`, still `+1.749` bits worse, and the best alpha change on the active
context is `alpha=2`, `+17.859` bits worse.

The post-itemctx_param copy/payload context-alpha pair search then combines the
`5056` copy-length context/shared-alpha rows with the `4928` literal-payload
context/shared-alpha rows into `24915968` implied pairs. Component minima keep
the active book-midpoint copy-length `alpha=1` plus global payload `alpha=1`
pair best at `8561.792` bits. The best changed pair is the payload
book-midpoint `alpha=1` row at `+1.749` bits, and the best pair with both
components changed is copy-length book-quartile `alpha=1` plus payload
book-midpoint `alpha=1`, `+3.690` bits worse.

The post-itemctx_param copy/payload/item context-alpha triple search then
combines the `5056` copy-length context/shared-alpha rows, `4928`
literal-payload context/shared-alpha rows, and `17024` item-type candidates
into `424169439232` implied triples. Component minima keep the active
book-midpoint copy-length `alpha=1`, global payload `alpha=1`, and item-type
split at book `6`, order `1`, alpha `2` triple best at `8561.792` bits. The
best changed triple is the item-type alpha `1` row at `+0.415` bits, and the
best triple with all three components changed is copy-length book-quartile
`alpha=1`, payload book-midpoint `alpha=1`, and item-type alpha `1`,
`+4.106` bits worse.

The post-itemctx_param address/copy-order pair search then combines the `10`
copy-source address ledger rows with the `5` within-copy order rows into `50`
pairs. The best overall pair is `-72.935` bits, but it is nondecodable because
it combines the literal-seed address no-mode lower bound with the copy-order
no-mode lower bound. The active min_len-bounded absolute address plus
source-first copy order pair remains the best decodable row at `8561.792`
bits. The best changed decodable pair is the sparse run-list copy-order row,
still `+8.979` bits worse; the best decodable pair with both components
changed is `+18.039` bits worse.

The post-itemctx_param address/item-type pair search then combines the `10`
copy-source address rows with the `17024` item-type candidates into `170240`
pairs. The best overall pair is nondecodable because it uses the literal-seed
address no-mode lower bound. The active min_len-bounded absolute address plus
item-type split at book `6`, order `1`, alpha `2` remains best among decodable
rows at `8561.792` bits. The best changed decodable pair is item-type alpha
`1`, `+0.415` bits worse; the best decodable pair with both components changed
is `+9.476` bits worse.

The post-itemctx_param address/payload context-alpha pair search then combines
the `10` copy-source address rows with the `4928` literal-payload context/alpha
rows into `49280` pairs. The best overall pair is nondecodable because it uses
the literal-seed address no-mode lower bound. The active min_len-bounded
absolute address plus global literal-payload `alpha=1` remains best among
decodable rows at `8561.792` bits. The best changed decodable pair is payload
book-midpoint `alpha=1`, `+1.749` bits worse; the best decodable pair with both
components changed is `+10.809` bits worse.

The prequential generation model audit then changes the validation unit. It
does not search another formula. It freezes the then-active `8561.792` bit model as
`compression_bound` and tests learned copy-length, literal-payload, and
item-type components on train/holdout cuts. Prefix-online and prefix-frozen
scoring beat uniform at all cutoffs `10/20/35/50/60`; for example, with `35`
train books and `35` holdout books, learned-component uniform cost is
`1016.319` bits, prefix-online cost is `968.175`, and prefix-frozen cost is
`980.298`. This supports partial predictive structure, but the classification
is `prequential_generation_partial_not_final`: it still does not explain row0
or establish a final authorial generation method.

The prequential order control audit then checks whether the prefix result is
specific to numeric book order. It compares each numeric prefix against `1000`
random same-size train-book sets. Prefix training still beats uniform on every
cutoff, but random train sets usually save more bits; for example, at `35`
train books the numeric prefix saves `48.145` bits online versus uniform, while
random train sets average `165.553` bits saved. The classification is
`prequential_predictive_not_numeric_order_specific`: the learned components are
real distributional evidence, not a promoted numeric-order generation proof.

The prequential component ablation audit then separates robust learned
components from compression-bound detail. The copy-length midpoint context
remains best on both online and frozen prefix holdouts. Literal payload,
however, generalizes better with previous-one-digit context than with the
active previous-two-digit context; item type generalizes better with the
book-6 split alone than with the active split plus previous-item context.
Therefore the `8561.792` code remains the compression bound, but the simpler
holdout winners are the cleaner generation-explanation components.

The simplified generation profile compile then measures those holdout-preferred
components on the full corpus. The profile keeps the same recipe and validates
`70/70` roundtrip, but costs `8613.581` bits, `+51.789` versus the active
compression bound. It is therefore useful as `generation_explanation_profile`,
not as a promoted lower MDL code.

The item-type split-only formula compile then tests the one component from that
profile that also improves the full-corpus code. Keeping the recipe, forced
rules, and item-type declaration charge fixed, split-only item-type coding
validates `70/70` and lowers the active bound from `8561.792` to `8558.667`
bits. This is a mechanical book-generation improvement only; it does not
explain row0 or add semantics.

The item-type split-only alpha resweep then closes the immediate parameter
frontier for that promoted model. `alpha=2` remains best at `8558.667` bits
after charging alpha declaration deltas; `alpha=1` is nearest at `+0.309` bits
worse, and no alternate alpha is promoted.

The item-type/op-shape boundary gate then separates two uses of "type". The
split-only item-type sequence remains a retained generation-profile stream, but
the compact recipe does not need explicit op `type` fields: `text` implies a
literal op, while `source_digit_pos` plus `length` implies a copy op. Removing
`348` explicit type fields preserves `70/70` roundtrip and has `+0.000` bit
delta. This sharpens the recipe dependency ledger without deriving row0 or
adding semantics.

The prequential and row0-origin audit then changes direction away from
compression micro-sweeps. It freezes `8558.667` as the current
`compression_bound`: learned components beat uniform on all prefix
future-suffix splits, but random same-size train-book controls are usually
stronger, so numeric order and final authorial method are not promoted. The
same audit records row0 as still exogenous across manual lookup,
permutation/group, 10x10 grid, order/frequency, external-text, and
workbook/script-artifact hypotheses.

A 2026-06-21 consolidation reruns that direction as a stricter analysis-only
audit: `8558.667` bits is treated as the frozen validation scope, while later
compression-only reductions are not counted as generation evidence. Prefix and
contiguous-block holdouts retain positive learned-component gains versus
uniform baselines, but public-bookcase family holdouts include nonpositive
failures, so the classification is only
`predictive_signal_partial_not_generation_method`. The row0/table result is
unchanged: row0 remains exogenous, and no plaintext or semantic claim is
introduced.
A follow-up family-failure audit decomposes those failures: bookcases `33` and
`8` are copy-only failures dominated by copy-length underperformance, while
bookcase `6` is online-positive but frozen-negative because item-type coding
loses to uniform under frozen counts. This narrows the failure mode without
promoting a final authorial method.
A train-CV component-selector audit then tests whether a train-only fallback
can disable failing components before seeing the held-out family. It cannot:
inner family validation keeps all active components for every public-bookcase
holdout, leaving the same failures. Only a heldout oracle rescues them, so no
component fallback is promoted as a generation rule.
A recipe-externality audit then quantifies the remaining limitation: only
`4285.876` of `8558.667` bits (`50.076%`) are the prequentially scored
components, while `4272.791` bits (`49.924%`) remain fixed recipe or
non-learned ledger. The prequential split scores rows extracted from the full
formula; it does not discover held-out literal/copy segmentation or copy
source addresses.
A recipe-reparse evidence matrix then checks whether that fixed-recipe
externality is total. It is not: deterministic reparse roundtrips all
prefix-held-out suffixes, beats the active suffix recipes under frozen counts,
and beats content controls. The stronger order claim remains partial, because a
focused cutoff-`50` train-set control lets random same-size training inventories
match or exceed the numeric prefix (`p=0.1538`).
A multi-cutoff train-set control then repeats that check at cutoffs `35/50/60`:
numeric prefix beats the random-train mean and max at `2/3` cutoffs, but loses
at cutoff `60`. That sharpens the boundary: recipe reparsing is mechanically
predictive, while numeric order is still not promoted as authorial proof.
A public-bookcase family holdout then checks the family axis where
component-only scoring failed. Deterministic reparse beats raw digits in
`19/19` families and in `3/3` component-failure families, but beats the active
frozen recipe in only `14/19`; the recipe signal is therefore stronger, while
the active full-corpus recipe still has local wins.
A family-loss decomposition then localizes those five local wins: all five
held-out families still roundtrip and beat raw digit coding, four losses are
dominated by copy-address bits with identical literal/copy inventory, and one
family is an exact tie. This explains the residual family gap as local ledger
overhead against an already-seen active recipe, not as row0 or semantic
evidence.
A same-coordinate address-space audit then corrects that comparison. When the
active recipe is repriced in the same heldout-after-train coordinate system as
the reparse, all five active recipes still roundtrip and the mean copy-address
delta drops from `4.667` bits to approximately `0.000` bits. The apparent
active local wins were therefore coordinate artifacts, not real family-reparse
failures.
Applying that correction to all public-bookcase families gives the cleaner
scoreboard: reparse beats raw digits in `19/19` families and beats or ties the
active family recipe in `19/19` after address correction, versus `15/19` before
correction. The mean reparse-minus-active gap improves from `-139.959` to
`-161.381` bits. This strengthens predictive recipe validation, but still does
not derive row0 or promote a final authorial method.
A no-test-carryover variant then removes cross-book carryover inside each
held-out family. Each held-out book is parsed from the training-complement
inventory alone; it still roundtrips `19/19` families and beats raw digit
coding in `19/19`, with mean gain `1054.570` bits. The family signal therefore
does not depend on held-out books feeding other held-out books.
A leave-one-book-out no-self audit then pushes the same check to singleton
granularity. Each book is held out and reparsed from the other `69` books only;
all `70/70` roundtrip and beat raw digit coding, with mean gain `469.307` bits
and minimum gain `96.055` bits. This validates item-level mechanical
redundancy but remains complement-inventory evidence, not an authorial order or
row0-origin proof.
A singleton source-attribution audit then maps the dependency graph behind that
result: `189` copy items produce `11062` copied digits, with mean `2.171`
distinct source books per target and mean top-source share `0.772`. It also
exposes a caveat rather than hiding it: `3001` copied digits (`0.271289`) cross
artificial source-book boundaries in the concatenated complement inventory,
while current-prefix copying is tiny (`8` digits, share `0.000723`).
A book-bounded singleton source audit then removes that caveat as a dependency:
forbidding copy sources from crossing source-book boundaries still gives
`70/70` roundtrip and `70/70` raw wins. Mean gain remains `464.898` bits, with
only `4.409` mean bits of penalty versus the unbounded singleton parser.
A family-excluded singleton source audit then removes a different possible
dependency: for books with a known public-bookcase family label, all same-family
books are removed from frozen train counts and copy sources. The signal still
roundtrips `70/70`, beats raw in `70/70`, and beats raw in `46/46`
family-labeled books, with mean gain `460.251` bits. Same-family source
memorization is therefore not required for the singleton signal, although the
result remains mechanical redundancy evidence rather than a final authorial
method.
An online prefix book frontier audit then decomposes the deterministic online
formula at target-book granularity. Under the previous-books-only constraint,
the book-bounded variant roundtrips `70/70`, beats raw in `69/70`, and the only
failure is the cold-start book `0`, before any prior-book inventory exists.
After that bootstrap, it beats raw in `69/69`; cumulative book-bounded gain
crosses break-even at book `2`, with mean gain `419.761` bits. This is the
strongest current sequential generation frontier, still without deriving row0
or plaintext.
An online bootstrap seed-policy audit then tests the remaining cold-start
exception directly. Book `0` costs `488.857` bits under the online parser but
`478.358` bits as a raw uniform seed, so one explicit raw seed saves `10.499`
bits and changes the local ledger to `70/70` wins-or-ties against raw (`69/70`
strict wins). This closes the local bootstrap failure as accounting, not as a
new promoted bound or authorial proof.
A seeded online formula rescore audit then checks that boundary against the
complete formula scorer. Promotion is rejected: the existing online formula is
`8343.062` bits, replacing book `0` with one literal seed gives `8344.041`
bits (`+0.979`), and the book-bounded seeded formula gives `8648.260` bits
(`+305.198`). The seed remains a bootstrap explanation, not a better full
formula.
A seeded rescore loss-decomposition audit explains the small `+0.979` failure:
the seeded formula saves `36.842` non-payload bits, but the complete scorer
adds `37.821` literal-payload bits. The local seed saving is therefore real as
bootstrap accounting, but insufficient as formula compression.
A seed exception signal-cost audit closes the remaining escape hatch: even a
zero-cost deterministic fallback is `+0.979` bits worse than the online formula,
a one-book exception index is `+7.108`, and promotion would require negative
descriptor cost (`< -0.979` bits). The book-0 seed exception is therefore
closed as a formula-promotion path.
A row0 requirement-matrix follow-up then normalizes the origin side of the
same audit: manual lookup, permutation/group, 10x10 grid, order/frequency,
external text, and workbook/script artifact hypotheses all have explicit
algorithm, cost, coverage, contradiction, and control entries. Promoted
row0-origin formulas remain `0`, so the acceptable negative result is retained:
the origin of row0 continues exogenous under current evidence.

The prequential recipe reparse audit then tests the remaining recipe
dependency. With only train-prefix component counts frozen, a deterministic LZ
parser roundtrips every future suffix and beats the active full-corpus recipe
under the same frozen counts on all five cutoffs. This strengthens the
mechanical copy/reference explanation, but it remains split-specific analysis;
it does not lower the full-corpus `compression_bound` or derive row0.

The recipe-reparse control audit then tests whether this is generic LZ behavior.
At cutoffs `20/35/50`, random same-length, per-book-shuffled, and suffix-pool
shuffled test books all have negative gain versus raw digits, while the real
suffixes retain large positive gains. This upgrades the result from
component-only validation to controlled predictive recipe evidence, still
without changing the bound or making a semantic claim.

The train-set control then checks whether that predictive recipe evidence is
specific to numeric prefix order. At focused cutoff `50`, the numeric prefix
beats the random train-set mean, but one random inventory exceeds it
(`p(random >= observed)=0.1538`). The copy/reference mechanism remains
predictive; numeric order is not promoted as an authorial generation order.

The online deterministic reparse compile then applies the same parser to the
full corpus as a deterministic formula. It roundtrips `70/70` and lowers the
bound from `8558.667` to `8343.062` bits, but it is still mechanical only:
row0 origin and semantics are unchanged.

The online reparse order-control audit then checks whether this is arbitrary
book-order overfitting. Numeric order remains best against reverse, parity,
length-derived, and 6 seeded random orders; the best random raw order is still
`+188.584` bits worse before charging `log2(70!)` for arbitrary order.

The online formula recipe-prune audit then separates representation artifacts
from required recipe dependencies. Book `length` and copy `target_start` are
derivable; removing them in-memory preserves `8343.062` bits and `70/70`, while
literal payload plus copy source/length fields remain required declarations.
The canonical online recipe compile materializes that stripped projection as
the compact current formula representation, without changing the bound.
The literal-length-derived recipe compile then removes literal op `length` as
an independent field, because it is derived from literal `text`; copy `length`
remains declared because copied text is not stored in the operation.
The op-type-derived recipe compile then removes op `type` as an independent
field: `text` implies literal, while `source_digit_pos` plus `length` implies
copy. Literal text, copy source, and copy length are now the remaining
operation-level recipe dependencies.
The recipe representation dependency gate consolidates those compiles: `766`
independent recipe fields are derivable with `+0.000` bit delta and `70/70`,
while literal text, copy source, and copy length remain declared dependencies.
The item-type/op-shape boundary gate keeps this compatible with the earlier
item-type split-only result: item-type sequence modeling remains retained, but
compact-recipe op `type` fields are representation artifacts.
The copy-source canonicality audit then checks whether those remaining source
fields are arbitrary. All 261 copy sources are the earliest legal occurrence of
the copied chunk at the declared length; only 123 are unique, so this is an
encoder-side canonicality result, not a decoder-side source removal.
The source canonicality decodability gate then makes that boundary explicit:
the earliest-source rule depends on the future target chunk, `138/261` source
choices remain ambiguous at the declared length, and the copy-source dependency
is not removed. The current decodable representation remains the
default/exception source ledger.
A control addendum then compares that rule with alternatives: latest occurrence
matches only `123/261`, previous-source-plus-length only `5/261`, and uniform
random candidate choice would expect `169.473` hits (`log2 P(all earliest)
=-236.596`).
The source-selection derivation boundary gate then consolidates the negative
side: earliest-source canonicality is complete, but it depends on future target
text; backward-distance source coding is `+25.551` bits worse and loses all
prefix splits, and the best state-free default is still `+15.186` bits worse.
Copy source is therefore canonical but still declared.
The copy-length default decodability audit then tests the remaining copy-length
dependency. The high-coverage target-max rule matches `238/261` copies but is
encoder-only because it requires future target digits. A decodable
`decoder_max_possible` default plus adaptive exception ledger lowers
copy-length cost from `1485.689` to `1348.806` bits after an explicit `8` bit
declaration delta, promoting the mechanical bound to `8206.178` bits. Copy
length is remodeled, not eliminated; row0 and semantics remain unchanged.
The copy-length derivation boundary gate then makes that limit explicit:
target-max matches `238/261` copies but is encoder-only, the decodable
max-possible model has `60` defaults and `201` exceptions, midpoint context
generalizes, and the compact recipe still declares `261` copy lengths.
The copy-source default decodability audit then tests the largest remaining
declared component. A previous-source-plus-length default is decodable but only
matches `5/261` copy sources; combined with a global adaptive exception-source
stream and a charged `12` bit declaration delta, it lowers copy-address cost
from `3031.700` to `3002.838` bits and promotes the mechanical bound to
`8177.317` bits. Copy source is remodeled, not eliminated.
The default/exception prequential validation audit then tests those two
promotions under holdout. They retain positive online gains on every prefix
future-suffix split and, after fixing train-count freezing, positive frozen
gains on every prefix split (`min frozen aggregate=50.303` bits). Family
holdouts still include nonpositive failures, so this remains prefix-frozen
partial component evidence rather than a final generation method. A
component-profile compile then records `8177.317` bits as both the active
`compression_bound` and the prefix-frozen generation profile for this
default/exception layer. The generation claim remains partial because
family/bookcase holdouts still fail.
The copy-source distance audit then tests a decodable backward-distance source
encoding. It is rejected: the distance default/exception replacement is
`+25.551` bits worse than the active absolute-source default/exception model.
The current literal-payload profile audit then retests an older simplification
claim on the updated recipe. Literal payload order-1 no longer qualifies for
the current profile: it is `+95.968` bits on the full corpus and `+28.609`
bits worse in aggregate frozen prefix tests, despite winning cutoffs
`20/35/50`. The current profile therefore keeps order-2.
The current active prequential profile audit then consolidates all learned
streams in the then-active `8177.317` bit formula: copy length, copy source, literal
payload, and item type. These streams account for `7157.317` bits (`87.526%`)
and beat uniform on every tested prefix, contiguous-block, and public-bookcase
family holdout; the weakest family frozen gain is still `6.269` bits. Random
same-size train controls are usually stronger than numeric prefixes, so this
strengthens component-level predictive validation without proving recipe
discovery or authorial book order.
The current active profile boundary gate then records the same conclusion as a
single prequential-side decision: the `8177.317`-bit active profile is retained,
but exact active reparse is still blocked by previous-copy source/length state
and the best state-free replacement is `+15.186` bits worse.
The copy-source state compression gate then sharpens that blocker: the source
default only needs `previous_copy_end`, so the previous `(source, length)` pair
can be compressed to one scalar without changing default/exception
classification. The aggregate candidate-state proxy falls from `969111171` to
`26758611` (`97.239%` reduction), but no complete active parser is promoted.
The active-reparse feasibility follow-up then shows what this buys: every
tested book-level `previous_copy_end` source-state proxy is below `1,000,000`,
and cutoff `60` has `9/10` books below `250,000`. This makes a future
book-local active-source prototype plausible by proxy, but it still does not
solve the full active objective, adaptive counts, tie-breaking, copy source
selection, copy length declaration, literal payload, or item-type ledger.
The current-formula dependency scoreboard then re-counts the latest
source-substitution formula directly: it roundtrips `70/70` with `348` ops,
`87` literal payload fields, `261` copy-source fields, and `261` copy-length
fields still declared. A source-length joint derivability audit then checks
whether those two copy dependencies become simpler as a pair. They do not. The
latest source substitutions reduce the earlier all-earliest source pattern from
`261/261` to `251/261`, showing that the last compression gains traded away a
piece of source canonicality. Joint earliest+target-max still covers `230/261`
copy events, but it is encoder-oracle only because it needs future target text.
The decoder-valid declared-source+decoder-max rule covers only `60/261`, and a
state-only previous-end+decoder-max rule covers only `1/261`. Source and copy
length therefore remain declared; the next mainline mechanical test is still a
structural decoder-known source/length parser or objective. Literal payload and
item type are downstream unless that parser changes available copy choices.
A follow-up canonicality tradeoff audit prices the cleaner source profile
directly. Restoring all `10` non-earliest current sources to their earliest
legal occurrence raises the current total from `8160.825608` to `8177.316653`
bits (`+16.491045`). The current formula remains the lower compression bound,
while the all-earliest variant is the cleaner generation-explanation profile,
not a promoted bound.
The copy-length side then gets the same segmentation treatment. The target-max
rule matches `238/261` copy events, but all `23` exceptions enter exactly one
following operation and stop inside it; they absorb `0` complete following ops
and reach book end `0` times. The exceptions are therefore resegmentation
boundaries, not scalar length-default noise. Copy-length progress now requires
a joint segmentation/source/length parser.
A local target-max resegmentation candidate audit then tests that rewrite
directly: extend the copy to target-max and trim the following operation. It
finds `42/46` valid candidates and `5` proxy improvements. The best proxy
candidate is book `9` op `0` in `preserve_next_mode`, with delta
`-2.059513` bits. This is not a promoted bound because the candidate total is
a compatible-component proxy; promotion requires exact scoring under the current
source-substitution ledger or a joint reparse objective.
A formula gate then runs that exact scoring step. It reproduces the current
`8160.825608`-bit bound and promotes the same book `9` op `0`
`preserve_next_mode` resegmentation, lowering the bound to `8158.766094` bits
for a `+2.059513`-bit gain. The gain is a mechanical compression-bound update
only; `row0` origin, plaintext, and semantics remain unchanged.
A second exact pass retests the remaining compatible target-max rewrites after
that promotion. It skips the stale exception already changed by gate 53, tests
`44` candidates, finds `40` valid and `4` improving, and promotes book `2` op
`9` in `preserve_next_mode` with slack `1`. That lowers the bound again from
`8158.766094` to `8157.065654` bits, for a `+1.700440`-bit gain. This is
still a mechanical compression-bound update only; `row0` origin, plaintext,
and semantics remain unchanged.
A saturation gate then continues the exact greedy target-max frontier. It
promotes two more positive passes, book `56` op `8` and book `51` op `0`,
and reduces the bound from `8157.065654` to `8156.050355` bits. The final
frontier tests `38` candidates, with `34` valid and `0` exact improvements.
This closes the local target-max resegmentation family under the current
scorer, but it is still not a row0 derivation, plaintext claim, or final
authorial method.
Rerunning the exact same-chunk source-substitution frontier after that
resegmentation finds a microscopic pair gain: book `46` op `2` and book `47`
op `0` move the bound from `8156.050355` to `8156.050167` bits
(`+0.000188`). This is compression-bound bookkeeping after a representation
change, not stronger generation evidence.
A second post-target-max source pass finds another microscopic pair, both in
book `49`, and moves the bound to `8156.049986` bits (`+0.000181`). This
confirms that the reopened source frontier is now back in micro-sweep territory.
A stop audit then freezes that post-target-max source path as non-mainline:
the two passes sum to only `0.000369` bits, while selector-cost sanity checks
dominate by `32.244` bits. No third post-target-max source pass is run.
The active-formula dependency refresh then compares this current formula with
the gate-48 formula: the bound is `4.775621` bits lower, but declared recipe
dependencies remain unchanged at `609` fields. The only count-level payload
shift is one digit from literal payload to copied payload, so the source/length
explanation gap is not reduced.
A source/length joint refresh confirms the same boundary: active target-max
length hits rise from `238/261` to `242/261`, but decoder-valid joint rules are
unchanged (`60/261` declared-source+decoder-max, `28/261`
unique-source+decoder-max, `1/261` previous-end+decoder-max). This keeps source
and length as declared dependencies rather than derived generation rules.
The active copy-length exception topology then narrows the residual length
frontier: target-max exceptions drop from `23` to `19` and slack digits drop
from `128` to `115`, but all `19` remaining exceptions still enter exactly one
following operation and stop inside it. This is still a joint segmentation
problem, not a scalar length-default problem.
The residual target-max resegmentation gate then exact-scores all `38` local
extend-and-trim rewrites for those `19` active exceptions. `34` candidates are
valid, `0` improve the active bound, and the best valid rewrite is still
`-0.000163` bits worse. This closes the remaining local target-max frontier
under the active exact scorer.
The active exception stop-rule separability gate then tests whether a simple
single-feature or pairwise-conjunction rule can identify those residual
boundaries across all `261` copy events. It finds `0` exact separators; the
best rule is target-adjacent and not decoder-valid, with TP/FP/FN `11/53/8`,
F1 `0.265060`, and permutation-control `p=0.160000`. The residual copy-length
boundary therefore still needs richer nonlocal parser state rather than another
local stop heuristic.
The active exception finite-state model gate then tests a slightly richer
family: `231` KT-coded context models over online decoder-valid features. The
best model uses only `source_previous_end` and costs `112.749463` bits after
descriptor cost, which is `+17.943077` bits worse than the explicit
exception-list baseline (`94.806385` bits), with permutation `p=0.638000`.
Small finite-state context is therefore not a controlled replacement for the
remaining exception list.
The partial-boundary shift gate then tests the local-window case left open by
the full target-max rewrite: all positive shifts smaller than or equal to
target-max inside the same two-operation window. It finds `2/229` exact-scored
improvements. The promotion gate materializes the best one, book `10` op `0`
in `preserve_next_mode` with delta `3` of slack `72`, lowering the mechanical
bound from `8156.049986` to `8155.261037` bits with `70/70` roundtrip. The
gain is source-ledger driven (`copy_source_bits -0.997536`, `copy_length_bits +0.208587`)
and changes neither `row0` origin nor semantics.
A second partial-boundary pass then promotes book `46` op `1`, also in
`preserve_next_mode`, with delta `1` of slack `3`. It lowers the bound again
from `8155.261037` to `8154.676268` bits with `70/70` roundtrip. The gain is
copy-length-ledger driven (`copy_length_bits -0.584963`, `copy_source_bits +0.000194`).
A saturation gate then tests `221` remaining partial-shift
candidates, finds `0` improvements, and leaves the best valid remaining shift
`-0.000163` bits worse. This closes the local partial-shift family at the
current scorer.
A cutoff-60 source-state prototype then executes the cheaper next step by
repricing deterministic reparse recipes with the active `previous_copy_end`
source ledger. It roundtrips `10/10` held-out books, beats raw digit coding in
`10/10`, and is `-10.241` aggregate bits versus uniform-address reparse, but
only `4/10` books improve individually and no source-state recipe
reoptimization is promoted.
The multi-cutoff source-state reprice gate then repeats the same test at
cutoffs `10/20/35/50/60`. All cutoffs roundtrip, every held-out book remains
positive against raw digit coding, and `5/5` cutoffs beat uniform-address
reparse in aggregate, totaling `-112.968` bits. This validates the
`previous_copy_end` source ledger over reparsed recipes, but it is still
repricing only rather than source-state-aware recipe discovery.
A fixed-segmentation source-choice optimizer then closes the simplest local
improvement path: changing only copy source positions while preserving copied
chunks and copy lengths changes `0/514` sources and gives `+0.000` bits versus
the repriced ledger. Future source-state gains must therefore come from
segmentation, copy-length, or global path-state optimization rather than local
source substitution.
A global fixed-segmentation source-path optimizer then confirms that the
remaining value is path-state rather than local. The exact DP changes `10/514`
sources, improves the repriced ledger by `-42.359` bits, beats repricing in
`5/5` cutoffs, and uses max state count `14`. Segmentation and copy lengths
remain fixed, so this is still a partial optimizer rather than a complete
active parser.
The full-corpus source-path formula gate then checks whether that path-state
signal survives the real adaptive source-stream score. It does: changing
`2/261` same-chunk source positions lowers copy-source cost from `3002.838` to
`2987.933` bits and moves the active fixed-recipe bound from `8177.317` to
`8162.412` bits. The recipe segmentation and copy lengths remain fixed, so
this improves the compression bound without proving complete parser discovery.
The full-corpus source-substitution frontier then exhaustively checks all
single and pair same-chunk legal source substitutions under the real adaptive
source score. It searches `376` singles and `69849` pairs; the best pair changes
book `7` op `1` and book `14` op `2`, lowering the bound from `8162.412` to
`8160.827` bits. Triples and higher-order source substitutions remain
unsearched, and segmentation/copy lengths remain fixed.
A second pass over the same single/pair frontier on the promoted formula finds
only a microscopic gain: book `24` op `0` and book `49` op `6` lower the bound
from `8160.827092` to `8160.826421` bits. This is a compression-bound update,
not stronger generation evidence.
A third pass still finds a positive pair, but it is smaller again: book `34`
op `6` and book `36` op `1` lower the bound from `8160.826421` to
`8160.825917` bits. This reinforces local source-frontier saturation rather
than providing new generation evidence.
A fourth pass still finds a positive pair, but it is smaller again: book `28`
op `4` and book `56` op `5` lower the bound from `8160.825917` to
`8160.825608` bits. This is compression-bound bookkeeping and local
source-frontier saturation, not new generation evidence.
The follow-up source-substitution saturation audit makes that stop rule
explicit: the last three same-chunk local passes sum to only `0.001484` bits,
the fourth-pass positive-pair fraction falls to `0.007287`, and a minimum
pair-selector floor of `16.092` bits dwarfs the latest unpriced gain. Repeated
local source micro-sweeps are therefore frozen as no longer mainline; progress
now requires a structural source/length derivation, holdout-predictive parser
improvement, or row0-origin evidence.
The active reparse state-boundary audit then localizes the recipe-discovery
blocker. The current copy-source default depends on the previous copy source
plus previous copy length, so exact active reparse must carry
`(book_pos, previous_item, previous_copy_source, previous_copy_length)` rather
than the old `(book_pos, previous_item)` state. The largest cutoff-10 state
proxy is `302879952`, and the max book-level multiplier is `38968.0`; no active
reparse parser is promoted yet.
The copy-source state-free default audit then tests whether that state can be
removed by replacing the active source default with decoder-computable defaults
based on emitted length, book position, or current copy length. The best
state-free rule is `state_free_back_current_length`, but it is still `+15.186`
bits worse on the full corpus and worse in every prefix frozen split, so the
path-dependent source state remains the current implementation boundary.
A source-state dependency gate then consolidates that boundary with the
canonicality result: earliest-source canonicality is encoder-side only, the
active reparse state remains
`(book_pos, previous_item, previous_copy_source, previous_copy_length)`, and
state-free defaults lose `5/5` prefix-frozen checks. No compression bound or
generation-method claim is promoted.
The copy-length midpoint context audit then checks whether the active
`book_id < 35` split is removable or merely posthoc. It is retained as
supported context: midpoint beats global by `13.839` stream bits, ranks second
among all 69 one-cut boundaries, beats global in every prefix frozen split,
and passes book-id permutation controls (`p=0.0033`). The searched cutoff `37`
is not promoted because it gains only `0.256` bits over the natural midpoint.
A prequential-side gate now records the same result as component validation:
the midpoint context generalizes, while the searched cutoff remains rejected as
ad-hoc local tuning rather than a new generation formula.
The literal copy availability boundary audit then narrows the remaining
literal-payload externality. `73/87` literal starts have no legal `min_len`
copy candidate, covering `788/857` literal digits at item level; at digit
granularity, `760/857` literal digits are forced by copy unavailability. The
residual parser frontier is localized to `14` literal starts and `97` literal
digit positions where a copy candidate exists but the cost parser chose
literal text.
A prequential-side literal availability gate consolidates the next checks:
`74` in-literal repair candidates and `465` cross-op candidates are all worse,
with best deltas `+1.180` and `+0.027` bits. Literal externality is reduced,
not removed.
The optional literal copy repair frontier then tests the simplest repair family
for that residual set: replacing a prefix of one optional literal run with a
legal prior copy. It scores `74` candidates across `5` eligible starts under
the full active ledger; no candidate improves, and the best remains `+1.180`
bits worse. Broader repairs crossing operation boundaries remain a separate
frontier.
The online order frontier controls then test the per-book online-prefix
frontier against the same named and random order controls used by the aggregate
order audit. Numeric order still has `69/69` after-bootstrap raw wins, but this
criterion is not unique: `10/11` tested orders also pass, including `6/6`
seeded random orders, and `random_04` beats numeric by `+0.549` bits in mean
after-bootstrap gain and `+61.452` bits in total gain. This keeps the online
frontier as predictive-parser evidence while rejecting the stronger claim that
the per-book frontier proves numeric order.
The order frontier promotion gate then reconciles that local metric with the
full formula ledger. The local frontier winner `random_04` is still `+188.584`
bits worse than numeric under the complete online formula before order cost and
`+521.038` bits worse after descriptor cost. No tested non-numeric order can
promote under a nonnegative descriptor, so the frontier metric is demoted from
promotion score to diagnostic control.
The cross-op optional literal copy frontier then tests that broader local
family. It permits a replacement copy to cross the literal boundary and consume
following operations before trimming the remaining recipe. It scores `465`
valid candidates; none improves, and the best is only `+0.027` bits worse than
active, so the active parser remains retained for this local frontier.
The cross-op near-tie decomposition then checks that this tiny loss is not a
rounding artifact. The best candidate saves `4.000` literal-structure bits,
`7.431` payload bits, and `1.417` item-type bits, but pays `1.639` copy-length
bits and `11.237` copy-source bits. The near miss is source-ledger dominated
and remains unpromoted.
The cross-op source break-even audit then quantifies the oracle boundary. The
candidate source is the earliest of two full-length occurrences, and a
source-free oracle would improve by `11.209` bits, but the active source ledger
is `0.027` bits above break-even. This remains an encoder-side clue, not a
decoder-side source derivation.
The copy-source structural context audit then tests whether ordinary mechanical
contexts reduce that source ledger. They do not: book-half, length bucket,
exact length, book-position bucket, and combined contexts all worsen the global
exception prior. Book-half is the best non-global context at `+5.872` bits and
is worse in every prefix-frozen split.
The source blocker structural context gate then folds the near-tie and source
context audits into one promotion test. The cross-op candidate is only `+0.027`
bits worse than active, and a source-free oracle would be `-11.209` bits, but
that oracle is non-decodable. The best decodable simple context, book-half, is
`+5.872` bits worse than the global source prior and loses all `5/5`
prefix-frozen checks. Simple declared source contexts are therefore closed as a
rescue path for this near tie.
The literal-payload default decodability audit then tests whether the largest
remaining digit stream can use a modal default plus exceptions. It cannot:
the active categorical previous-emitted-digit order-2 model remains best, and
the best default/exception candidate is `+38.049` bits worse. No
literal-payload fallback is promoted.
The literal-payload structural context audit then tests whether literal-run
offset, run-length bucket, book half/parity, or bounded combinations with
`prev2` improve payload coding. They all over-split the stream; the active
`prev2` categorical model remains best.
The literal-payload model gate then folds the availability/default/structural
checks together after forced literals are separated. Order-1 loses by
`+95.968` bits on the full corpus and by `+47.346` / `+28.609` bits in
aggregate online/frozen prefix totals; the best modal default/exception
candidate is `+38.049` bits worse and the best non-active structural context
is `+19.159` bits worse. The result retains the active order-2 payload
dependency; it does not promote a new bound or a generation method.

The row0 origin frontier audit then indexes the existing table-origin tests
directly instead of tuning the book compressor again. Matrix generators, pair
rule covers, the `6<->9` orbit, tape features, low-rank factors, structural
exception/render layers, K5 and `5x2` eye models, and hierarchical provenance
still produce no charged, controlled, holdout-capable pair-label formula. The
classification is `row0_origin_frontier_saturated_current_corpus`: row0 origin
remains open, but broad current-corpus brute force is no longer the mainline.
The row0 parallel provenance bridge then imports the independent row0-origin
front. It traces local workbook/import/reconstruction/audit layers, but
CipSoft origin remains untraced. Worksheet anchors have a nominal `54.178` bit
lookup reduction, but after explicit pair+label costs they are `-11.852` bits
versus lookup; rare-singleton anchors net to `0.000` bits after paying label
data. Row0 therefore remains a substrate assumed by the book generator, not a
derived component of the generator.

The same provenance does not solve the unresolved pair table. The
hierarchical-provenance audit derived 31 features per unordered pair from
book operations, tape component references, inventory self-references,
omitted-zero rendering, and canonical token positions. The best stump was
`diff <= 4.5`, with only `16/55` hits, `-196.1` rough bits versus lookup, and
inventory-preserving hit control `p=0.4194`. The best order-fill diagnostic
reached `11/55` (`p=0.8816`). Therefore the hierarchical formula improves
book generation, not row0 pair-cell placement.

## H-AUTH / H-GEN Status

| ID | Status |
|---|---|
| H-AUTH1 | `best_design_model_no_intent_claim` |
| H-AUTH2 | `plausible_mechanism_frame` |
| H-AUTH3 | `plausible_design_interpretation` |
| H-GEN1 | `supermodule_not_promoted` |
| H-GEN2 | `weak_topology_module_signal` |
| H-GEN3 | `candidate_compiled_in_this_front` |
| H-GEN3B | `controlled_mechanical_improvement_no_semantics` |
| H-GEN3C | `controlled_inventory_reuse_order_not_promoted` |
| H-GEN3D | `hierarchical_reference_formula_roundtrips_no_semantics` |
| H-GEN3E | `controlled_sequential_lz_book_formula` |
| H-GEN3F | `order_search_not_promoted_after_permutation_cost` |
| H-GEN3G | `controlled_sequential_lz_run_literal_formula` |
| H-GEN3H | `controlled_sequential_lz_dp_parse_formula` |
| H-GEN3I | `copy_source_address_absolute_retained` |
| H-GEN3J | `copy_graph_literal_seed_atlas_compiled_no_formula_promotion` |
| H-GEN3K | `structured_physical_order_not_better_than_numeric` |
| H-GEN3L | `literal_seed_address_optimistic_only_not_promoted` |
| H-GEN3M | `literal_seed_grouped_mode_optimistic_only_not_promoted` |
| H-GEN3N | `copy_hub_macro_model_not_promoted` |
| H-GEN3O | `restricted_hybrid_vocabulary_not_promoted` |
| H-GEN3P | `dp_min_len_sweep_retains_min_len_6` |
| H-GEN3Q | `controlled_copy_length_code_improvement` |
| H-GEN3R | `copy_length_grid_retains_rice_k4_min_len_5` |
| H-GEN3S | `rice_copy_address_optimistic_only_not_promoted` |
| H-GEN3T | `controlled_literal_length_code_improvement` |
| H-GEN3U | `joint_length_grid_retains_rice_k4_literal_rice_k3_min_len_5` |
| H-GEN3V | `controlled_literal_payload_adaptive_improvement` |
| H-GEN3W | `current_formula_address_optimistic_only_not_promoted` |
| H-GEN3X | `controlled_literal_to_copy_single_repair_improvement` |
| H-GEN3Y | `post_repair_payload_alpha_retains_14` |
| H-GEN3Z | `post_repair_address_optimistic_only_not_promoted` |
| H-GEN3AA | `literal_to_copy_pair_repair_not_promoted` |
| H-GEN3AB | `controlled_book_length_ledger_improvement` |
| H-GEN3AC | `multi_anchor_book_length_ledger_not_promoted` |
| H-GEN3AD | `controlled_digit_only_copy_address_improvement` |
| H-GEN3AE | `digit_address_optimistic_only_not_promoted` |
| H-GEN3AF | `controlled_digit_address_literal_repair_improvement` |
| H-GEN3AG | `post_digit_repair_payload_alpha_retains_14` |
| H-GEN3AH | `post_digit_repair_address_optimistic_only_not_promoted` |
| H-GEN3AI | `controlled_item_type_ledger_improvement` |
| H-GEN3AJ | `controlled_markov_item_type_ledger_improvement` |
| H-GEN3AK | `controlled_book_start_item_type_ledger_improvement` |
| H-GEN3AL | `controlled_literal_forces_copy_type_ledger_improvement` |
| H-GEN3AM | `controlled_remaining_short_forces_literal_type_ledger_improvement` |
| H-GEN3AN | `controlled_remaining_short_literal_length_improvement` |
| H-GEN3AO | `controlled_forced_length_literal_repair_improvement` |
| H-GEN3AP | `post_forced_repair_payload_alpha_retains_14` |
| H-GEN3AQ | `post_forced_repair_address_optimistic_only_not_promoted` |
| H-GEN3AR | `post_forced_repair_pair_not_promoted` |
| H-GEN3AS | `post_forced_repair_triple_not_promoted` |
| H-GEN3AT | `post_forced_repair_quad_not_promoted` |
| H-GEN3AU | `post_forced_repair_quint_not_promoted` |
| H-GEN3AV | `post_forced_repair_sext_not_promoted` |
| H-GEN3AW | `post_forced_repair_sept_not_promoted` |
| H-GEN3AX | `post_forced_repair_oct_not_promoted` |
| H-GEN3AY | `post_forced_repair_nonet_not_promoted` |
| H-GEN3AZ | `post_forced_repair_decet_not_promoted` |
| H-GEN3BA | `post_forced_repair_eleven_not_promoted` |
| H-GEN3BB | `post_forced_repair_twelve_not_promoted` |
| H-GEN3BC | `post_forced_repair_high_order_not_promoted` |
| H-GEN3BD | `controlled_literal_payload_context_improvement` |
| H-GEN3BE | `controlled_literal_payload_context_order_improvement` |
| H-GEN3BF | `controlled_item_type_context_order_improvement` |
| H-GEN3BG | `contextual_local_repair_not_promoted` |
| H-GEN3BH | `controlled_contextual_copy_to_literal_improvement` |
| H-GEN3BI | `post_copy_literal_local_frontier_closed` |
| H-GEN3BJ | `contextual_address_optimistic_only_not_promoted` |
| H-GEN3BK | `post_contextual_parameter_resweep_retains_current` |
| H-GEN3BL | `controlled_bounded_copy_length_improvement` |
| H-GEN3BM | `controlled_min_len_bounded_copy_address_improvement` |
| H-GEN3BN | `controlled_minaddr_local_repair_improvement` |
| H-GEN3BO | `controlled_post_minaddr_repair_local_improvement` |
| H-GEN3BP | `post_minaddr_repair2_local_frontier_closed` |
| H-GEN3BQ | `post_repair2_parameter_resweep_retains_current` |
| H-GEN3BR | `post_repair2_pair_frontier_closed` |
| H-GEN3BS | `post_repair2_address_optimistic_only_not_promoted` |
| H-GEN3BT | `post_repair2_copy_order_optimistic_only_not_promoted` |
| H-GEN3BU | `controlled_post_repair2_adaptive_copy_length_improvement` |
| H-GEN3BV | `post_adaptive_copy_length_local_frontier_closed` |
| H-GEN3BW | `post_adaptive_parameter_resweep_retains_current` |
| H-GEN3BX | `post_adaptive_pair_frontier_closed` |
| H-GEN3BY | `post_adaptive_address_optimistic_only_not_promoted` |
| H-GEN3BZ | `post_adaptive_copy_order_optimistic_only_not_promoted` |
| H-GEN3CA | `controlled_post_adaptive_copy_length_midpoint_context_improvement` |
| H-GEN3CB | `post_midpoint_local_frontier_closed` |
| H-GEN3CC | `controlled_post_midpoint_copy_length_alpha_improvement` |
| H-GEN3CD | `post_midpoint_alpha1_local_frontier_closed` |
| H-GEN3CE | `post_midpoint_alpha1_pair_frontier_closed` |
| H-GEN3CF | `post_midpoint_alpha1_address_optimistic_only_not_promoted` |
| H-GEN3CG | `post_midpoint_alpha1_copy_order_optimistic_only_not_promoted` |
| H-GEN3CH | `post_midpoint_alpha1_copy_length_context_retains_midpoint` |
| H-GEN3CI | `post_midpoint_alpha_by_context_not_promoted` |
| H-GEN3CJ | `post_midpoint_literal_payload_context_not_promoted` |
| H-GEN3CK | `bounded_post_midpoint_alpha1_top60_triple_probe_not_promoted` |
| H-GEN3CL | `controlled_post_midpoint_item_type_context_improvement` |
| H-GEN3CM | `controlled_post_itemctx_parameter_improvement` |
| H-GEN3CN | `post_itemctx_param_local_frontier_closed` |
| H-GEN3CO | `post_itemctx_param_pair_frontier_closed` |
| H-GEN3CP | `post_itemctx_param_address_optimistic_only_not_promoted` |
| H-GEN3CQ | `post_itemctx_param_copy_order_optimistic_only_not_promoted` |
| H-GEN3CR | `post_itemctx_param_copy_length_context_retains_midpoint` |
| H-GEN3CS | `post_itemctx_param_alpha_by_context_not_promoted` |
| H-GEN3CT | `post_itemctx_param_literal_payload_context_not_promoted` |
| H-GEN3CU | `post_itemctx_param_item_type_context_family_not_promoted` |
| H-GEN3CV | `post_itemctx_param_payload_item_type_pair_not_promoted` |
| H-GEN3CW | `post_itemctx_param_copy_length_item_type_pair_not_promoted` |
| H-GEN3CX | `post_itemctx_param_payload_copy_length_item_type_triple_not_promoted` |
| H-GEN3CY | `post_itemctx_param_copy_length_alpha_item_type_pair_not_promoted` |
| H-GEN3CZ | `post_itemctx_param_copy_length_alpha_payload_pair_not_promoted` |
| H-GEN3DA | `post_itemctx_param_copy_alpha_payload_item_type_triple_not_promoted` |
| H-GEN3DB | `post_itemctx_param_copy_length_context_alpha_not_promoted` |
| H-GEN3DC | `post_itemctx_param_literal_payload_context_alpha_not_promoted` |
| H-GEN3DD | `post_itemctx_param_copy_payload_context_alpha_pair_not_promoted` |
| H-GEN3DE | `post_itemctx_param_copy_payload_item_context_alpha_triple_not_promoted` |
| H-GEN3DF | `post_itemctx_param_address_copy_order_pair_optimistic_only_not_promoted` |
| H-GEN3DG | `post_itemctx_param_address_item_type_pair_optimistic_only_not_promoted` |
| H-GEN3DH | `post_itemctx_param_address_payload_context_alpha_pair_optimistic_only_not_promoted` |
| H-GEN4 | `open_low_expectation` |
| H-GEN4A | `hierarchical_provenance_not_pair_table_formula` |
| H-GEN5 | `watchlist_only` |

## Reports

- [Authorial mechanism synthesis report](../../analysis/authorial_mechanism_20260620/reports/authorial_mechanism_synthesis_report.md)
- [Final authorial mechanism report](../../analysis/authorial_mechanism_20260620/reports/final_authorial_mechanism_report.md)
- [First-principles hypothesis audit](../../analysis/authorial_mechanism_20260620/reports/test_results/01_first_principles_hypothesis_audit.md)
- [Recipe supermodule search](../../analysis/authorial_mechanism_20260620/reports/test_results/02_recipe_supermodule_search.md)
- [Topology module signal audit](../../analysis/authorial_mechanism_20260620/reports/test_results/03_topology_module_signal_audit.md)
- [Literal absorption search](../../analysis/authorial_mechanism_20260620/reports/test_results/04_literal_absorption_search.md)
- [Literal reference formula compile](../../analysis/authorial_mechanism_20260620/reports/test_results/05_literal_reference_formula_compile.md)
- [Literal reference benchmark and controls](../../analysis/authorial_mechanism_20260620/reports/test_results/06_literal_reference_benchmark_controls.md)
- [Tape inventory self-reference search](../../analysis/authorial_mechanism_20260620/reports/test_results/07_tape_inventory_self_reference_search.md)
- [Hierarchical reference formula compile](../../analysis/authorial_mechanism_20260620/reports/test_results/08_hierarchical_reference_formula_compile.md)
- [Hierarchical provenance pair-label audit](../../analysis/authorial_mechanism_20260620/reports/test_results/09_hierarchical_provenance_pair_label_audit.md)
- [Sequential LZ book formula compile](../../analysis/authorial_mechanism_20260620/reports/test_results/10_sequential_lz_book_formula_compile.md)
- [Sequential LZ book order search](../../analysis/authorial_mechanism_20260620/reports/test_results/11_sequential_lz_order_search.md)
- [Sequential LZ literal-run cost compile](../../analysis/authorial_mechanism_20260620/reports/test_results/12_sequential_lz_literal_run_cost_compile.md)
- [Sequential LZ dynamic-parse compile](../../analysis/authorial_mechanism_20260620/reports/test_results/13_sequential_lz_dp_parse_compile.md)
- [Copy source address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/14_copy_source_address_model_search.md)
- [Copy graph provenance audit](../../analysis/authorial_mechanism_20260620/reports/test_results/15_copy_graph_provenance_audit.md)
- [Structured physical order LZ test](../../analysis/authorial_mechanism_20260620/reports/test_results/16_structured_physical_order_lz_test.md)
- [Literal seed address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/17_literal_seed_address_model_search.md)
- [Literal seed grouped-mode search](../../analysis/authorial_mechanism_20260620/reports/test_results/18_literal_seed_grouped_mode_search.md)
- [Copy hub macro model search](../../analysis/authorial_mechanism_20260620/reports/test_results/19_copy_hub_macro_model_search.md)
- [Restricted hybrid vocabulary reparse](../../analysis/authorial_mechanism_20260620/reports/test_results/20_restricted_hybrid_vocabulary_reparse.md)
- [DP min-length sweep control](../../analysis/authorial_mechanism_20260620/reports/test_results/21_dp_min_len_sweep_control.md)
- [Copy length code reparse](../../analysis/authorial_mechanism_20260620/reports/test_results/22_copy_length_code_reparse.md)
- [Copy length grid sweep](../../analysis/authorial_mechanism_20260620/reports/test_results/23_copy_length_grid_sweep.md)
- [Rice copy address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/24_rice_copy_address_model_search.md)
- [Literal run length code reparse](../../analysis/authorial_mechanism_20260620/reports/test_results/25_literal_run_length_code_reparse.md)
- [Joint length code grid sweep](../../analysis/authorial_mechanism_20260620/reports/test_results/26_joint_length_code_grid_sweep.md)
- [Literal payload model search](../../analysis/authorial_mechanism_20260620/reports/test_results/27_literal_payload_model_search.md)
- [Current formula address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/28_current_formula_address_model_search.md)
- [Literal-to-copy repair search](../../analysis/authorial_mechanism_20260620/reports/test_results/29_literal_to_copy_repair_search.md)
- [Post-repair payload alpha sweep](../../analysis/authorial_mechanism_20260620/reports/test_results/30_post_repair_payload_alpha_sweep.md)
- [Post-repair address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/31_post_repair_address_model_search.md)
- [Literal-to-copy pair repair search](../../analysis/authorial_mechanism_20260620/reports/test_results/32_literal_to_copy_pair_repair_search.md)
- [Book length ledger search](../../analysis/authorial_mechanism_20260620/reports/test_results/33_book_length_ledger_search.md)
- [Book length multi-anchor search](../../analysis/authorial_mechanism_20260620/reports/test_results/34_book_length_multi_anchor_search.md)
- [Digit-only copy address compile](../../analysis/authorial_mechanism_20260620/reports/test_results/35_digit_only_copy_address_compile.md)
- [Digit address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/36_digit_address_model_search.md)
- [Digit-address literal repair search](../../analysis/authorial_mechanism_20260620/reports/test_results/37_digit_address_literal_repair_search.md)
- [Post-digit-repair payload alpha sweep](../../analysis/authorial_mechanism_20260620/reports/test_results/38_post_digit_repair_payload_alpha_sweep.md)
- [Post-digit-repair address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/39_post_digit_repair_address_model_search.md)
- [Item-type ledger compile](../../analysis/authorial_mechanism_20260620/reports/test_results/40_item_type_ledger_compile.md)
- [Markov item-type ledger compile](../../analysis/authorial_mechanism_20260620/reports/test_results/41_markov_item_type_ledger_compile.md)
- [Book-start item-type ledger compile](../../analysis/authorial_mechanism_20260620/reports/test_results/42_book_start_item_type_ledger_compile.md)
- [Literal-forces-copy item-type ledger compile](../../analysis/authorial_mechanism_20260620/reports/test_results/43_literal_forces_copy_type_ledger_compile.md)
- [Remaining-short-forces-literal item-type ledger compile](../../analysis/authorial_mechanism_20260620/reports/test_results/44_remaining_short_forces_literal_type_ledger_compile.md)
- [Remaining-short literal-length compile](../../analysis/authorial_mechanism_20260620/reports/test_results/45_remaining_short_literal_length_compile.md)
- [Forced-length literal repair search](../../analysis/authorial_mechanism_20260620/reports/test_results/46_forced_length_literal_repair_search.md)
- [Post-forced-repair payload alpha sweep](../../analysis/authorial_mechanism_20260620/reports/test_results/47_post_forced_repair_payload_alpha_sweep.md)
- [Post-forced-repair address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/48_post_forced_repair_address_model_search.md)
- [Post-forced-repair pair search](../../analysis/authorial_mechanism_20260620/reports/test_results/49_post_forced_repair_pair_search.md)
- [Post-forced-repair triple search](../../analysis/authorial_mechanism_20260620/reports/test_results/50_post_forced_repair_triple_search.md)
- [Post-forced-repair quad search](../../analysis/authorial_mechanism_20260620/reports/test_results/51_post_forced_repair_quad_search.md)
- [Post-forced-repair quint search](../../analysis/authorial_mechanism_20260620/reports/test_results/52_post_forced_repair_quint_search.md)
- [Post-forced-repair sext search](../../analysis/authorial_mechanism_20260620/reports/test_results/53_post_forced_repair_sext_search.md)
- [Post-forced-repair sept search](../../analysis/authorial_mechanism_20260620/reports/test_results/54_post_forced_repair_sept_search.md)
- [Post-forced-repair oct search](../../analysis/authorial_mechanism_20260620/reports/test_results/55_post_forced_repair_oct_search.md)
- [Post-forced-repair nonet search](../../analysis/authorial_mechanism_20260620/reports/test_results/56_post_forced_repair_nonet_search.md)
- [Post-forced-repair decet search](../../analysis/authorial_mechanism_20260620/reports/test_results/57_post_forced_repair_decet_search.md)
- [Post-forced-repair eleven-repair search](../../analysis/authorial_mechanism_20260620/reports/test_results/58_post_forced_repair_eleven_search.md)
- [Post-forced-repair twelve-repair search](../../analysis/authorial_mechanism_20260620/reports/test_results/59_post_forced_repair_twelve_search.md)
- [Post-forced-repair high-order exhaustion](../../analysis/authorial_mechanism_20260620/reports/test_results/60_post_forced_repair_high_order_exhaustion.md)
- [Post-forced-repair literal payload context search](../../analysis/authorial_mechanism_20260620/reports/test_results/61_post_forced_repair_literal_payload_context_search.md)
- [Literal payload context order sweep](../../analysis/authorial_mechanism_20260620/reports/test_results/62_literal_payload_context_order_sweep.md)
- [Item-type context order sweep](../../analysis/authorial_mechanism_20260620/reports/test_results/63_item_type_context_order_sweep.md)
- [Contextual local repair search](../../analysis/authorial_mechanism_20260620/reports/test_results/64_contextual_local_repair_search.md)
- [Contextual copy-to-literal repair search](../../analysis/authorial_mechanism_20260620/reports/test_results/65_contextual_copy_to_literal_repair_search.md)
- [Post copy-to-literal local frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/66_post_copy_literal_local_frontier.md)
- [Contextual address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/67_contextual_address_model_search.md)
- [Post-contextual parameter resweep](../../analysis/authorial_mechanism_20260620/reports/test_results/68_post_contextual_parameter_resweep.md)
- [Bounded copy-length code compile](../../analysis/authorial_mechanism_20260620/reports/test_results/69_bounded_copy_length_code_compile.md)
- [Min-length-bounded copy address compile](../../analysis/authorial_mechanism_20260620/reports/test_results/70_min_len_bounded_copy_address_compile.md)
- [Minaddr local frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/71_minaddr_local_frontier.md)
- [Post-minaddr-repair local frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/72_post_minaddr_repair_local_frontier.md)
- [Post-minaddr-repair2 local frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/73_post_minaddr_repair2_local_frontier.md)
- [Post-repair2 parameter resweep](../../analysis/authorial_mechanism_20260620/reports/test_results/74_post_repair2_parameter_resweep.md)
- [Post-repair2 pair frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/75_post_repair2_pair_frontier.md)
- [Post-repair2 address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/76_post_repair2_address_model_search.md)
- [Post-repair2 copy order search](../../analysis/authorial_mechanism_20260620/reports/test_results/77_post_repair2_copy_order_search.md)
- [Post-repair2 adaptive copy-length compile](../../analysis/authorial_mechanism_20260620/reports/test_results/78_post_repair2_adaptive_copy_length_compile.md)
- [Post-adaptive-copy-length local frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/79_post_adaptive_copy_length_local_frontier.md)
- [Post-adaptive parameter resweep](../../analysis/authorial_mechanism_20260620/reports/test_results/80_post_adaptive_parameter_resweep.md)
- [Post-adaptive pair frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/81_post_adaptive_pair_frontier.md)
- [Post-adaptive address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/82_post_adaptive_address_model_search.md)
- [Post-adaptive copy order search](../../analysis/authorial_mechanism_20260620/reports/test_results/83_post_adaptive_copy_order_search.md)
- [Post-adaptive copy-length context search](../../analysis/authorial_mechanism_20260620/reports/test_results/84_post_adaptive_copy_length_context_search.md)
- [Post-midpoint local frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/85_post_midpoint_local_frontier.md)
- [Post-midpoint parameter resweep](../../analysis/authorial_mechanism_20260620/reports/test_results/86_post_midpoint_parameter_resweep.md)
- [Post-midpoint alpha1 local frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/87_post_midpoint_alpha1_local_frontier.md)
- [Post-midpoint alpha1 pair frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/88_post_midpoint_alpha1_pair_frontier.md)
- [Post-midpoint alpha1 address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/89_post_midpoint_alpha1_address_model_search.md)
- [Post-midpoint alpha1 copy order search](../../analysis/authorial_mechanism_20260620/reports/test_results/90_post_midpoint_alpha1_copy_order_search.md)
- [Post-midpoint alpha1 copy-length context resweep](../../analysis/authorial_mechanism_20260620/reports/test_results/91_post_midpoint_alpha1_copy_length_context_resweep.md)
- [Post-midpoint alpha1 context alpha grid](../../analysis/authorial_mechanism_20260620/reports/test_results/92_post_midpoint_alpha1_context_alpha_grid.md)
- [Post-midpoint alpha1 literal payload context search](../../analysis/authorial_mechanism_20260620/reports/test_results/93_post_midpoint_alpha1_literal_payload_context_search.md)
- [Post-midpoint alpha1 top60 triple probe](../../analysis/authorial_mechanism_20260620/reports/test_results/94_post_midpoint_alpha1_top60_triple_probe.md)
- [Post-midpoint alpha1 item-type context search](../../analysis/authorial_mechanism_20260620/reports/test_results/95_post_midpoint_alpha1_item_type_context_search.md)
- [Post-itemctx parameter resweep](../../analysis/authorial_mechanism_20260620/reports/test_results/96_post_itemctx_parameter_resweep.md)
- [Post-itemctx param local frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/97_post_itemctx_param_local_frontier.md)
- [Post-itemctx param pair frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/98_post_itemctx_param_pair_frontier.md)
- [Post-itemctx param address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/99_post_itemctx_param_address_model_search.md)
- [Post-itemctx param copy order search](../../analysis/authorial_mechanism_20260620/reports/test_results/100_post_itemctx_param_copy_order_search.md)
- [Post-itemctx param copy-length context resweep](../../analysis/authorial_mechanism_20260620/reports/test_results/101_post_itemctx_param_copy_length_context_resweep.md)
- [Post-itemctx param context alpha grid](../../analysis/authorial_mechanism_20260620/reports/test_results/102_post_itemctx_param_context_alpha_grid.md)
- [Post-itemctx param literal payload context search](../../analysis/authorial_mechanism_20260620/reports/test_results/103_post_itemctx_param_literal_payload_context_search.md)
- [Post-itemctx param item-type context family search](../../analysis/authorial_mechanism_20260620/reports/test_results/104_post_itemctx_param_item_type_context_family_search.md)
- [Post-itemctx param payload/item-type pair context search](../../analysis/authorial_mechanism_20260620/reports/test_results/105_post_itemctx_param_payload_item_type_pair_context_search.md)
- [Post-itemctx param copy-length/item-type pair context search](../../analysis/authorial_mechanism_20260620/reports/test_results/106_post_itemctx_param_copy_length_item_type_pair_context_search.md)
- [Post-itemctx param payload/copy-length/item-type triple context search](../../analysis/authorial_mechanism_20260620/reports/test_results/107_post_itemctx_param_payload_copy_length_item_type_triple_context_search.md)
- [Post-itemctx param copy-length alpha/item-type pair search](../../analysis/authorial_mechanism_20260620/reports/test_results/108_post_itemctx_param_copy_length_alpha_item_type_pair_search.md)
- [Post-itemctx param copy-length alpha/payload pair search](../../analysis/authorial_mechanism_20260620/reports/test_results/109_post_itemctx_param_copy_length_alpha_payload_pair_search.md)
- [Post-itemctx param copy-alpha/payload/item-type triple search](../../analysis/authorial_mechanism_20260620/reports/test_results/110_post_itemctx_param_copy_alpha_payload_item_type_triple_search.md)
- [Post-itemctx param copy-length context/shared-alpha resweep](../../analysis/authorial_mechanism_20260620/reports/test_results/111_post_itemctx_param_copy_length_context_alpha_resweep.md)
- [Post-itemctx param literal-payload context/shared-alpha resweep](../../analysis/authorial_mechanism_20260620/reports/test_results/112_post_itemctx_param_literal_payload_context_alpha_resweep.md)
- [Post-itemctx param copy/payload context-alpha pair search](../../analysis/authorial_mechanism_20260620/reports/test_results/113_post_itemctx_param_copy_payload_context_alpha_pair_search.md)
- [Post-itemctx param copy/payload/item context-alpha triple search](../../analysis/authorial_mechanism_20260620/reports/test_results/114_post_itemctx_param_copy_payload_item_context_alpha_triple_search.md)
- [Post-itemctx param address/copy-order pair search](../../analysis/authorial_mechanism_20260620/reports/test_results/115_post_itemctx_param_address_copy_order_pair_search.md)
- [Post-itemctx param address/item-type pair search](../../analysis/authorial_mechanism_20260620/reports/test_results/116_post_itemctx_param_address_item_type_pair_search.md)
- [Post-itemctx param address/payload context-alpha pair search](../../analysis/authorial_mechanism_20260620/reports/test_results/117_post_itemctx_param_address_payload_context_alpha_pair_search.md)
- [Prequential generation model audit](../../analysis/authorial_mechanism_20260620/reports/test_results/118_prequential_generation_model_audit.md)
- [Row0 origin frontier audit](../../analysis/authorial_mechanism_20260620/reports/test_results/119_row0_origin_frontier_audit.md)
- [Prequential order control audit](../../analysis/authorial_mechanism_20260620/reports/test_results/120_prequential_order_control_audit.md)
- [Prequential component ablation audit](../../analysis/authorial_mechanism_20260620/reports/test_results/121_prequential_component_ablation_audit.md)
- [Simplified generation profile compile](../../analysis/authorial_mechanism_20260620/reports/test_results/122_simplified_generation_profile_compile.md)
- [Item-type split-only formula compile](../../analysis/authorial_mechanism_20260620/reports/test_results/123_item_type_split_only_formula_compile.md)
- [Item-type split-only alpha resweep](../../analysis/authorial_mechanism_20260620/reports/test_results/124_item_type_split_only_alpha_resweep.md)
- [Item-type op-shape boundary gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/33_item_type_op_shape_boundary_gate.md)
- [Prequential and row0 origin audit](../../analysis/authorial_mechanism_20260620/reports/test_results/125_prequential_and_row0_origin_audit.md)
- [Prequential and row0 origin audit 2026-06-21](../../analysis/prequential_and_row0_origin_audit_20260621/reports/prequential_and_row0_origin_audit.md)
- [Family holdout failure audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/02_family_holdout_failure_audit.md)
- [Train-CV component selector audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/03_train_cv_component_selector_audit.md)
- [Recipe externality audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/04_recipe_externality_audit.md)
- [Row0 hypothesis requirement audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/05_row0_hypothesis_requirement_audit.md)
- [Row0 parallel provenance bridge audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/47_row0_parallel_provenance_bridge_audit.md)
- [Current formula dependency scoreboard](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/48_current_formula_dependency_scoreboard.md)
- [Source-length joint derivability audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/49_source_length_joint_derivability_audit.md)
- [Source canonicality tradeoff audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/50_source_canonicality_tradeoff_audit.md)
- [Copy length segmentation exception audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/51_copy_length_segmentation_exception_audit.md)
- [Target-max resegmentation candidate audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/52_targetmax_resegmentation_candidate_audit.md)
- [Target-max resegmentation formula gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/53_targetmax_resegmentation_formula_gate.md)
- [Target-max resegmentation second-pass gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/54_targetmax_resegmentation_second_pass_gate.md)
- [Target-max resegmentation saturation gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/55_targetmax_resegmentation_saturation_gate.md)
- [Post-target-max source substitution frontier gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/56_post_targetmax_source_substitution_frontier_gate.md)
- [Post-target-max source substitution second-pass gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/57_post_targetmax_source_substitution_second_pass_gate.md)
- [Post-target-max source substitution stop audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/58_post_targetmax_source_substitution_stop_audit.md)
- [Active formula dependency refresh gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/59_active_formula_dependency_refresh_gate.md)
- [Active source-length joint refresh gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/60_active_source_length_joint_refresh_gate.md)
- [Active copy-length exception topology gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/61_active_copy_length_exception_topology_gate.md)
- [Active residual target-max resegmentation gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/62_active_residual_targetmax_resegmentation_gate.md)
- [Recipe reparse evidence matrix](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/06_recipe_reparse_evidence_matrix.md)
- [Recipe reparse train-set multi-cutoff](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/07_recipe_reparse_trainset_multicutoff.md)
- [Recipe reparse family holdout](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/08_recipe_reparse_family_holdout.md)
- [Recipe reparse family loss decomposition](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/09_recipe_reparse_family_loss_decomposition.md)
- [Family holdout address-space audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/10_family_holdout_address_space_audit.md)
- [Family holdout address-corrected scoreboard](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/11_family_holdout_address_corrected_scoreboard.md)
- [Family holdout no-test-carryover audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/12_family_holdout_no_test_carryover_audit.md)
- [Leave-one-book-out no-self audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/13_leave_one_book_out_no_self_audit.md)
- [Leave-one-book-out source attribution audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/14_leave_one_book_out_source_attribution_audit.md)
- [Leave-one-book-out book-bounded source audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/15_leave_one_book_out_book_bounded_source_audit.md)
- [Leave-one-book-out family-excluded source audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/16_leave_one_book_out_family_excluded_source_audit.md)
- [Online prefix book frontier audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/17_online_prefix_book_frontier_audit.md)
- [Online bootstrap seed policy audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/18_online_bootstrap_seed_policy_audit.md)
- [Seeded online formula rescore audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/19_seeded_online_formula_rescore_audit.md)
- [Seeded rescore loss decomposition](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/20_seeded_rescore_loss_decomposition.md)
- [Seed exception signal cost audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/21_seed_exception_signal_cost_audit.md)
- [Online order frontier controls](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/22_online_order_frontier_controls.md)
- [Order frontier promotion gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/23_order_frontier_promotion_gate.md)
- [Prequential recipe reparse audit](../../analysis/authorial_mechanism_20260620/reports/test_results/126_prequential_recipe_reparse_audit.md)
- [Prequential recipe reparse controls](../../analysis/authorial_mechanism_20260620/reports/test_results/127_prequential_recipe_reparse_controls.md)
- [Prequential recipe train-set controls](../../analysis/authorial_mechanism_20260620/reports/test_results/128_prequential_recipe_reparse_trainset_controls.md)
- [Online deterministic reparse compile](../../analysis/authorial_mechanism_20260620/reports/test_results/129_online_deterministic_reparse_compile.md)
- [Online reparse order control audit](../../analysis/authorial_mechanism_20260620/reports/test_results/130_online_reparse_order_control_audit.md)
- [Online formula recipe prune audit](../../analysis/authorial_mechanism_20260620/reports/test_results/131_online_formula_recipe_prune_audit.md)
- [Canonical online recipe formula compile](../../analysis/authorial_mechanism_20260620/reports/test_results/132_canonical_online_recipe_formula_compile.md)
- [Literal-length-derived recipe compile](../../analysis/authorial_mechanism_20260620/reports/test_results/133_literal_length_derived_recipe_compile.md)
- [Op-type-derived recipe compile](../../analysis/authorial_mechanism_20260620/reports/test_results/134_op_type_derived_recipe_compile.md)
- [Recipe representation dependency gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/30_recipe_representation_dependency_gate.md)
- [Copy source canonicality audit](../../analysis/authorial_mechanism_20260620/reports/test_results/135_copy_source_canonicality_audit.md)
- [Source canonicality decodability gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/25_source_canonicality_decodability_gate.md)
- [Online copy-source canonicality controls](../../analysis/authorial_mechanism_20260620/reports/test_results/140_online_copy_source_canonicality_audit.md)
- [Source selection derivation boundary gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/31_source_selection_derivation_boundary_gate.md)
- [Copy length default decodability audit](../../analysis/authorial_mechanism_20260620/reports/test_results/136_copy_length_default_decodability_audit.md)
- [Copy length derivation boundary gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/32_copy_length_derivation_boundary_gate.md)
- [Copy source default decodability audit](../../analysis/authorial_mechanism_20260620/reports/test_results/137_copy_source_default_decodability_audit.md)
- [Default/exception prequential validation](../../analysis/authorial_mechanism_20260620/reports/test_results/141_default_exception_prequential_validation.md)
- [Default/exception component profile](../../analysis/authorial_mechanism_20260620/reports/test_results/142_default_exception_component_profile.md)
- [Current literal payload profile audit](../../analysis/authorial_mechanism_20260620/reports/test_results/143_current_literal_payload_profile_audit.md)
- [Copy source distance model audit](../../analysis/authorial_mechanism_20260620/reports/test_results/144_copy_source_distance_model_audit.md)
- [Current active prequential profile audit](../../analysis/authorial_mechanism_20260620/reports/test_results/145_current_active_prequential_profile_audit.md)
- [Current active profile boundary gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/34_current_active_profile_boundary_gate.md)
- [Copy source state compression gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/35_copy_source_state_compression_gate.md)
- [Active reparse state-boundary audit](../../analysis/authorial_mechanism_20260620/reports/test_results/146_active_reparse_state_boundary_audit.md)
- [Copy source state-free default audit](../../analysis/authorial_mechanism_20260620/reports/test_results/147_copy_source_state_free_default_audit.md)
- [Source state dependency gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/26_source_state_dependency_gate.md)
- [Copy length midpoint context audit](../../analysis/authorial_mechanism_20260620/reports/test_results/148_copy_length_midpoint_context_audit.md)
- [Copy length midpoint context gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/27_copy_length_midpoint_context_gate.md)
- [Literal copy availability boundary audit](../../analysis/authorial_mechanism_20260620/reports/test_results/149_literal_copy_availability_boundary_audit.md)
- [Literal copy availability gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/28_literal_copy_availability_gate.md)
- [Optional literal copy repair frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/150_optional_literal_copy_repair_frontier.md)
- [Cross-op optional literal copy frontier](../../analysis/authorial_mechanism_20260620/reports/test_results/151_cross_op_optional_literal_copy_frontier.md)
- [Cross-op near-tie decomposition](../../analysis/authorial_mechanism_20260620/reports/test_results/152_cross_op_near_tie_decomposition.md)
- [Cross-op source break-even audit](../../analysis/authorial_mechanism_20260620/reports/test_results/153_cross_op_source_break_even_audit.md)
- [Copy source structural context audit](../../analysis/authorial_mechanism_20260620/reports/test_results/154_copy_source_structural_context_audit.md)
- [Source blocker structural context gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/24_source_blocker_structural_context_gate.md)
- [Full source all-policy multi-cutoff probe](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/93_full_source_all_policy_multicutoff_probe.md)
- [Full source all-policy five-cutoff probe](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/94_full_source_all_policy_fivecutoff_probe.md)
- [Full source policy invariance boundary](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/95_full_source_policy_invariance_boundary.md)
- [Full source canonical policy boundary](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/96_full_source_canonical_policy_boundary.md)
- [Source policy selector boundary](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/97_source_policy_selector_boundary.md)
- [Full source exact skeleton invariance](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/98_full_source_exact_skeleton_invariance.md)
- [Exact skeleton dependency ledger](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/99_exact_skeleton_dependency_ledger.md)
- [Final skeleton decoder ambiguity audit](../../analysis/skeleton_decoder_ambiguity_audit_20260621/reports/final_skeleton_decoder_ambiguity_audit.md)
- [Skeleton decoder ambiguity gate](../../analysis/skeleton_decoder_ambiguity_audit_20260621/reports/test_results/01_skeleton_decoder_ambiguity_gate.md)
- [Final generation boundary closure audit](../../analysis/generation_boundary_closure_audit_20260621/reports/final_generation_boundary_closure_audit.md)
- [Generation boundary closure audit](../../analysis/generation_boundary_closure_audit_20260621/reports/test_results/01_generation_boundary_closure_audit.md)
- [Final operation count generation audit](../../analysis/operation_count_generation_audit_20260621/reports/final_operation_count_generation_audit.md)
- [Operation count generation gate](../../analysis/operation_count_generation_audit_20260621/reports/test_results/01_operation_count_generation_gate.md)
- [Final operation shape count generation audit](../../analysis/operation_shape_count_generation_audit_20260621/reports/final_operation_shape_count_generation_audit.md)
- [Operation shape count generation gate](../../analysis/operation_shape_count_generation_audit_20260621/reports/test_results/01_operation_shape_count_generation_gate.md)
- [Final operation type sequence generation audit](../../analysis/operation_type_sequence_generation_audit_20260621/reports/final_operation_type_sequence_generation_audit.md)
- [Operation type sequence generation gate](../../analysis/operation_type_sequence_generation_audit_20260621/reports/test_results/01_operation_type_sequence_generation_gate.md)
- [Final operation type-weighted length audit](../../analysis/operation_type_weighted_length_audit_20260621/reports/final_operation_type_weighted_length_audit.md)
- [Operation type-weighted length gate](../../analysis/operation_type_weighted_length_audit_20260621/reports/test_results/01_operation_type_weighted_length_gate.md)
- [Final operation length Markov audit](../../analysis/operation_length_markov_audit_20260621/reports/final_operation_length_markov_audit.md)
- [Operation length Markov gate](../../analysis/operation_length_markov_audit_20260621/reports/test_results/01_operation_length_markov_gate.md)
- [Final operation length motif audit](../../analysis/operation_length_motif_audit_20260621/reports/final_operation_length_motif_audit.md)
- [Operation length motif library gate](../../analysis/operation_length_motif_audit_20260621/reports/test_results/01_operation_length_motif_library_gate.md)
- [Final operation cutpoint scaling audit](../../analysis/operation_cutpoint_scaling_audit_20260621/reports/final_operation_cutpoint_scaling_audit.md)
- [Operation cutpoint scaling gate](../../analysis/operation_cutpoint_scaling_audit_20260621/reports/test_results/01_operation_cutpoint_scaling_gate.md)
- [Final operation cutpoint lattice audit](../../analysis/operation_cutpoint_lattice_audit_20260621/reports/final_operation_cutpoint_lattice_audit.md)
- [Operation cutpoint lattice gate](../../analysis/operation_cutpoint_lattice_audit_20260621/reports/test_results/01_operation_cutpoint_lattice_gate.md)
- [Final operation recursive partition audit](../../analysis/operation_recursive_partition_audit_20260621/reports/final_operation_recursive_partition_audit.md)
- [Operation recursive partition gate](../../analysis/operation_recursive_partition_audit_20260621/reports/test_results/01_operation_recursive_partition_gate.md)
- [Final book order generation audit](../../analysis/book_order_generation_audit_20260621/reports/final_book_order_generation_audit.md)
- [Book order dependency gate](../../analysis/book_order_generation_audit_20260621/reports/test_results/01_book_order_dependency_gate.md)
- [Final book length generation audit](../../analysis/book_length_generation_audit_20260621/reports/final_book_length_generation_audit.md)
- [Book length generation gate](../../analysis/book_length_generation_audit_20260621/reports/test_results/02_book_length_generation_gate.md)
- [Final source-free skeleton generation audit](../../analysis/source_free_skeleton_generation_audit_20260621/reports/final_source_free_skeleton_generation_audit.md)
- [Source-free skeleton grammar gate](../../analysis/source_free_skeleton_generation_audit_20260621/reports/test_results/02_source_free_skeleton_grammar_gate.md)
- [Final literal payload generation audit](../../analysis/literal_payload_generation_audit_20260621/reports/final_literal_payload_generation_audit.md)
- [Literal payload context gate](../../analysis/literal_payload_generation_audit_20260621/reports/test_results/02_literal_payload_context_gate.md)
- [Final literal payload reference subcodec audit](../../analysis/literal_payload_reference_subcodec_audit_20260621/reports/final_literal_payload_reference_subcodec_audit.md)
- [Literal payload reference subcodec gate](../../analysis/literal_payload_reference_subcodec_audit_20260621/reports/test_results/01_literal_payload_reference_subcodec_gate.md)
- [Final copy source generation audit](../../analysis/copy_source_generation_audit_20260621/reports/final_copy_source_generation_audit.md)
- [Copy source context gate](../../analysis/copy_source_generation_audit_20260621/reports/test_results/03_copy_source_context_gate.md)
- [Final target-conditioned source collapse audit](../../analysis/target_conditioned_source_collapse_audit_20260621/reports/final_target_conditioned_source_collapse_audit.md)
- [Target-conditioned source collapse gate](../../analysis/target_conditioned_source_collapse_audit_20260621/reports/test_results/01_target_conditioned_source_collapse_gate.md)
- [Final target chunk dictionary audit](../../analysis/target_chunk_dictionary_audit_20260621/reports/final_target_chunk_dictionary_audit.md)
- [Target chunk dictionary gate](../../analysis/target_chunk_dictionary_audit_20260621/reports/test_results/01_target_chunk_dictionary_gate.md)
- [Final target chunk signature audit](../../analysis/target_chunk_signature_audit_20260621/reports/final_target_chunk_signature_audit.md)
- [Target chunk signature gate](../../analysis/target_chunk_signature_audit_20260621/reports/test_results/01_target_chunk_signature_gate.md)
- [Final target digit process audit](../../analysis/target_digit_process_audit_20260621/reports/final_target_digit_process_audit.md)
- [Target digit process gate](../../analysis/target_digit_process_audit_20260621/reports/test_results/01_target_digit_process_gate.md)
- [Final target digit boundary audit](../../analysis/target_digit_boundary_audit_20260621/reports/final_target_digit_boundary_audit.md)
- [Target digit boundary gate](../../analysis/target_digit_boundary_audit_20260621/reports/test_results/01_target_digit_boundary_gate.md)
- [Final target digit boundary pruning audit](../../analysis/target_digit_boundary_pruning_audit_20260621/reports/final_target_digit_boundary_pruning_audit.md)
- [Target digit boundary pruning gate](../../analysis/target_digit_boundary_pruning_audit_20260621/reports/test_results/01_target_digit_boundary_pruning_gate.md)
- [Final target digit boundary rank-code audit](../../analysis/target_digit_boundary_rankcode_audit_20260621/reports/final_target_digit_boundary_rankcode_audit.md)
- [Target digit boundary rank-code gate](../../analysis/target_digit_boundary_rankcode_audit_20260621/reports/test_results/01_target_digit_boundary_rankcode_gate.md)
- [Final target digit boundary type audit](../../analysis/target_digit_boundary_type_audit_20260621/reports/final_target_digit_boundary_type_audit.md)
- [Target digit boundary type gate](../../analysis/target_digit_boundary_type_audit_20260621/reports/test_results/01_target_digit_boundary_type_gate.md)
- [Final skeleton dependency after boundary pruning audit](../../analysis/skeleton_dependency_after_boundary_pruning_20260621/reports/final_skeleton_dependency_after_boundary_pruning_audit.md)
- [Skeleton dependency after boundary pruning gate](../../analysis/skeleton_dependency_after_boundary_pruning_20260621/reports/test_results/01_skeleton_dependency_after_boundary_pruning_gate.md)
- [Final target digit boundary threshold audit](../../analysis/target_digit_boundary_threshold_audit_20260621/reports/final_target_digit_boundary_threshold_audit.md)
- [Target digit boundary threshold gate](../../analysis/target_digit_boundary_threshold_audit_20260621/reports/test_results/01_target_digit_boundary_threshold_gate.md)
- [Final target digit boundary peak audit](../../analysis/target_digit_boundary_peak_audit_20260621/reports/final_target_digit_boundary_peak_audit.md)
- [Target digit boundary peak gate](../../analysis/target_digit_boundary_peak_audit_20260621/reports/test_results/01_target_digit_boundary_peak_gate.md)
- [Final target digit boundary island audit](../../analysis/target_digit_boundary_island_audit_20260621/reports/final_target_digit_boundary_island_audit.md)
- [Target digit boundary island gate](../../analysis/target_digit_boundary_island_audit_20260621/reports/test_results/01_target_digit_boundary_island_gate.md)
- [Final target digit boundary miss residual audit](../../analysis/target_digit_boundary_miss_residual_audit_20260621/reports/final_target_digit_boundary_miss_residual_audit.md)
- [Target digit boundary miss residual gate](../../analysis/target_digit_boundary_miss_residual_audit_20260621/reports/test_results/01_target_digit_boundary_miss_residual_gate.md)
- [Final target digit boundary miss transition audit](../../analysis/target_digit_boundary_miss_transition_audit_20260621/reports/final_target_digit_boundary_miss_transition_audit.md)
- [Target digit boundary miss transition gate](../../analysis/target_digit_boundary_miss_transition_audit_20260621/reports/test_results/01_target_digit_boundary_miss_transition_gate.md)
- [Final skeleton generation route review](../../analysis/skeleton_generation_route_review_20260622/reports/final_skeleton_generation_route_review.md)
- [Skeleton generation route review](../../analysis/skeleton_generation_route_review_20260622/reports/test_results/01_skeleton_generation_route_review.md)
- [Final joint target stream parser audit](../../analysis/joint_target_stream_parser_audit_20260622/reports/final_joint_target_stream_parser_audit.md)
- [Joint boundary digit gate](../../analysis/joint_target_stream_parser_audit_20260622/reports/test_results/01_joint_boundary_digit_gate.md)
- [Boundary hazard state gate](../../analysis/joint_target_stream_parser_audit_20260622/reports/test_results/02_boundary_hazard_state_gate.md)
- [Boundary hazard endpoint decoder gate](../../analysis/joint_target_stream_parser_audit_20260622/reports/test_results/03_boundary_hazard_endpoint_decoder_gate.md)
- [Combined boundary endpoint decoder gate](../../analysis/joint_target_stream_parser_audit_20260622/reports/test_results/04_combined_boundary_endpoint_decoder_gate.md)
- [Final latent transducer generation audit](../../analysis/latent_transducer_generation_audit_20260622/reports/final_latent_transducer_generation_audit.md)
- [Latent transducer beam gate](../../analysis/latent_transducer_generation_audit_20260622/reports/test_results/01_latent_transducer_beam_gate.md)
- [Closed loop digit survival gate](../../analysis/latent_transducer_generation_audit_20260622/reports/test_results/03_closed_loop_digit_survival_gate.md)
- [Closed loop rescue ledger](../../analysis/latent_transducer_generation_audit_20260622/reports/test_results/04_closed_loop_rescue_ledger.md)
- [Closed loop rescue surface audit](../../analysis/latent_transducer_generation_audit_20260622/reports/test_results/05_closed_loop_rescue_surface_audit.md)
- [Copy state rescue diagnostic](../../analysis/latent_transducer_generation_audit_20260622/reports/test_results/06_copy_state_rescue_diagnostic.md)
- [Copy candidate ranking frontier](../../analysis/latent_transducer_generation_audit_20260622/reports/test_results/07_copy_candidate_ranking_frontier.md)
- [Copy hint stream lower bound](../../analysis/latent_transducer_generation_audit_20260622/reports/test_results/08_copy_hint_stream_lower_bound.md)
- [Copy hint stream structure gate](../../analysis/latent_transducer_generation_audit_20260622/reports/test_results/09_copy_hint_stream_structure_gate.md)
- [Final innovation stream transducer audit](../../analysis/innovation_stream_transducer_audit_20260622/reports/final_innovation_stream_transducer_audit.md)
- [Innovation tape replay gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/01_innovation_tape_replay_gate.md)
- [Innovation tape structure gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/03_innovation_tape_structure_gate.md)
- [Tape synchronized closed loop gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/04_tape_synchronized_closed_loop_gate.md)
- [Seed derived tape subcodec gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/05_seed_derived_tape_subcodec_gate.md)
- [Seed walk source model gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/06_seed_walk_source_model_gate.md)
- [Innovation tape schedule gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/07_innovation_tape_schedule_gate.md)
- [Tape trigger policy gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/08_tape_trigger_policy_gate.md)
- [Decoder visible trigger policy gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/09_decoder_visible_trigger_policy_gate.md)
- [Boundary candidate trigger gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/10_boundary_candidate_trigger_gate.md)
- [Decoder visible boundary candidate trigger gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/11_decoder_visible_boundary_candidate_trigger_gate.md)
- [Internal boundary candidate trigger decomposition gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/12_internal_boundary_candidate_trigger_decomposition_gate.md)
- [Book start mode gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/13_book_start_mode_gate.md)
- [Generation dependency frontier ledger](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/14_generation_dependency_frontier_ledger.md)
- [Length control tape gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/15_length_control_tape_gate.md)
- [Joint type-length control tape gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/16_joint_type_length_control_tape_gate.md)
- [Final unified control program audit](../../analysis/unified_control_program_audit_20260622/reports/final_unified_control_program_audit.md)
- [Unified residual control ledger](../../analysis/unified_control_program_audit_20260622/reports/test_results/01_unified_residual_control_ledger.md)
- [Unified control program tests](../../analysis/unified_control_program_audit_20260622/reports/test_results/02_unified_control_program_tests.md)
- [Final stateful control program audit](../../analysis/stateful_control_program_audit_20260622/reports/final_stateful_control_program_audit.md)
- [Stateful control program gate](../../analysis/stateful_control_program_audit_20260622/reports/test_results/01_stateful_control_program_gate.md)
- [Final length innovation factor audit](../../analysis/length_innovation_factor_audit_20260622/reports/final_length_innovation_factor_audit.md)
- [Length innovation factor gate](../../analysis/length_innovation_factor_audit_20260622/reports/test_results/01_length_innovation_factor_gate.md)
- [Final coarse control program audit](../../analysis/coarse_control_program_audit_20260622/reports/final_coarse_control_program_audit.md)
- [Coarse control program gate](../../analysis/coarse_control_program_audit_20260622/reports/test_results/01_coarse_control_program_gate.md)
- [Final book-level coarse length controller audit](../../analysis/book_level_coarse_length_controller_audit_20260622/reports/final_book_level_coarse_length_controller_audit.md)
- [Book-level coarse length controller gate](../../analysis/book_level_coarse_length_controller_audit_20260622/reports/test_results/01_book_level_coarse_length_controller_gate.md)
- [Final composition index structure audit](../../analysis/composition_index_structure_audit_20260622/reports/final_composition_index_structure_audit.md)
- [Composition index structure gate](../../analysis/composition_index_structure_audit_20260622/reports/test_results/01_composition_index_structure_gate.md)
- [Final minimal external tape program audit](../../analysis/minimal_external_tape_program_audit_20260622/reports/final_minimal_external_tape_program_audit.md)
- [Executable decoder contract](../../analysis/minimal_external_tape_program_audit_20260622/reports/test_results/01_executable_decoder_contract.md)
- [Unified external tape ledger](../../analysis/minimal_external_tape_program_audit_20260622/reports/test_results/02_unified_external_tape_ledger.md)
- [Macro program gate](../../analysis/minimal_external_tape_program_audit_20260622/reports/test_results/03_macro_program_gate.md)
- [Final source tape removal program audit](../../analysis/source_tape_removal_program_audit_20260622/reports/final_source_tape_removal_program_audit.md)
- [Source tape removal program gate](../../analysis/source_tape_removal_program_audit_20260622/reports/test_results/01_source_tape_removal_program_gate.md)
- [Final book-level controller program integration audit](../../analysis/book_level_controller_program_integration_audit_20260622/reports/final_book_level_controller_program_integration_audit.md)
- [Book-level controller program integration gate](../../analysis/book_level_controller_program_integration_audit_20260622/reports/test_results/01_book_level_controller_program_integration_gate.md)
- [Final executable program frontier synthesis audit](../../analysis/executable_program_frontier_synthesis_audit_20260622/reports/final_executable_program_frontier_synthesis_audit.md)
- [Executable program frontier synthesis](../../analysis/executable_program_frontier_synthesis_audit_20260622/reports/test_results/01_executable_program_frontier_synthesis.md)
- [Final joint chunk-origin route audit](../../analysis/joint_chunk_origin_route_audit_20260622/reports/final_joint_chunk_origin_route_audit.md)
- [Joint chunk-origin route gate](../../analysis/joint_chunk_origin_route_audit_20260622/reports/test_results/01_joint_chunk_origin_route_gate.md)
- [Final joint chunk-origin beam pilot audit](../../analysis/joint_chunk_origin_beam_pilot_audit_20260622/reports/final_joint_chunk_origin_beam_pilot_audit.md)
- [Bucket chunk-origin beam pilot](../../analysis/joint_chunk_origin_beam_pilot_audit_20260622/reports/test_results/01_bucket_chunk_origin_beam_pilot.md)
- [Final chunk length-prior integration audit](../../analysis/chunk_length_prior_integration_audit_20260622/reports/final_chunk_length_prior_integration_audit.md)
- [Chunk length-prior integration gate](../../analysis/chunk_length_prior_integration_audit_20260622/reports/test_results/01_chunk_length_prior_integration_gate.md)
- [Final Markov chunk-content prior audit](../../analysis/markov_chunk_content_prior_audit_20260622/reports/final_markov_chunk_content_prior_audit.md)
- [Markov chunk-content prior gate](../../analysis/markov_chunk_content_prior_audit_20260622/reports/test_results/01_markov_chunk_content_prior_gate.md)
- [Final latent-state route synthesis audit](../../analysis/latent_state_route_synthesis_audit_20260622/reports/final_latent_state_route_synthesis_audit.md)
- [Latent-state route synthesis](../../analysis/latent_state_route_synthesis_audit_20260622/reports/test_results/01_latent_state_route_synthesis.md)
- [Final latent nonlocal state program pilot audit](../../analysis/latent_nonlocal_state_program_pilot_audit_20260622/reports/final_latent_nonlocal_state_program_pilot_audit.md)
- [Latent nonlocal state program pilot](../../analysis/latent_nonlocal_state_program_pilot_audit_20260622/reports/test_results/01_latent_nonlocal_state_program_pilot.md)
- [Final schedule-state multistream pilot audit](../../analysis/schedule_state_multistream_pilot_audit_20260622/reports/final_schedule_state_multistream_pilot_audit.md)
- [Schedule-state multistream pilot](../../analysis/schedule_state_multistream_pilot_audit_20260622/reports/test_results/01_schedule_state_multistream_pilot.md)
- [Final book multiset/order factorization audit](../../analysis/book_multiset_order_factorization_audit_20260622/reports/final_book_multiset_order_factorization_audit.md)
- [Book multiset/order factorization gate](../../analysis/book_multiset_order_factorization_audit_20260622/reports/test_results/01_book_multiset_order_factorization_gate.md)
- [Final within-book order program audit](../../analysis/within_book_order_program_audit_20260622/reports/final_within_book_order_program_audit.md)
- [Within-book order program gate](../../analysis/within_book_order_program_audit_20260622/reports/test_results/01_within_book_order_program_gate.md)
- [Final sequence mutation program audit](../../analysis/sequence_mutation_program_audit_20260622/reports/final_sequence_mutation_program_audit.md)
- [Sequence mutation program gate](../../analysis/sequence_mutation_program_audit_20260622/reports/test_results/01_sequence_mutation_program_gate.md)
- [Final generative route frontier synthesis audit](../../analysis/generative_route_frontier_synthesis_audit_20260622/reports/final_generative_route_frontier_synthesis_audit.md)
- [Generative route frontier synthesis](../../analysis/generative_route_frontier_synthesis_audit_20260622/reports/test_results/01_generative_route_frontier_synthesis.md)
- [Final digit content boundary transducer audit](../../analysis/digit_content_boundary_transducer_audit_20260622/reports/final_digit_content_boundary_transducer_audit.md)
- [All-position boundary transducer gate](../../analysis/digit_content_boundary_transducer_audit_20260622/reports/test_results/01_all_position_boundary_transducer_gate.md)
- [Start candidate ranking gate](../../analysis/digit_content_boundary_transducer_audit_20260622/reports/test_results/02_start_candidate_ranking_gate.md)
- [Final paid-control context payload codec audit](../../analysis/paid_control_context_payload_codec_audit_20260622/reports/final_paid_control_context_payload_codec_audit.md)
- [Final parser/decoder frontier synthesis audit](../../analysis/parser_decoder_frontier_synthesis_audit_20260622/reports/final_parser_decoder_frontier_synthesis_audit.md)
- [Final target-free internal start program audit](../../analysis/target_free_internal_start_program_audit_20260622/reports/final_target_free_internal_start_program_audit.md)
- [Final internal start beam capacity audit](../../analysis/internal_start_beam_capacity_audit_20260622/reports/final_internal_start_beam_capacity_audit.md)
- [Final internal start beam control audit](../../analysis/internal_start_beam_control_audit_20260622/reports/final_internal_start_beam_control_audit.md)
- [Internal start beam control gate](../../analysis/internal_start_beam_control_audit_20260622/reports/test_results/01_internal_start_beam_control_gate.md)
- [Final internal start beam paid-control audit](../../analysis/internal_start_beam_paid_control_audit_20260622/reports/final_internal_start_beam_paid_control_audit.md)
- [Internal start beam paid-control gate](../../analysis/internal_start_beam_paid_control_audit_20260622/reports/test_results/01_internal_start_beam_paid_control_gate.md)
- [Final online x64 coarse-control program audit](../../analysis/online_x64_coarse_control_program_audit_20260622/reports/final_online_x64_coarse_control_program_audit.md)
- [Online x64 coarse-control program gate](../../analysis/online_x64_coarse_control_program_audit_20260622/reports/test_results/01_online_x64_coarse_control_program_gate.md)
- [Final executable v2 residual coupling audit](../../analysis/executable_v2_residual_coupling_audit_20260622/reports/final_executable_v2_residual_coupling_audit.md)
- [Executable v2 residual coupling gate](../../analysis/executable_v2_residual_coupling_audit_20260622/reports/test_results/01_executable_v2_residual_coupling_gate.md)
- [Final executable v2 remaining-tape coupling audit](../../analysis/executable_v2_remaining_tape_coupling_audit_20260622/reports/final_executable_v2_remaining_tape_coupling_audit.md)
- [Executable v2 remaining-tape coupling gate](../../analysis/executable_v2_remaining_tape_coupling_audit_20260622/reports/test_results/01_executable_v2_remaining_tape_coupling_gate.md)
- [Final content-addressed event program audit](../../analysis/content_addressed_event_program_audit_20260622/reports/final_content_addressed_event_program_audit.md)
- [Content-addressed event program gate](../../analysis/content_addressed_event_program_audit_20260622/reports/test_results/01_content_addressed_event_program_gate.md)
- [Final event-aligned chunk library audit](../../analysis/event_aligned_chunk_library_audit_20260622/reports/final_event_aligned_chunk_library_audit.md)
- [Event-aligned chunk library gate](../../analysis/event_aligned_chunk_library_audit_20260622/reports/test_results/01_event_aligned_chunk_library_gate.md)
- [Final source-boundary candidate program audit](../../analysis/source_boundary_candidate_program_audit_20260622/reports/final_source_boundary_candidate_program_audit.md)
- [Source-boundary candidate program gate](../../analysis/source_boundary_candidate_program_audit_20260622/reports/test_results/01_source_boundary_candidate_program_gate.md)
- [Final executable v3 source-boundary program audit](../../analysis/executable_v3_source_boundary_program_audit_20260622/reports/final_executable_v3_source_boundary_program_audit.md)
- [Executable v3 source-boundary program gate](../../analysis/executable_v3_source_boundary_program_audit_20260622/reports/test_results/01_executable_v3_source_boundary_program_gate.md)
- [Final executable v3 source-boundary robustness audit](../../analysis/executable_v3_source_boundary_robustness_audit_20260622/reports/final_executable_v3_source_boundary_robustness_audit.md)
- [Executable v3 source-boundary robustness gate](../../analysis/executable_v3_source_boundary_robustness_audit_20260622/reports/test_results/01_executable_v3_source_boundary_robustness_gate.md)
- [Final boundary-mark propagation program audit](../../analysis/boundary_mark_propagation_program_audit_20260622/reports/final_boundary_mark_propagation_program_audit.md)
- [Boundary-mark propagation program gate](../../analysis/boundary_mark_propagation_program_audit_20260622/reports/test_results/01_boundary_mark_propagation_program_gate.md)
- [Final one-sided source-boundary program audit](../../analysis/one_sided_source_boundary_program_audit_20260622/reports/final_one_sided_source_boundary_program_audit.md)
- [One-sided source-boundary program gate](../../analysis/one_sided_source_boundary_program_audit_20260622/reports/test_results/01_one_sided_source_boundary_program_gate.md)
- [Final executable v4 one-sided boundary program audit](../../analysis/executable_v4_one_sided_boundary_program_audit_20260622/reports/final_executable_v4_one_sided_boundary_program_audit.md)
- [Executable v4 one-sided boundary program gate](../../analysis/executable_v4_one_sided_boundary_program_audit_20260622/reports/test_results/01_executable_v4_one_sided_boundary_program_gate.md)
- [Final shared innovation tape audit](../../analysis/shared_innovation_tape_audit_20260622/reports/final_shared_innovation_tape_audit.md)
- [Shared literal-length tape gate](../../analysis/shared_innovation_tape_audit_20260622/reports/test_results/01_shared_literal_length_tape_gate.md)
- [Hybrid innovation tape subcodec gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/17_hybrid_innovation_tape_subcodec_gate.md)
- [Book control header gate](../../analysis/innovation_stream_transducer_audit_20260622/reports/test_results/18_book_control_header_gate.md)
- [Skeleton rule coverage audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/100_skeleton_rule_coverage_audit.md)
- [Skeleton template reuse audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/101_skeleton_template_reuse_audit.md)
- [Type motif library ledger](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/102_type_motif_library_ledger.md)
- [Copy availability type exception ledger](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/103_copy_availability_type_exception_ledger.md)
- [Target position derivation ledger](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/104_target_position_derivation_ledger.md)
- [Optional literal exception rule audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/105_optional_literal_exception_rule_audit.md)
- [Prequential optional literal rule validation](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/106_prequential_optional_literal_rule_validation.md)
- [Operation type dependency ledger](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/107_operation_type_dependency_ledger.md)
- [Recent gates row0 compatibility refresh](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/108_recent_gates_row0_compatibility_refresh.md)
- [Operation length dependency ledger](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/110_operation_length_dependency_ledger.md)
- [Decoder length candidate ambiguity audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/111_decoder_length_candidate_ambiguity_audit.md)
- [Decoder length policy audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/112_decoder_length_policy_audit.md)
- [Final segmentation decision audit](../../analysis/segmentation_decision_audit_20260621/reports/final_segmentation_decision_audit.md)
- [Segmentation decision trace](../../analysis/segmentation_decision_audit_20260621/reports/test_results/01_segmentation_decision_trace.md)
- [Structural segmentation hypothesis audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/02_structural_segmentation_hypothesis_audit.md)
- [Parser dependency reduction ledger](../../analysis/segmentation_decision_audit_20260621/reports/test_results/04_parser_dependency_reduction_ledger.md)
- [Literal gap boundary audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/05_literal_gap_boundary_audit.md)
- [Online literal stop rule audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/06_online_literal_stop_rule_audit.md)
- [Literal stop exception topology audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/07_literal_stop_exception_topology_audit.md)
- [Integrated online literal parser audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/08_integrated_online_literal_parser_audit.md)
- [Integrated parser policy and drift audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/09_integrated_parser_policy_and_drift_audit.md)
- [Integrated parser override audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/10_integrated_parser_override_audit.md)
- [Integrated parser peak strength audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/11_integrated_parser_peak_strength_audit.md)
- [Integrated parser residual context audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/12_integrated_parser_residual_context_audit.md)
- [Global objective parser audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/13_global_objective_parser_audit.md)
- [Feature weighted global parser audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/14_feature_weighted_global_parser_audit.md)
- [Source boundary alignment audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/15_source_boundary_alignment_audit.md)
- [Single drift repair oracle audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/16_single_drift_repair_oracle_audit.md)
- [Observable repair policy audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/17_observable_repair_policy_audit.md)
- [Conditional repair classifier audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/18_conditional_repair_classifier_audit.md)
- [Two-stage conditional repair audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/19_two_stage_conditional_repair_audit.md)
- [Post-repair residual oracle audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/20_post_repair_residual_oracle_audit.md)
- [Post-repair residual feature audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/21_post_repair_residual_feature_audit.md)
- [Residual branch continuation audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/22_residual_branch_continuation_audit.md)
- [Branch ranker prequential audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/23_branch_ranker_prequential_audit.md)
- [Contextual mode selector audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/24_contextual_mode_selector_audit.md)
- [Contextual mode stability audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/25_contextual_mode_stability_audit.md)
- [Hierarchical context backoff audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/26_hierarchical_context_backoff_audit.md)
- [Observable decision tree policy audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/27_observable_decision_tree_policy_audit.md)
- [Target boundary recurrence audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/28_target_boundary_recurrence_audit.md)
- [Future copy opportunity audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/29_future_copy_opportunity_audit.md)
- [Source state continuity audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/30_source_state_continuity_audit.md)
- [Global source state continuity audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/31_global_source_state_continuity_audit.md)
- [Phase grid segmentation audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/32_phase_grid_segmentation_audit.md)
- [Context nearest branch audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/33_context_nearest_branch_audit.md)
- [Structural signal consensus audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/34_structural_signal_consensus_audit.md)
- [Structural vote residual decomposition](../../analysis/segmentation_decision_audit_20260621/reports/test_results/35_structural_vote_residual_decomposition.md)
- [Branch choice frontier closure audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/36_branch_choice_frontier_closure_audit.md)
- [Path template reuse audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/37_path_template_reuse_audit.md)
- [Trajectory neighbor parser audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/38_trajectory_neighbor_parser_audit.md)
- [Observable state support audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/39_observable_state_support_audit.md)
- [Latent state requirement audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/40_latent_state_requirement_audit.md)
- [Latent state lookup cost gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/41_latent_state_lookup_cost_gate.md)
- [Compact latent rule frontier](../../analysis/segmentation_decision_audit_20260621/reports/test_results/42_compact_latent_rule_frontier.md)
- [Source-free residual rule gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/43_source_free_residual_rule_gate.md)
- [Operation n-gram grammar gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/44_operation_ngram_grammar_gate.md)
- [Residual exception transfer gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/45_residual_exception_transfer_gate.md)
- [Branch rank position audit](../../analysis/segmentation_decision_audit_20260621/reports/test_results/46_branch_rank_position_audit.md)
- [Branch rank exception cost gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/47_branch_rank_exception_cost_gate.md)
- [Residual site detector gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/48_residual_site_detector_gate.md)
- [Book skeleton alignment gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/49_book_skeleton_alignment_gate.md)
- [Source interval context gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/50_source_interval_context_gate.md)
- [Source interval precision gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/51_source_interval_precision_gate.md)
- [Source interval observable precision gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/52_source_interval_observable_precision_gate.md)
- [Source interval cost gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/53_source_interval_cost_gate.md)
- [Book-start copy subclass gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/54_book_start_copy_subclass_gate.md)
- [Observable signature support gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/55_observable_signature_support_gate.md)
- [Sequential signature support gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/56_sequential_signature_support_gate.md)
- [Latent path-state budget gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/57_latent_path_state_budget_gate.md)
- [Beam survival budget gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/58_beam_survival_budget_gate.md)
- [Beam rank selector gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/59_beam_rank_selector_gate.md)
- [Beam selector stability gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/60_beam_selector_stability_gate.md)
- [Beam hierarchical backoff gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/61_beam_hierarchical_backoff_gate.md)
- [Residual patch program gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/62_residual_patch_program_gate.md)
- [Beam Markov state selector gate](../../analysis/segmentation_decision_audit_20260621/reports/test_results/63_beam_markov_state_selector_gate.md)
- [Final seed primacy audit](../../analysis/seed_primacy_audit_20260621/reports/final_seed_primacy_audit.md)
- [Prequential seed selection audit](../../analysis/seed_primacy_audit_20260621/reports/test_results/03_prequential_seed_selection_audit.md)
- [Seed requirement closure audit](../../analysis/seed_primacy_audit_20260621/reports/test_results/04_seed_requirement_closure_audit.md)
- [Seed primacy integration audit](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/109_seed_primacy_integration_audit.md)
- [Literal payload default decodability audit](../../analysis/authorial_mechanism_20260620/reports/test_results/138_literal_payload_default_decodability_audit.md)
- [Literal payload structural context audit](../../analysis/authorial_mechanism_20260620/reports/test_results/139_literal_payload_structural_context_audit.md)
- [Literal payload model gate](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/29_literal_payload_model_gate.md)
- [Authorial provenance source notes](../../analysis/authorial_provenance_audit_20260621/reports/authorial_provenance_source_notes.md)
- [Chayenne spacing audit](../../analysis/authorial_provenance_audit_20260621/reports/test_results/01_chayenne_spacing_audit.md)
- [V4 unanchored copy residual audit](../../analysis/v4_unanchored_copy_residual_audit_20260622/reports/final_v4_unanchored_copy_residual_audit.md)
- [Unanchored copy-origin representation audit](../../analysis/unanchored_copy_origin_representation_audit_20260622/reports/final_unanchored_copy_origin_representation_audit.md)
- [Executable v5 source-endpoint memory audit](../../analysis/executable_v5_source_endpoint_memory_audit_20260622/reports/final_executable_v5_source_endpoint_memory_audit.md)
- [Joint content-origin program audit](../../analysis/joint_content_origin_program_audit_20260622/reports/final_joint_content_origin_program_audit.md)
- [Executable v6 literal-span origin audit](../../analysis/executable_v6_literal_span_origin_audit_20260622/reports/final_executable_v6_literal_span_origin_audit.md)
- [Causal event graph program audit](../../analysis/causal_event_graph_program_audit_20260622/reports/final_causal_event_graph_program_audit.md)
- [Innovation lineage basis audit](../../analysis/innovation_lineage_basis_audit_20260622/reports/final_innovation_lineage_basis_audit.md)
- [Lineage signature library audit](../../analysis/lineage_signature_library_audit_20260622/reports/final_lineage_signature_library_audit.md)
- [Residual content-basis program audit](../../analysis/residual_content_basis_program_audit_20260622/reports/final_residual_content_basis_program_audit.md)
- [Residual content-fingerprint program audit](../../analysis/residual_content_fingerprint_program_audit_20260622/reports/final_residual_content_fingerprint_program_audit.md)
- [Seed bootstrap copy-surface audit](../../analysis/seed_bootstrap_copy_surface_audit_20260622/reports/final_seed_bootstrap_copy_surface_audit.md)
- [Seed bootstrap transducer program audit](../../analysis/seed_bootstrap_transducer_program_audit_20260622/reports/final_seed_bootstrap_transducer_program_audit.md)
- [Seed bootstrap decision-policy audit](../../analysis/seed_bootstrap_decision_policy_audit_20260622/reports/final_seed_bootstrap_decision_policy_audit.md)

## Executable v5 source-endpoint memory

The latest executable-program increment promotes `source_endpoint_memory` as a
small residual reduction, not as a complete generator. Once a copy source is
paid or derived, its source-side endpoints become reusable online marks for
future source-interval derivation. The executable decoder still roundtrips
`70/70` books. External bits excluding seed fall from v4 `4109.138` to v5
`4097.333`, a reduction of `11.805` bits after charging `1.585` bits to declare
the representation family. Copy classes shift to `52` fully-derived intervals,
`55` end-only intervals, and `101` fallback copy-hint intervals.

This changes the executable dependency ledger only. It does not change `row0`,
plaintext, translation, semantics, or the separate `compression_bound`.

## Literal-span content-origin subprogram

The v5 frontier synthesis identifies copy fallback identity, literal payload,
and residual composition as the main non-seed blockers. A joint content-origin
gate then tests whether fallback copy sources can be addressed through already
emitted content origins instead of an independent copy-hint tape. The promoted
piece is narrow: `literal_span_offset` applies to only `11/101` v5 fallback
copy events, but it costs `858.798` bits after declaration versus `891.118`
copy-hint bits, saving `32.320` bits. It has `4/5` positive prefix holdout
splits and beats the random source-position p05 control (`858.798` vs
`875.078`).

Integrated as a limited executable-ledger reduction, this moves external bits
excluding seed from v5 `4097.333` to `4065.013`. It is not a complete
content-origin generator: most fallback copy origins, literal payload, seed
payload, `row0`, plaintext, translation, semantics, and the separate
`compression_bound` remain unchanged.

The executable v6 closure integrates that subprogram into the decoder contract.
Roundtrip remains `70/70`; copy classes become `52` both-endpoint intervals,
`55` end-only intervals, `11` literal-span sources, and `90` fallback copy
hints. The replaced subset previously cost `111.547` copy-hint bits and is now
addressed by `76.905` literal-span offset bits plus model declaration. This
closes the v6 bookkeeping and leaves the next main question at the event-graph
level, not another isolated source/endpoint codec.

The causal event graph audit then tests that main question. It converts the v6
decoder into a graph of seed spans, literal innovation spans, copy intervals,
operation spans, source-boundary/endpoint marks, and causal edges. As a ledger
the graph is useful, but prefix/family macro induction does not become a
smaller generator: `72` split-stream rows are tested, the best macro delta is
still `+88.238` bits versus direct event labels, `0` rows are positive, only
`2/72` beat shuffled p05, and shuffled literal tape preserves `0/53` literal
chunks. The result is `causal_event_graph_program_not_promoted`; the blocker
remains origin of innovation/content, not another isolated local selector.

An innovation-lineage basis audit then tests that blocker directly. It
propagates every emitted digit back to a seed or literal innovation atom and
asks whether the remaining `90` v6 fallback copy origins can be addressed in
that basis. The provenance is informative (`55/90` sources are contiguous
single-atom intervals, all from seed atoms), but the paid address program is
worse: `1022.251` bits versus `779.571` copy-hint bits, `0/5` positive prefix
splits, and no win against randomized-lineage controls. The lineage basis is
therefore retained as provenance only, not as a generator.

A follow-up lineage-signature library gate asks whether those remaining
fallback chunks share reusable causal signatures rather than event-by-event
copy hints. They do not under the paid tests: the best
`signature_kind_run_lengths` family needs `63` signatures and costs
`1516.786` bits versus `779.571` copy-hint bits (`+737.215`), with `0/5`
positive prefix splits and no shuffled-control win. This keeps the blocker at
content/origin selection, not graph organization.

A constructive content-basis gate then tests that blocker more directly. A
paid fallback chunk may enter an online basis, and later fallback chunks may be
generated by exact or substring reference to that basis. The route still does
not promote: exact reuse hits only `1/90` and costs `+3.419` bits versus the
current copy-hint tape, while substring reuse hits `38/90` but costs
`+157.970` bits. Prefix support is `0/5`, family support is `0`, and shuffled
controls are not beaten. Residual content origin therefore remains external.

A paid content-fingerprint gate tests the same blocker from the other side:
given exact length, can a short prefix/suffix/edge fingerprint select the
copied chunk from prior material more cheaply than a copy hint? No. The best
policy is `prefix_1`, already `+245.804` bits worse than copy-hint and with
`0` unique content selections. Longer edge fingerprints eventually become
unique (`edge_8` has `90/90` unique selections), but at `+1549.686` bits. The
route is therefore not a smaller content-selection program.

The next constructive pivot is seed bootstrap, because the v6 ledger still pays
books `0..9` as `1696` raw digits (`5633.990` bits). A target-conditioned
copy-surface audit finds that this field is not random-looking under previous
copy: at `min_len=4`, `1335/1696` seed digits are copy-covered, versus
same-multiset shuffled p95 `534`. The clue is strong across min_lens
`[4, 5, 6, 8, 10, 12]`, but it is still only a surface clue. Book-order
permutation controls show that most of the signal comes from repeated content,
not from proving canonical `0..9` as authorial seed order. The next real gate is
a target-free bootstrap policy that derives seed copy starts/choices from a
smaller innovation tape.

The first target-free bootstrap policy gate does not promote. It grants the
seed book lengths, the `361`-digit literal tape from the surface parse, and one
deterministic context-copy policy. The best policy (`context=4`, `copy_len=4`,
`latest`) matches only the first `55` seed digits before correction, yields
`0/10` exact seed books, and costs `6656.992` bits after raw suffix correction:
`+1023.002` worse than the raw seed payload. Shuffled literal-tape controls
show the prefix is non-random (`p95=1`), but the policy still does not reduce
the executable ledger. The blocker is now more precise: repeated seed content
exists, but the copy-start/source-length decision policy is still missing.

A teacher-forced decision-policy audit isolates that blocker. On the true seed
prefix path, with suffix-repeat features and the literal-tape pointer visible,
simple prefix-selected rules reach only `0.446` mean holdout accuracy, below
shuffled-label p95 `0.847`. The selected rule has high precision when it calls
copy, but copy recall is only about `0.08-0.10` on nonempty splits, so it
mostly learns not to copy. This demotes simple visible-state copy/literal rules
as a bootstrap path; any future seed generator needs a richer decision state or
a different innovation process.

## Boundary

This page changes the mechanical model, not the semantic verdict. Future work
should treat the adaptive bounded copy-length plus Rice literal-length sequential LZ formula,
the one-step literal-to-copy repair, the signed-Rice book-length ledger,
min_len-bounded digit-only copy addresses, and the digit-address literal repair,
plus the adaptive/Markov/book-start/literal-force item-type ledgers,
remaining-short forced-literal rule, forced short-suffix literal lengths, the
final forced-length local repair, retained absolute `source_digit_pos`
addresses, and
the previous-emitted-digit literal payload context model with declared order
`2`, the item-type context-order ledger with declared order `3`, and the
contextual copy-to-literal repair plus one minaddr local literal-to-copy repair,
one post-minaddr local literal-to-copy repair, and the adaptive copy-length
index ledger with `alpha=2`, plus a fixed book-midpoint context for that
copy-length prior and final `alpha=1`, plus a declared item-type prior split at
book `6` with split-only item-type coding, plus the deterministic online
reparse compile, the decodable copy-length default/exception ledger, and the
decodable copy-source default/exception ledger, as the current strongest
copy/reference fabrication bound at roughly `8177.3` bits.
Follow-up
literal-to-copy repairs,
immediate copy-to-literal repairs or pairs, alternate decodable address
ledgers, post-repair2 address-model retests, and post-repair2 parameter
resweeps, plus post-repair2 copy-order and post-adaptive local-frontier retests,
plus post-adaptive parameter, pair-frontier, address-model, and copy-order
resweeps, the post-midpoint local frontier, and the post-midpoint alpha1 local
frontier plus pair frontier, address-model retest, and copy-order retest do
not improve the current frontier; the post-alpha1 context resweep retains the
midpoint context, and the per-context alpha grid retains shared `alpha=1`.
The literal-payload context search also retains the global payload model; the
bounded top60 triple probe does not improve the current frontier inside its
declared scope. The post-itemctx parameter resweep promotes only the item-type
extra-context parameter, not a new recipe, row0 origin, or semantic reading.
The post-itemctx_param local and pair frontiers do not improve the current
frontier. The post-itemctx_param address and copy-order retests also remain
optimistic-only or worse after decodable mode/address costs. The
post-itemctx_param copy-length context and context-alpha retests retain the
fixed midpoint `alpha=1` model. The post-itemctx_param literal-payload context
search also retains the global payload model. The post-itemctx_param item-type
context family sweep retains the active split `6`, order `1`, alpha `2` model.
The joint payload/item-type and copy-length/item-type context sweeps also
retain that active pair, the triple sweep retains the same active triple, and
the copy-length alpha/item-type and alpha/payload sweeps retain the same active
pair. The copy-alpha/payload/item-type triple sweep retains the same active
triple. The copy-length context/shared-alpha resweep retains the same active
book-midpoint `alpha=1` context. The literal-payload context/shared-alpha
resweep retains the same active global `alpha=1` payload model. The
copy/payload context-alpha pair search retains the same active pair. The
copy/payload/item context-alpha triple search retains the same active triple.
The address/copy-order pair search retains the same active decodable copy-cost
ledger and records only a nondecodable lower bound. The address/item-type pair
search also retains the same active decodable pair and records only a
nondecodable lower bound. The address/payload context-alpha pair search also
retains the same active decodable pair and records only a nondecodable lower
bound. The prequential audit freezes this state as `compression_bound` and
moves the mainline progress bar to holdout behavior, structural mechanism,
simplification, or row0 origin evidence. The item-type/op-shape boundary keeps
split-only item-type coding as a retained sequence model while treating compact
recipe op `type` fields as derivable representation only.
Continue
testing matrix origin, topology holdouts, and official source watchlists under
the same Outcome Ledger.
