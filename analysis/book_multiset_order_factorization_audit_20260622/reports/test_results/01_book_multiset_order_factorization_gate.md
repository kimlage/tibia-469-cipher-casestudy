# Book Multiset/Order Factorization Gate

Classification: `BOOK_MULTISET_ORDER_FACTORIZATION_AUDIT_ONLY`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Decompose the current joint operation-token stream into a per-book multiset and an exact within-book order index. This directly tests the clue left by HMM/schedule gates that failed same-book shuffle controls.

## Summary

- Selected bag bits: `2972.334`.
- Selected order-index bits: `587.378`.
- Selected total sequence bits: `3559.712`.
- Order share of selected representation: `0.165`.
- Global bag bits: `3029.556`.
- Bag saving vs global: `57.222` bits.
- Cells beating permuted-feature p95: `0/5`.
- Selected models using granted count features: `0/5`.

## Prefix Holdouts

| Cutoff | Selected family | Test ops | Bag bits | Order bits | Bag saving | Beats permuted p95 | Grants count feature |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `20` | `book_phase` | `182` | `1087.611` | `228.267` | `0.000` | `False` | `False` |
| `30` | `book_phase` | `140` | `861.664` | `170.470` | `12.679` | `False` | `False` |
| `40` | `book_phase` | `95` | `541.301` | `112.227` | `44.543` | `False` | `False` |
| `50` | `book_phase` | `56` | `349.026` | `61.337` | `0.000` | `False` | `False` |
| `60` | `book_phase` | `20` | `132.733` | `15.077` | `0.000` | `False` | `False` |

## Decision

This gate can promote only if book-level composition is predicted above permuted-feature controls and the remaining exact order index is small or handled by a separate generator. Otherwise the result is a useful ledger factorization, not a mechanical generation program.
