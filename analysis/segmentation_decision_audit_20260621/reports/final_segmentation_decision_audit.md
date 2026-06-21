# Final Segmentation Decision Audit

Status: `analysis_only`
Classification: `PROMOTED_MECHANICAL_SEGMENTATION_CLUE` for parser segmentation; `AUDIT_ONLY` for source-free generation.
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Can the retained `(source,length)` decisions be explained as a
mechanical segmentation/parser rule rather than another local bit
sweep?

## Main Result

On the stable copy projection used by the recent length gates, the rule
`choose the longest previous target match; break source ties by earliest source`
recovers `207/208`
copy pairs.

This is a real mechanical parser clue: it sharply reduces the declared
`(source,length)` dependency for copy segmentation when the target book
text is being parsed. It is not a source-free generator for the 70 books,
because it still requires the target suffix as input and has one
exception.

## Trace Coverage

- Reference skeleton operations: `261`.
- Stable-projection operations traced: `262`.
- Copy decisions traced: `208`.
- Candidate pair median: `80.000`.
- Candidate pair max: `1248.0`.
- Declared copy equals source-local target max: `207/208`.
- Stable-projection literal gaps: `54` with `265` literal digits.

The stable projection has one more literal gap than the reference
skeleton ledger (`54` vs `53`) and one fewer literal digit (`265` vs
`266`). This report therefore treats the finding as a copy-segmentation
parser clue, not a replacement for the full skeleton ledger.

## Structural Hypotheses

| Hypothesis | Result | Boundary |
|---|---:|---|
| Longest previous target match + earliest source | `207/208` | parser clue, target-text-aware |
| Random source among global-max matches | expected `119.739/208` | negative control |
| Unique global-max source forcing | `78/208` rows | partial only |
| Recurrent next boundary preserved | `123/208` | weak clue, not sufficient |
| Stop before max protects literal payload | `0/208` | rejected |

## Exception

| Book | Op | Projection copy | Declared length | Max length | Candidate pairs | Declared boundary pairs | Max boundary pairs |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `55` | `2` | `2` | `44` | `45` | `95` | `7` | `0` |

## Decision

- Found a strong target-text-aware parser rule for copy segmentation.
- Did not find a source-free generation rule for the book digits.
- Reduced the practical copy `(source,length)` blocker to: target text must be available, stable projection must be accepted, and one exception remains.
- Rejected the literal-payload-protection shortcut and weakened recurrent-boundary explanations.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, fan gloss, semantic reading, or case reopening is introduced.

## Dependency Reduction Ledger

| Representation | Operation/skeleton records | Literal chunks | Copy/source exception records | Parser rule records | Total materialized records |
|---|---:|---:|---:|---:|---:|
| Exact skeleton ledger | `261` | `53` | `208` | `0` | `522` |
| Target-text parser projection | `262` | `54` | `1` | `1` | `318` |

- Materialized record delta: `-204`.
- Conditional copy `(source,length)` fields removed: `414`.
- Full greedy source-free parser exact books: `39/60`.
- Full greedy mismatch books: `[10, 12, 13, 14, 16, 17, 23, 25, 26, 32, 34, 38, 39, 42, 44, 49, 52, 55, 57, 58, 65]`.

The dependency reduction is therefore real but conditional. It needs
target text and the stable projection's copy starts; it does not derive
the full operation sequence source-free.

## Literal Gap Boundary

| Hypothesis | Result | Boundary |
|---|---:|---|
| Stop at first available match | `23/54` | rejected |
| Stop at local-window best literal+copy advance | `54/54` | declared-window clue |
| Stop at full-suffix best literal+copy advance | `11/49` | source-free rule rejected |

- Copy was already available at literal start in `17` gaps.
- Future stable copy improves immediate copy in `48` followed-by-copy gaps.

This explains why first-match greedy parsing fails: stable literal gaps
often wait for a better next copy. But the explanation is still
conditioned on the declared literal window; it does not derive that
window source-free.

## Online Literal Stop Rule

| Rule | Result | Boundary |
|---|---:|---|
| First confirmed max-copy local peak, window `6` | `45/49` followed-by-copy gaps | partial online clue |
| Same rule plus book-end default | `50/54` literal gaps | partial parser rule |

