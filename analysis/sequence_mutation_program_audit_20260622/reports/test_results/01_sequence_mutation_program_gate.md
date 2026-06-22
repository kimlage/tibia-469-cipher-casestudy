# Sequence Mutation Program Gate

Classification: `SEQUENCE_MUTATION_PROGRAM_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether a future book's joint operation-token sequence can be encoded as an optimistic edit script from a previous training-book sequence.

## Summary

- Selected edit lower-bound bits: `4742.368`.
- Sequence unigram baseline bits: `3525.674`.
- Saving vs sequence unigram: `-1216.694` bits.
- Cells beating shuffled-train p95: `0/5`.
- Cells beating random-source p95: `2/5`.
- Selected cells using skeleton-count policies: `0/5`.
- Oracle lower-bound saving with paid source index: `-832.040` bits.

## Prefix Holdouts

| Cutoff | Policy | Test ops | Edit lb bits | Baseline bits | Saving | Shuffle p95 | Random p95 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `20` | `previous_book` | `182` | `1575.409` | `1257.712` | `-317.697` | `False` | `True` |
| `30` | `previous_book` | `140` | `1284.978` | `1022.013` | `-262.965` | `False` | `True` |
| `40` | `phase_then_length` | `95` | `940.218` | `690.350` | `-249.868` | `False` | `False` |
| `50` | `previous_book` | `56` | `741.943` | `408.084` | `-333.859` | `False` | `False` |
| `60` | `previous_book` | `20` | `199.819` | `147.516` | `-52.304` | `False` | `False` |

## Decision

This is a lower-bound test. It can reject sequence mutation if weak, but it cannot by itself promote a generator because matched positions and full edit syntax are not completely charged.
