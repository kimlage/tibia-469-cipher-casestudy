# Final Operation Count Generation Audit

Status: `analysis_only`
Classification: `OPERATION_COUNT_GENERATOR_REJECTED_WITH_AUDIT_ONLY_CONTEXT_CLUE`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Can the source-free skeleton's per-book operation count be generated
from book id and book length before choosing cutpoints, operation
types, or sources?

## Result

- Books tested: `60`.
- Operation total: `261`.
- Model candidates: `229`.
- Best model: `context_book_mod10_x_length_bucket`.
- Best exact books: `40/60`.
- Best absolute error: `98`.
- Best paid records: `55` vs exact atlas `60`.
- Paid-record delta vs exact atlas: `-5`.
- Random mean/p95/max exact books: `8.143` / `13` / `18`.
- Prefix/holdout cover-all cells: `0/5`.
- Prefix/holdout beats-random-p95 exact cells: `0/5`.

The best full-fit context is a small audit-only dependency-compression
clue: `book_mod10_x_length_bucket` plus corrections costs fewer records
than declaring one operation count per book. It is not a generator:
it misses `20` books full-fit and fails every prefix/holdout promotion
gate.

## Decision

- No operation-count generator is promoted.
- The operation-count field remains a retained skeleton dependency.
- The `-5` paid-record full-fit reduction is audit-only and does not change the compression bound.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Operation count generation gate](test_results/01_operation_count_generation_gate.md)