- Prequential cells: `5`.
- Selected policy matches suffix oracle in `3/5` cells.
- Promotes source-free literal stop rule: `False`.

This reduces the literal-window blocker further: most starts are now
explained by an online local-peak rule, but four followed-by-copy gaps
remain exceptions.

## Literal Stop Exception Topology

- Exception count: `4`.
- Exception classes: `{'book_start_overstop': 1, 'book_start_understop': 1, 'long_internal_understop': 1, 'microgap_zero_offset_understop': 1}`.
- Best source-free exception flag: `source_free_predicted_copy_le8` with recall `0.750` and `9` false positives.
- Promotes exception rule: `False`.

The residual exceptions are heterogeneous; no source-free exception
flag isolates all four without false positives.

## Integrated Online Parser

The online stop rule was then frozen and run as an end-to-end
target-text-aware parser, without granting declared literal windows
or copy starts.

| Parser | Exact books | Operations | Literal digits | Boundary |
|---|---:|---:|---:|---|
| Full greedy control | `39/60` | n/a | n/a | earlier control |
| Integrated online stop + longest copy | `46/60` | `268` vs stable `262` | `329` vs stable `265` | partial parser, not promoted |

- Exact-book delta vs full greedy: `7`.
- Mismatch books: `[14, 16, 20, 21, 26, 28, 30, 34, 36, 39, 45, 55, 57, 63]`.

This is a real parser improvement over first-match greedy, but it
still drifts in `14/60` books and over-literalizes the stable
projection. The integrated parser therefore reduces the segmentation
blocker but does not replace the retained operation-start ledger or
emit a source-free generator.

## Integrated Parser Policy Frontier

A follow-up gate retuned the same local-peak stop family as an
integrated parser, rather than scoring stops inside known literal
windows.

| Policy | Exact books | Drift books | Boundary |
|---|---:|---:|---|
| First-match greedy | `39/60` | `21` | rejected baseline |
| Gate-08 active `max_copy_length:window6` | `46/60` | `14` | partial parser |
| Best prefix-stable `max_copy_length:window5` | `48/60` | `12` | partial, not promoted |

- Prequential selected policy matches suffix oracle in `5/5` cells.
- Best-policy drift classes: `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 4}`.

The window-5 policy is a real integrated-parser improvement and is
stable under prefix policy selection, but it still leaves `12/60`
books mismatched. The remaining topology mixes missed book-start
copies, missed internal copies, literal understops, and one copy
length drift, so the local-peak family is not a complete
segmentation mechanism.

## Immediate-Copy Override Control

The next obvious structural rescue is to override the local-peak
wait rule when a strong copy is already available. Gate 10 tests
book-start, internal, and any-position immediate-copy overrides
across thresholds `5..20`.

| Family | Best exact books | Selected by prefix? | Boundary |
|---|---:|---|---|
| No override baseline | `48/60` | yes | retained |
| Immediate-copy overrides | `48/60` | `3/5` oracle cells | rejected |

- Best policy: `window5:no_override`.
- Exact-book improvement vs baseline: `0`.

The override family does not improve the parser. In the problematic
middle prefix cells it overfits train books and loses held-out
suffix books, especially through false book-start copies. The
remaining segmentation blocker is therefore not a simple
immediate-copy/missed-copy threshold.

## Peak-Strength Control

The opposite rescue is to wait for a stronger local peak before
ending a literal run, aiming to fix literal-understop drifts.

| Family | Best exact books | Boundary |
|---|---:|---|
| Window-5 baseline | `48/60` | retained |
| Minimum peak strength | `48/60` | rejected |

- Best policy: `window5:min_peak_len5`.
- Exact-book improvement vs baseline: `0`.
- Prequential selected policy matches suffix oracle in `3/5` cells.

Raising the minimum accepted peak does not improve exact coverage.
The first alternate threshold, `min_peak_len6`, ties `48/60` but
increases literal digits and turns some understops into missed-copy
and overstop failures; larger thresholds degrade sharply. The
remaining literal-understop cases are therefore not solved by a
simple weak-peak filter.

