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

## Target Boundary Recurrence Control

Gate 28 tests whether branch choices preserve more recurrent
target-side chunk boundaries. Each branch defines a next boundary
at `target_start + length`; recurrence policies score raw digit
context around that boundary.

| Policy | Total hits | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---:|---|
| Active branch baseline | `224/234` | `0/10` | `0` | retained control |
| Best recurrence policy `max_left_right_r8` | `31/234` | `1/10` | `194` | rejected |

- Recurrence policies tested: `11`.
- Radii tested: `[2, 3, 4, 6, 8]`.
- Prequential zero-clean-false-change cells: `0/5`.
- Prequential cover-all-test-residual cells: `1/5`.

Target-side boundary recurrence is not the missing segmentation
rule. The best recurrence policy gets only `1/10` residuals,
changes `194` clean controls, and is worse than random-boundary
controls on total hits.

## Future Copy Opportunity Control

Gate 29 tests whether branch choices preserve or create
near-future copy opportunities. Each branch is scored by copy
availability at its boundary and within a short lookahead window.

| Policy | Total hits | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---:|---|
| Active branch baseline | `224/234` | `0/10` | `0` | retained control |
| Best opportunity policy `max_copy_positions` | `96/234` | `2/10` | `130` | rejected |

- Lookahead positions: `12`.
- Opportunity policies tested: `5`.
- Prequential zero-clean-false-change cells: `0/5`.
- Prequential cover-all-test-residual cells: `1/5`.

Near-future copy opportunity does not explain the residual branch
choices. The best policy catches only `2/10` residuals and changes
`130` clean controls, while randomized feature controls do better
on total hits.

## Source State Continuity Control

Gate 30 tests whether branch choices preserve continuity with
the previous copy in the accepted book-local prefix path: same
source, source at previous source end, same source end, or
minimum source/length deltas.

| Policy | Total hits | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---:|---|
| Active branch baseline | `224/234` | `0/10` | `0` | retained control |
| Best source-state policy `min_source_delta` | `217/234` | `6/10` | `13` | rejected |

- Decisions with previous-copy state: `162`.
- Residual decisions with previous-copy state: `6/10`.
- Best eligible residual hits: `3/6`.
- Prequential zero-clean-false-change cells: `0/5`.
- Prequential cover-all-test-residual cells: `1/5`.

Book-local source-state continuity is not the missing parser
rule. It is stronger than shuffled source-state controls and
does catch some residuals, but the gain is bought by changing
clean decisions and it fails the clean holdout gate.

## Global Source State Continuity Upper Bound

Gate 31 grants a stronger version of the source-state hypothesis:
the previous-copy state is carried across books and is built from
the full stable-projection history before each decision. Candidate
branches are still scored only by source/source-end/length
continuity.

| Policy | Total hits | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---:|---|
| Active branch baseline | `224/234` | `0/10` | `0` | retained control |
| Best global source-state policy `min_source_delta` | `217/234` | `6/10` | `13` | rejected upper bound |

- Residual decisions with previous-copy state: `10/10`.
- Best eligible residual hits: `6/10`.
- Prequential zero-clean-false-change cells: `0/5`.
- Prequential cover-all-test-residual cells: `1/5`.

Even with stable-projection history granted, source-state continuity
does not become a parser rule: it catches some residuals but still
changes clean decisions and fails the clean holdout gate.

## Phase/Grid Segmentation Control

Gate 32 tests whether branch choices preserve a simple cycle
or grid phase over target boundary, operation length, source,
source end, or source-target alignment. Cycles tested are
`2/3/4/5/8/10/16/20`.

| Policy | Total hits | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---:|---|
| Active branch baseline | `224/234` | `0/10` | `0` | retained control |
| Best phase/grid policy `source_mod0_10` | `225/234` | `1/10` | `0` | weak full-fit clue, rejected rule |

- Phase/grid policies tested: `64`.
- Prequential zero-clean-false-change cells: `1/5`.
- Prequential cover-all-test-residual cells: `1/5`.
- Prequential selected matches oracle cells: `1/5`.

The `source_mod0_10/20` family gives a one-residual full-fit
clue without false clean-control changes, but it does not
generalize under prefix/holdout and leaves `9/10` residuals
unexplained. Phase/grid alignment is therefore not the missing
segmentation parser.

## Context Nearest-Branch Control

