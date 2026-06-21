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

## Next Blocker

The next real blocker is not another local length policy. It is a
source-free account of why the target digit stream exists, or a
controlled parser integration that proves the stable projection can
replace the retained `(source,length)` ledger without smuggling in
target text or changing the skeleton/literal accounting.

## Sources

- [Segmentation decision trace](test_results/01_segmentation_decision_trace.md)
- [Structural segmentation hypothesis audit](test_results/02_structural_segmentation_hypothesis_audit.md)
