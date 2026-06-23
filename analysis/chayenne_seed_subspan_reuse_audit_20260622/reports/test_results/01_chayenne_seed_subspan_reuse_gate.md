# Chayenne Seed Subspan Reuse Gate

Classification: `chayenne_seed_subspan_external_cover_clue_not_reuse_program`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

| Metric | Observed | Control |
| --- | ---: | ---: |
| Chayenne cover digits | `49/49` | p95 `0`, max `36` |
| Derived occurrences | `15` | p95 `19`, p99 `22` |
| Distinct derived books | `15` | p95 `17` |
| Derived covered digits | `402` | p95 `431` |
| External cover clue | `True` | control max `36` |

## Span Rows

| Span | Seed Location | Length | Derived Occurrences | Derived Books |
| --- | --- | ---: | ---: | --- |
| `chayenne_span_0` | `book 1:16` | `36` | `9` | `[10, 19, 27, 31, 35, 37, 41, 63, 66]` |
| `chayenne_span_1` | `book 2:111` | `13` | `6` | `[22, 28, 46, 48, 51, 53]` |

## Decision

`Chayenne spans uniquely cover the external holdout, but corpus reuse does not beat same-length seed controls`

Next blocker: `subspan reuse does not derive module selection, replay events, or innovation origin`

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
