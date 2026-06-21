# Final Operation Type Sequence Generation Audit

Status: `analysis_only`
Classification: `OPERATION_TYPE_SEQUENCE_GENERATOR_REJECTED_AS_POSTHOC_TEMPLATE`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Can the literal/copy order inside each book be generated once
`(op_count, literal_count)` is granted?

## Result

- Books/operations: `60` / `261`.
- Literal/copy operation totals: `53` / `208`.
- Models tested: `10`.
- Best model: `template_book_mod5_x_shape`.
- Best model kind: `template`.
- Best exact books: `60/60`.
- Best type hits: `261/261`.
- Best paid records: `235` vs exact type fields `261`.
- Paid-record delta vs exact type fields: `-26`.
- Random mean/p95/max exact books: `39.449` / `42` / `44`.
- Random mean/p95/max type hits: `191.486` / `201` / `211`.
- Prefix/holdout cover-all cells: `0/5`.
- Prefix/holdout beats-random-p95 exact cells: `0/5`.
- Prefix/holdout beats-random-p95 type-hit cells: `0/5`.

The best full-fit model is an exact template map, not a generator:
it reproduces all books only by carrying `235` template records,
`-26` versus the exact type-field atlas, and it has no
promoting holdout cells.

## Decision

- No operation-type-sequence generator is promoted.
- Literal/copy order remains retained unless derived jointly with length and copy availability.
- Exact full-fit templates are rejected as posthoc materialization.
- This does not change the compression bound.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Operation type sequence generation gate](test_results/01_operation_type_sequence_generation_gate.md)
