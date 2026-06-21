# Final Operation Length Markov Audit

Status: `analysis_only`
Classification: `OPERATION_LENGTH_MARKOV_GENERATOR_REJECTED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

If book lengths and operation types are granted, can simple Markov or
context grammars generate the `261` operation lengths?

## Result

- Books/operations: `60` / `261`.
- Context families tested: `11`.
- Best context: `op_index_x_type`.
- Best full-fit exact books: `9/60`.
- Best full-fit generated row hits: `43/261`.
- Best rowwise exact lengths: `52/261`.
- Best mean exact prefix ops: `0.217`.
- Prefix/holdout cover-all cells: `0/5`.
- Prefix/holdout any-exact-book cells: `1/5`.

## Decision

- No operation-length Markov/context generator is promoted.
- The operation-length atlas remains the operation-skeleton blocker.
- The negative result is generous: book lengths and operation types are granted.
- This does not change the compression bound.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Operation length Markov gate](test_results/01_operation_length_markov_gate.md)