Gate 33 tests whether stable branch actions recur with raw
digit context. Each policy finds the nearest prior or other-book
decision by target-context Hamming distance and applies that
training row's stable branch action class to the current branch
set.

| Policy | Total hits | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---:|---|
| Active branch baseline | `224/234` | `0/10` | `0` | retained control |
| Best leave-one-book nearest policy `nearest_context_l8_r8_action_class` | `216/234` | `0/10` | `8` | rejected |

- Nearest-context policies tested: `15`.
- Prequential zero-clean-false-change cells: `0/5`.
- Prequential cover-all-test-residual cells: `1/5`.
- Prequential selected matches oracle cells: `0/5`.

Raw digit context nearest-neighbor recurrence does not explain
the branch decisions. It is worse than the active baseline,
recovers `0/10` residuals, and shuffled training labels match
or exceed it.

## Structural Signal Consensus Control

Gate 34 tests whether weak structural signals become usable only
when independent families agree. Four families vote on each branch:
source-state continuity, phase/grid, near-future copy opportunity,
and recurrent target boundary. The parser switches away from the
active branch only if enough families choose the same non-active
branch.

| Policy | Total hits | Residual hits | Clean false changes | Boundary |
|---|---:|---:|---:|---|
| Active branch baseline | `224/234` | `0/10` | `0` | retained control |
| Best consensus `k3:source=global_min_source_delta:phase=source_mod0_10:future=max_copy_positions:boundary=max_left_right_r8` | `224/234` | `0/10` | `0` | rejected |

- Consensus configs tested: `48`.
- Prequential zero-clean-false-change cells: `4/5`.
- Prequential cover-all-test-residual cells: `1/5`.
- Prequential selected matches oracle cells: `4/5`.

Consensus improves precision by refusing to move, but then it
recovers `0/10` residuals. The lower-threshold train choice can
catch one residual only by introducing false clean-control
changes. Combining weak signals therefore does not solve the
branch-choice problem.

## Structural Vote Residual Decomposition

Gate 35 decomposes the rejected weak-signal frontier decision by
decision. It counts how many structural votes support the stable
branch in each residual and how often the same non-active support
appears in clean controls.

| Diagnostic | Value |
|---|---:|
| Residual stable-support histogram | `{'0': 2, '2': 6, '3': 1, '4': 1}` |
| Clean top-nonactive-support histogram | `{'0': 3, '1': 82, '2': 121, '3': 17, '4': 1}` |
| Residuals with stable support >=3 | `2/10` |
| Clean rows with nonactive support >=3 | `18` |

There is no hidden clean threshold. At threshold `3`, only books
`16` and `39` would be correctly flagged, while `18` clean controls
would also move. At threshold `4`, book `39` remains but one clean
control remains as well. The weak-signal front is therefore
diagnostically decomposed, not promoted.

## Branch Choice Frontier Closure

Gate 36 closes the current branch-choice weak-signal frontier as
audit-only. It compiles gates `16-35`, including oracle repairs,
observable repair policies, context tables, source-state rules,
phase/grid rules, nearest-context recurrence, consensus, and vote
decomposition.

| Diagnostic | Value |
|---|---:|
| Gates audited | `20` |
| Non-oracle gates audited | `18` |
| Complete promoted parser rules | `0` |
| Partial promoted rule clues | `0` |
| Clean-zero partial non-oracle rules | `4` |

The closure result is not a new parser. It says the stable residual
branch is oracle-repairable, but the tested non-oracle weak-signal
families do not justify another local branch-choice combination
under current evidence.

## Path Template Reuse Control

Gate 37 tests the next structural shortcut after weak signals:
whether the remaining first-drift corrections can be selected
by reusing exact source-free operation-length templates from
books that the active parser already parses exactly.

| Diagnostic | Value |
|---|---:|
| Exact parser books | `50` |
| Residual parser books | `10` |
| Best template width | `1` |
| Deterministic residual matches | `0/10` |
| Prequential residual cells with match | `0/4` |

No exact-length template width `1..3` explains any of the `10`
residual first-drift corrections. This rejects a simple
multi-op path-template reuse explanation and leaves the blocker
at a richer latent path/state mechanism or source-free target
digit account.

## Trajectory Neighbor Parser Control

Gate 38 tests a richer path/state shortcut: choose the residual
first-drift operation by nearest cumulative parser-state
trajectory from books already parsed exactly. It tests
trajectory-only, context-only, and combined vectors with
`k=1/3/5`.

