# Source-Free Residual Rule Gate

Classification: `source_free_residual_rule_rejected`
Translation delta: `NONE`

## Purpose

Gate 43 tests the strict source-free residual-rule path. Unlike gate 42, it
removes active parser/copy-availability features and uses only book/op ordinal
features. It also reports lookup-like `book_eq` predicates separately.

## Summary

- Residual count: `10`.
- Predicate count: `45`.
- Structural candidate rule sets:
  `4495`.
- Lookup-like candidate rule sets:
  `5510`.
- Structural best net bits vs lookup:
  `-5.366`.
- Structural best false positives:
  `1`.
- Structural best zero-false-positive net bits:
  `1.651`.
- Structural best zero-false-positive hits:
  `1`.
- Lookup-like best zero-false-positive net bits:
  `1.651`.
- Prequential structural cells with hit:
  `0/4`.
- Promotes source-free residual rule:
  `False`.

## Structural Frontier

| rules | hits | false positives | unresolved | uses book_eq | net bits | rule spec |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 1 | 8 | False | -5.366 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}] |
| 1 | 2 | 5 | 8 | False | -5.366 | [{'predicate': 'book_lt_40', 'label': ('copy', 5)}] |
| 1 | 2 | 8 | 8 | False | -5.366 | [{'predicate': 'all', 'label': ('copy', 5)}] |
| 2 | 3 | 1 | 7 | False | -3.727 | [{'predicate': 'book_mod5_2', 'label': ('literal', 28)}, {'predicate': 'book_mod5_4', 'label': ('copy', 5)}] |
| 2 | 3 | 1 | 7 | False | -3.727 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_mod10_0', 'label': ('copy', 10)}] |
| 2 | 3 | 1 | 7 | False | -3.727 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_mod10_1', 'label': ('copy', 9)}] |
| 2 | 3 | 1 | 7 | False | -3.727 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_mod10_4', 'label': ('literal', 39)}] |
| 2 | 3 | 1 | 7 | False | -3.727 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_mod10_7', 'label': ('literal', 28)}] |

## Lookup-Like Frontier

| rules | hits | false positives | unresolved | uses book_eq | net bits | rule spec |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 1 | 8 | False | -5.366 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}] |
| 1 | 2 | 5 | 8 | False | -5.366 | [{'predicate': 'book_lt_40', 'label': ('copy', 5)}] |
| 1 | 2 | 8 | 8 | False | -5.366 | [{'predicate': 'all', 'label': ('copy', 5)}] |
| 2 | 3 | 1 | 7 | False | -3.727 | [{'predicate': 'book_mod5_2', 'label': ('literal', 28)}, {'predicate': 'book_mod5_4', 'label': ('copy', 5)}] |
| 2 | 3 | 1 | 7 | False | -3.727 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_mod10_0', 'label': ('copy', 10)}] |
| 2 | 3 | 1 | 7 | False | -3.727 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_mod10_1', 'label': ('copy', 9)}] |
| 2 | 3 | 1 | 7 | False | -3.727 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_mod10_4', 'label': ('literal', 39)}] |
| 2 | 3 | 1 | 7 | False | -3.727 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_mod10_7', 'label': ('literal', 28)}] |

## Structural Prequential Rows

| cutoff | train | test | test hits | test false positives | train net bits | selected rules |
| --- | --- | --- | --- | --- | --- | --- |
| 20 | 2 | 8 | 0 | 8 | -1.132 | [{'predicate': 'op_even', 'label': ('literal', 39)}, {'predicate': 'op_odd', 'label': ('literal', 1)}] |
| 30 | 5 | 5 | 0 | 4 | 0.775 | [{'predicate': 'book_parity_1', 'label': ('copy', 9)}] |
| 40 | 7 | 3 | 0 | 2 | 1.049 | [{'predicate': 'book_mod5_0', 'label': ('copy', 10)}] |
| 50 | 8 | 2 | 0 | 2 | 1.277 | [{'predicate': 'book_ge_40', 'label': ('copy', 8)}] |
| 60 | 10 | 0 | 0 | 0 | 0.000 | [] |

## Decision

No source-free residual rule is promoted. Structural book/op ordinal rules do
not beat the lookup with clean held-out coverage; allowing `book_eq` only turns
the rule into a lookup-like patch. The source-free path therefore still needs a
real digit-stream mechanism, not a residual selector.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
