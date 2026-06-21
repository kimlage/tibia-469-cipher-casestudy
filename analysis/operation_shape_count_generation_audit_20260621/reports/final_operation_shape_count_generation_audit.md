# Final Operation Shape Count Generation Audit

Status: `analysis_only`
Classification: `OPERATION_SHAPE_COUNT_GENERATOR_REJECTED_WITH_AUDIT_ONLY_CONTEXT_CLUE`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Can each book's coarse operation shape `(op_count, literal_count)`
be generated from book id and book length before exact type sequence,
cutpoints, or sources?

## Result

- Books tested: `60`.
- Operation total: `261`.
- Literal/copy operation totals: `53` / `208`.
- Model candidates: `2416`.
- Best model: `context_book_mod10_x_length_bucket`.
- Best exact shape books: `37/60`.
- Best op-count exact books: `38/60`.
- Best literal-count exact books: `45/60`.
- Best total shape error: `140`.
- Best paid records: `58` vs exact shape atlas `60`.
- Paid-record delta vs exact atlas: `-2`.
- Random mean/p95/max exact books: `5.580` / `9` / `12`.
- Prefix/holdout cover-all cells: `0/5`.
- Prefix/holdout beats-random-p95 exact cells: `0/5`.

The same context that helped `op_count` also gives a small full-fit
shape-count reduction, but it is weaker: only `-2` paid records
versus exact shape lookup, with `23` missed books and no promoting
holdout cells.

## Decision

- No operation-shape-count generator is promoted.
- Coarse `(op_count, literal_count)` shape remains a retained skeleton dependency.
- The `-2` paid-record full-fit reduction is audit-only and does not change the compression bound.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Operation shape count generation gate](test_results/01_operation_shape_count_generation_gate.md)