## Residual Context Predicate Control

After local-threshold rescues failed, gate 12 asks whether simple
observable parser-state predicates can identify the remaining
first-drift decisions well enough to become correction rules.

| Predicate family | Best result | Boundary |
|---|---|---|
| `peak_len_le5` | TP/FP/FN `4/3/8`, precision `0.571`, recall `0.333` | rejected |

- Decision rows: `221`.
- Error rows: `12`.
- Predicate count: `64`.
- Prequential selected predicate matches suffix oracle in `2/5` cells.

The best simple flag, `peak_len_le5`, catches only `4/12` residual
errors and also flags clean decisions. Broader predicates catch more
errors only by creating many false positives. The remaining drift
therefore looks like a mixed path/state problem rather than a
single observable local context rule.

## Global Objective Parser Control

Gate 13 tests a broader path-state hypothesis: dynamic programming
per book under simple global objectives over operations, literal
mass, and copy mass, without declared operation starts.

| Parser family | Best exact books | Boundary |
|---|---:|---|
| Window-5 local parser | `48/60` | retained baseline |
| Simple global objectives | `23/60` | rejected |

- Best objective: `balanced_ops_literals`.
- Exact-book delta vs window5: `-25`.
- Prequential selected objective matches suffix oracle in `5/5` cells.

The global DP objectives are stable but wrong: the best reaches only
`23/60`, far below the `48/60` local-parser baseline. Simple
global minimization of ops, literals, copies, or copy mass therefore
does not explain the retained stable segmentation. Any next path-state
model needs a richer learned or structural cost, not a crude global
objective.

## Feature-Weighted Global Parser Control

Gate 14 tests whether a small structural cost can rescue the global
DP approach: literal mass, copy base cost, copy-length reward,
short-copy penalty, and book-start-copy penalty.

| Parser family | Best exact books | Boundary |
|---|---:|---|
| Window-5 local parser | `48/60` | retained baseline |
| Feature-weighted DP profiles | `26/60` | rejected |

- Best profile: `no_copy_reward`.
- Exact-book delta vs window5: `-22`.
- Prequential selected profile matches suffix oracle in `2/5` cells.

The richer cost family improves over crude objectives only slightly
(`26/60` vs `23/60`) and remains far below the local `window5`
parser. A small linear feature cost over obvious copy/literal
features is therefore not the missing segmentation mechanism.

## Source Boundary Alignment Control

Gate 15 tests the structural block/chunk hypothesis that copies
reuse already segmented source-side operation chunks.

| Boundary measure | Hits |
|---|---:|
| Source starts on prior operation boundary | `28/208` |
| Source ends on prior operation boundary | `29/208` |
| Source interval equals one prior chunk | `0/208` |

- Best boundary-aware source tie policy: `both_boundaries_then_earliest` with `206/208` hits.
- Lift vs existing earliest-source rule: `-1`.

Source-side chunk boundaries do not explain the retained
segmentation. Boundary-aware tie-breakers are worse than the
existing earliest-source global-max rule, so the block-copy
hypothesis is rejected as a generation mechanism.

## Single-Drift Repair Oracle

Gate 16 asks whether the `12/60` integrated-parser drift
books are first-decision failures or deeper path failures.
It grants a stable-projection oracle only as a diagnostic
repair, then resumes the same `window5` parser.

| Oracle correction budget | Exact books | Residual repairs |
|---:|---:|---:|
| `0` | `48/60` | `0` |
| `1` | `59/60` | `11` |
| `2` | `60/60` | `12` |
| `3` | `60/60` | `12` |
| `4` | `60/60` | `12` |
| `5` | `60/60` | `12` |

- One oracle correction repairs `11/12` residual books.
- Two oracle corrections repair all `12/12` residual books.
- Full-oracle correction histogram: `{'1': 11, '2': 1}`.

This is an important blocker localization: most remaining
parser failures are isolated first-drift decisions, not
long unstable paths. It is still not a promoted rule because
the correction itself is chosen from the stable projection.

## Observable Repair Policy Control

