# Compact Latent Rule Frontier

Classification: `compact_latent_rule_rejected_cost_or_holdout`
Translation delta: `NONE`

## Purpose

Gate 42 tests whether a small observable latent rule can beat the explicit
residual lookup priced by gate 41. Candidate rules use residual-visible book,
operation, and active-operation features; each rule pays predicate and label
IDs before any remaining residual lookup is charged.

This is not a compression-bound update and not a row0/semantic claim.

## Summary

- Residual count: `10`.
- Predicate count: `49`.
- Label count: `9`.
- Candidate rule sets: `6276`.
- Baseline lookup bits: `79.361`.
- Best total bits: `74.117`.
- Best net bits vs lookup:
  `-5.243`.
- Best rule count: `1`.
- Best hits: `2`.
- Best false positives: `1`.
- Best zero-false-positive net bits vs lookup:
  `1.773`.
- Best zero-false-positive hits:
  `1`.
- Prequential cells with held-out hit:
  `0/4`.
- Promotes compact latent rule: `False`.

## Top Rule Sets

| rules | hits | false positives | unresolved | total bits | net bits | rule spec |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 1 | 8 | 74.117 | -5.243 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}] |
| 1 | 2 | 5 | 8 | 74.117 | -5.243 | [{'predicate': 'book_lt_40', 'label': ('copy', 5)}] |
| 1 | 2 | 6 | 8 | 74.117 | -5.243 | [{'predicate': 'active_type_literal', 'label': ('copy', 5)}] |
| 1 | 2 | 8 | 8 | 74.117 | -5.243 | [{'predicate': 'all', 'label': ('copy', 5)}] |
| 2 | 3 | 1 | 7 | 75.880 | -3.481 | [{'predicate': 'book_mod5_2', 'label': ('literal', 28)}, {'predicate': 'book_mod5_4', 'label': ('copy', 5)}] |
| 2 | 3 | 1 | 7 | 75.880 | -3.481 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_eq_14', 'label': ('literal', 39)}] |
| 2 | 3 | 1 | 7 | 75.880 | -3.481 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_eq_16', 'label': ('literal', 1)}] |
| 2 | 3 | 1 | 7 | 75.880 | -3.481 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_eq_20', 'label': ('copy', 10)}] |
| 2 | 3 | 1 | 7 | 75.880 | -3.481 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_eq_21', 'label': ('copy', 9)}] |
| 2 | 3 | 1 | 7 | 75.880 | -3.481 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}, {'predicate': 'book_eq_26', 'label': ('copy', 11)}] |

## Prequential Rows

| cutoff | train | test | test hits | test false positives | train net bits | selected rules |
| --- | --- | --- | --- | --- | --- | --- |
| 20 | 2 | 8 | 0 | 6 | 1.729 | [{'predicate': 'op_even', 'label': ('literal', 39)}] |
| 30 | 5 | 5 | 0 | 4 | 1.746 | [{'predicate': 'book_parity_1', 'label': ('copy', 9)}] |
| 40 | 7 | 3 | 0 | 0 | -5.277 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}] |
| 50 | 8 | 2 | 0 | 0 | -5.266 | [{'predicate': 'book_mod5_4', 'label': ('copy', 5)}] |
| 60 | 10 | 0 | 0 | 0 | 0.000 | [] |

## Decision

No compact latent rule is promoted. The best apparent MDL gain has false
positives, and the best zero-false-positive rule does not provide stable
held-out coverage. Under current evidence, the latent state still needs a real
mechanism, not a small residual-visible rule patch.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