| Diagnostic | Value |
|---|---:|
| Exact parser books | `50` |
| Residual parser books | `10` |
| Best policy | `trajectory`, k=`1` |
| Best residual hits | `0/10` |
| Prequential residual cells fully hit | `0/4` |
| Shuffle p_ge_observed | `1.0000` |

Every tested trajectory-neighbor policy scores `0/10` on the
residual first-drift choices. The nearest-neighbor shortcut is
therefore rejected as a replacement for the retained segmentation
decisions.

## Observable State Support Boundary

Gate 39 diagnoses whether the residual first-drift states are
outside the exact-book support, contradicted by exact examples,
or ambiguously supported under the currently exposed observable
state families.

| Diagnostic | Value |
|---|---:|
| Exact parser books | `50` |
| Residual parser books | `10` |
| Best exact-label family | `trajectory` |
| Deterministic exact-label matches | `0/10` |
| Supported residual states | `4/10` |
| Contradictory residual states | `2` |
| Prequential cells with deterministic match | `0/4` |

The best observable family gives `0/10` deterministic exact-label
matches. Six residuals are out of support and the supported
residuals are ambiguous or contradictory. The missing mechanism
therefore needs new latent state or a source-free target stream
account, not another reuse rule over the exposed state.

## Latent State Requirement Boundary

Gate 40 tests whether simple observable latent-state splits
repair the gate-39 support failure. It tries book parity,
book modulo/decade/half, operation index, target half, and
active-operation splits across the trajectory/context/combined
families.

| Diagnostic | Value |
|---|---:|
| Score count | `33` |
| Best split | `trajectory + target_half` |
| Deterministic matches | `0/10` |
| Supported residual states | `4/10` |
| Out-of-support residual states | `6/10` |
| Residuals needing latent resolution | `10` |
| Distinct stable labels needing resolution | `9` |
| Minimum oracle bits for distinct labels | `3.170` |

No simple split produces deterministic residual matches. A
candidate latent state would need to explain all `10` remaining
residual distinctions, with `9` distinct stable labels still
unaccounted for by the exposed state.

## Next Blocker

The next real blocker is not another local length policy or
a single residual feature flag, and not a simple first-branch
continuation objective or small prefix-trained branch ranker.
A finite context table has weak full-fit signal, but stability
tests collapse it under leave-one-book/context controls. The
hierarchical backoff variant still fails clean holdout, and a
small observable decision tree still misses held-out residuals.
Target-side boundary recurrence and near-future copy opportunity
are also rejected. Book-local source-state continuity is rejected
as well, and even the global carryover source-state upper bound
fails clean holdout. A simple phase/grid rule gives only a weak
one-residual full-fit clue. Raw context nearest-neighbor recurrence
is also rejected, and consensus over the weak structural signals
collapses back to the active baseline. Vote decomposition shows no
clean residual threshold hidden inside those signals. Gate 36 closes
that branch-choice weak-signal frontier as audit-only. Gate 37 then
rejects simple exact-length path-template reuse. Gate 38 rejects
nearest trajectory-state reuse. Gate 39 shows the exposed state
families have no deterministic residual support. Gate 40 shows
simple observable splits still leave `10` residual distinctions
needing latent resolution. The remaining blocker is a richer latent path/state
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
- [Target boundary recurrence audit](test_results/28_target_boundary_recurrence_audit.md)
- [Future copy opportunity audit](test_results/29_future_copy_opportunity_audit.md)
- [Source state continuity audit](test_results/30_source_state_continuity_audit.md)
- [Global source state continuity audit](test_results/31_global_source_state_continuity_audit.md)
- [Phase grid segmentation audit](test_results/32_phase_grid_segmentation_audit.md)
- [Context nearest branch audit](test_results/33_context_nearest_branch_audit.md)
- [Structural signal consensus audit](test_results/34_structural_signal_consensus_audit.md)
- [Structural vote residual decomposition](test_results/35_structural_vote_residual_decomposition.md)
- [Branch choice frontier closure audit](test_results/36_branch_choice_frontier_closure_audit.md)
- [Path template reuse audit](test_results/37_path_template_reuse_audit.md)
- [Trajectory neighbor parser audit](test_results/38_trajectory_neighbor_parser_audit.md)
- [Observable state support audit](test_results/39_observable_state_support_audit.md)
- [Latent state requirement audit](test_results/40_latent_state_requirement_audit.md)
