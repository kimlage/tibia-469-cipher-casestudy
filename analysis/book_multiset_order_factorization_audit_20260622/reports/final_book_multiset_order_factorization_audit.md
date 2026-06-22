# Final Book Multiset/Order Factorization Audit

Status: `analysis_only`
Classification: `BOOK_MULTISET_ORDER_FACTORIZATION_AUDIT_ONLY`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Does the recent multistream signal primarily live in book-level token composition rather than within-book order, and can that composition be predicted by prefix-trained metadata above controls?

## Result

The train-selected book-level factorization costs `2972.334` bag bits plus `587.378` exact order-index bits. Bag saving versus the global bag model is `57.222` bits, with `0/5` cells beating permuted-feature p95. The exact order index is `0.165` of the selected representation.

## Decision

The result is a generator only if the multiset can be predicted above controls and the order field is no longer a large external tape. Row0, plaintext, translation, and compression_bound remain unchanged.

## Reproducible Artifacts

- [01_book_multiset_order_factorization_gate.py](../scripts/01_book_multiset_order_factorization_gate.py)
- [01_book_multiset_order_factorization_gate.json](test_results/01_book_multiset_order_factorization_gate.json)
- [01_book_multiset_order_factorization_gate.md](test_results/01_book_multiset_order_factorization_gate.md)