Gate 17 tests whether the gate-16 oracle repairs can be
replaced by small observable parser actions: immediate-copy
forcing, book-start/internal copy forcing, next-peak literal
delay, short-copy literal substitution, copy shortening by one,
and one combined policy.

| Policy family | Exact books | Boundary |
|---|---:|---|
| Baseline `window5` | `48/60` | retained |
| Best observable repair policy `baseline_window5` | `48/60` | rejected |

- Exact delta vs baseline: `0`.
- Prequential selected matches oracle cells: `3/5`.

The first-drift oracle map does not yet convert into a small
observable repair rule. The baseline remains the best policy,
and train-selected repair actions overfit in the middle prefix
splits.

## Conditional Repair Classifier

Gate 18 tests a restricted classifier family: one observable
predicate plus one observable repair action, applied end-to-end
and selected under prefix/holdout.

| Parser | Exact books | Boundary |
|---|---:|---|
| Baseline `window5` | `48/60` | retained baseline |
| Best conditional classifier `if_peak_len_le5_then_skip_to_next_peak_ge5` | `50/60` | partial, not promoted |

- Exact delta vs baseline: `2`.
- Repairs applied by best classifier: `4`.
- Prequential selected matches oracle cells: `5/5`.
- Remaining mismatch books: `[14, 16, 20, 21, 26, 34, 39, 45, 55, 57]`.

This is the first non-oracle repair classifier in this front
to improve the integrated parser under prefix-stable selection.
It narrows the residual literal-understop class, but it still
leaves ten mixed drift books and therefore does not promote a
complete segmentation mechanism.

## Two-Stage Conditional Repair Control

Gate 19 keeps the gate-18 classifier as first stage and tests
whether one additional observable predicate-action rule can
close more of the remaining drift.

| Pipeline | Exact books | Boundary |
|---|---:|---|
| Active first stage `if_peak_len_le5_then_skip_to_next_peak_ge5` | `50/60` | retained |
| Best two-stage pipeline `if_peak_len_le5_then_skip_to_next_peak_ge5` | `50/60` | rejected as second-stage gain |

- Exact delta vs active first stage: `0`.
- Prequential selected matches oracle cells: `3/5`.

A second simple observable rule does not improve the parser.
The best pipeline is still the single gate-18 classifier, and
train-selected second-stage repairs overfit in the middle
prefix splits.

## Post-Repair Residual Oracle

Gate 20 keeps the gate-18 non-oracle classifier active,
then grants stable-projection repairs only as a diagnostic
upper bound for the remaining drift books.

| Oracle correction budget | Exact books | Residual repairs |
|---:|---:|---:|
| `0` | `50/60` | `0` |
| `1` | `59/60` | `9` |
| `2` | `60/60` | `10` |
| `3` | `60/60` | `10` |
| `4` | `60/60` | `10` |
| `5` | `60/60` | `10` |

- One oracle correction repairs `9/10` residual books.
- Two oracle corrections repair all `10/10` residual books.
- Full-oracle correction histogram: `{'1': 9, '2': 1}`.
- First-oracle correction classes: `{'book_start_copy_missed_as_literal': 3, 'copy_length_drift_same_source': 1, 'copy_started_inside_stable_literal': 1, 'internal_copy_missed_as_literal': 3, 'literal_understop': 2}`.

The remaining drift is still mostly first-decision local
under an oracle view: only book `20` needs two corrections.
This narrows the next classifier target, but does not promote
a parser because the repair choices come from the stable
projection.

## Post-Repair Residual Feature Screen

Gate 21 asks whether the gate-20 residual oracle map has a
non-oracle observable feature signature. The ten first residual
drifts are scored as positives against active-parser aligned
decisions before any drift as negative controls.

| Screen | Result | Boundary |
|---|---:|---|
| Best overall predicate `active_literal_immediate_copy_ge1` | TP/FP/FN `6/13/4` | rejected |
| Best zero-FP predicate `active_literal_immediate_copy_ge5__and__remaining_le20` | `1/10` residuals | too narrow |
| Full zero-FP detector | `None` | absent |

- Clean decision controls: `224`.
- Predicates tested: `365`.
- Prequential zero-test-FP cells: `0/5`.
- Prequential cover-all-test-residual cells: `1/5`.

