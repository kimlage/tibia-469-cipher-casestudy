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

## Next Blocker

The next real blocker is not another local length policy. It is a
source-free account of why the target digit stream exists, or a
parser integration that closes the remaining `12/60` drift cases
without smuggling in declared literal windows, target text generation,
or changed skeleton/literal accounting.

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