The residual errors are not separated by a simple feature flag.
The missed-copy subset is visible as an opportunity class, but
the same signature fires on already-correct parser decisions.
The remaining blocker therefore remains a richer path/state
segmentation rule rather than a single residual predicate.

## Residual Branch Continuation Control

Gate 22 tests the next path-state hypothesis: maybe the
stable residual operation is selected by how the active
parser continues after a forced first branch. Non-oracle
objectives may select only observable local branches; the
stable projection is used only as the evaluation label.

| Objective | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---|
| Oracle stable-prefix diagnostic | `10/10` | `0` | label-only upper bound |
| Best non-oracle `balanced_ops_literals` | `6/10` | `20` | rejected |

- Residual stable operations available as observable candidates: `10/10`.
- Clean controls: `224`.
- Prequential zero-clean-false-change cells: `0/5`.
- Prequential cover-all-test-residual cells: `1/5`.

The branch grammar is broad enough to include every stable
residual operation, but simple continuation objectives still
fail: the best non-oracle objective repairs only part of the
residual set and changes already-correct controls. The missing
mechanism is therefore not just a first-branch objective over
operation count, literal mass, or copied mass.

## Branch Ranker Prequential Control

Gate 23 tests whether a small pairwise branch ranker can learn
the missing path/state preference from prefix books. The ranker
uses observable branch and continuation features; stable
projection is used only as the train/evaluation label.

| Model | Total hits | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---:|---|
| Active branch baseline | `224/234` | `0/10` | `0` | retained control |
| Best full-fit ranker `residual_weight20` | `223/234` | `0/10` | `1` | rejected |

- Training modes: `['uniform', 'residual_weight5', 'residual_weight20', 'residual_only']`.
- Prequential zero-clean-false-change cells: `1/5`.
- Prequential cover-all-test-residual cells: `1/5`.

The learned ranker does not improve the retained active parser.
Modes that preserve clean controls still miss all residuals,
while residual-only weighting can hit some residual branches
only by destroying the clean-control path. This rejects a
small learned branch ranker as the missing generative parser.

## Contextual Mode Selector Control

Gate 24 tests a finite observable state table: each context
family learns which non-oracle branch objective to use from
stable labels, then is evaluated under prefix/holdout.

| Selector | Total hits | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---:|---|
| Active branch baseline | `224/234` | `0/10` | `0` | retained control |
| Best full-fit context `context_combo` | `229/234` | `5/10` | `0` | weak full-fit clue only |

- Context families tested: `10`.
- Prequential zero-clean-false-change cells: `1/5`.
- Prequential cover-all-test-residual cells: `1/5`.
- Prequential selected matches oracle cells: `3/5`.

A finite context table shows a real full-corpus signal:
the best observable context resolves half of the residuals
without false clean-control changes. It is still not promoted
because the same selector is not prefix/holdout stable and
does not cover future residuals reliably.

## Contextual Mode Stability Control

Gate 25 stress-tests the gate-24 `context_combo` full-fit
signal with support pruning, leave-one-book retraining, and
leave-context-out retraining.

| Test | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---|
| Full-fit `context_combo` | `5/10` | `0` | weak clue |
| Leave-one-book | `1/10` | n/a | rejected |
| Leave-context-out | `0/10` | n/a | rejected |

- Best supported threshold: `1`.
- Support thresholds tested: `5`.

The apparent context signal is not stable: most of the full-fit
residual repairs disappear when the held-out book is removed
from training or when low-support buckets are pruned. This
reclassifies the context table as a weak post-hoc clue, not
a generative parser rule.

## Hierarchical Context Backoff Control

Gate 26 tests whether the gate-25 failure was only context
sparsity. It trains observable context hierarchies and backs
off to coarser modes when support is low.

| Selector | Total hits | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---:|---|
| Best full-fit backoff `start_active_to_combo` support `1` | `229/234` | `5/10` | `0` | weak full-fit clue only |

- Families tested: `4`.
- Support thresholds tested: `5`.
- Prequential zero-clean-false-change cells: `1/5`.
- Prequential cover-all-test-residual cells: `1/5`.
- Prequential selected matches oracle cells: `2/5`.

Backoff does not rescue the contextual mode family. It keeps
the same full-fit ceiling but its held-out residual gains come
with false clean-control changes, so it is not a generative
parser rule.

## Observable Decision Tree Policy Control

Gate 27 tests whether the same residual branch choices need a
flat context table, or whether a small observable decision tree
over branch/position predicates can select a non-oracle continuation
objective.

| Parser | Total hits | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---:|---|
| Active branch baseline | `224/234` | `0/10` | `0` | retained control |
| Best observable tree | `228/234` | `4/10` | `0` | rejected |

- Observable predicates tested: `45`.
- Best tree depth/nodes: `3` / `9`.
- Prequential zero-clean-false-change cells: `5/5`.
- Prequential cover-all-test-residual cells: `1/5`.

The tree gives a stronger full-fit separator than the active baseline
without changing clean controls, but it recovers only `4/10`
residuals and recovers `0` held-out residuals in every split that
contains residuals. This rejects a small observable finite-state
decision tree as the missing parser.

## Next Blocker

The next real blocker is not another local length policy or
a single residual feature flag, and not a simple first-branch
continuation objective or small prefix-trained branch ranker.
A finite context table has weak full-fit signal, but stability
tests collapse it under leave-one-book/context controls. The
hierarchical backoff variant still fails clean holdout, and a
small observable decision tree still misses held-out residuals. The
remaining blocker is a richer path/state
segmentation account for why the parser waits, copies, or
understops at the remaining mixed residual sites, or a source-free
account of why the target digit stream exists.
Any promoted parser must close the residual drift without
smuggling in declared literal windows, target text generation,
or the stable projection as an oracle.

## Sources

- [Segmentation decision trace](test_results/01_segmentation_decision_trace.md)
- [Structural segmentation hypothesis audit](test_results/02_structural_segmentation_hypothesis_audit.md)
- [Parser dependency reduction ledger](test_results/04_parser_dependency_reduction_ledger.md)
- [Literal gap boundary audit](test_results/05_literal_gap_boundary_audit.md)
- [Online literal stop rule audit](test_results/06_online_literal_stop_rule_audit.md)
- [Literal stop exception topology audit](test_results/07_literal_stop_exception_topology_audit.md)
- [Integrated online literal parser audit](test_results/08_integrated_online_literal_parser_audit.md)
- [Integrated parser policy and drift audit](test_results/09_integrated_parser_policy_and_drift_audit.md)
- [Integrated parser override audit](test_results/10_integrated_parser_override_audit.md)
- [Integrated parser peak strength audit](test_results/11_integrated_parser_peak_strength_audit.md)
- [Integrated parser residual context audit](test_results/12_integrated_parser_residual_context_audit.md)
- [Global objective parser audit](test_results/13_global_objective_parser_audit.md)
- [Feature weighted global parser audit](test_results/14_feature_weighted_global_parser_audit.md)
- [Source boundary alignment audit](test_results/15_source_boundary_alignment_audit.md)
- [Single drift repair oracle audit](test_results/16_single_drift_repair_oracle_audit.md)
- [Observable repair policy audit](test_results/17_observable_repair_policy_audit.md)
- [Conditional repair classifier audit](test_results/18_conditional_repair_classifier_audit.md)
- [Two-stage conditional repair audit](test_results/19_two_stage_conditional_repair_audit.md)
- [Post-repair residual oracle audit](test_results/20_post_repair_residual_oracle_audit.md)
- [Post-repair residual feature audit](test_results/21_post_repair_residual_feature_audit.md)
- [Residual branch continuation audit](test_results/22_residual_branch_continuation_audit.md)
- [Branch ranker prequential audit](test_results/23_branch_ranker_prequential_audit.md)
- [Contextual mode selector audit](test_results/24_contextual_mode_selector_audit.md)
- [Contextual mode stability audit](test_results/25_contextual_mode_stability_audit.md)
- [Hierarchical context backoff audit](test_results/26_hierarchical_context_backoff_audit.md)
- [Observable decision tree policy audit](test_results/27_observable_decision_tree_policy_audit.md)
