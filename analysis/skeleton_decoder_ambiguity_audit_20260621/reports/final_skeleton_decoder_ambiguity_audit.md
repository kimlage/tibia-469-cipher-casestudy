# Final Skeleton Decoder Ambiguity Audit

Status: `analysis_only`
Classification: `SKELETON_DECODER_AMBIGUITY_BLOCKS_GENERATOR`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

If the exact source-free operation skeleton is granted, can a decoder
emit the books without declared copy-source choices and literal payload?

## Result

- Books tested: `60`.
- Skeleton operations/copies/literals: `261` / `208` / `53`.
- Copied/literal digits: `9301` / `266`.
- Seed payload digits granted operationally: `1696`.
- Legal source branching lower bound: `2550.594` bits.
- Literal payload branching: `883.633` bits.
- Combined decoder ambiguity lower bound after skeleton: `3434.227` bits.
- Equivalent lower-bound decimal choices: `10^1033.805`.
- Copy events with unique target-oracle source: `78/208`.
- Target-oracle source-choice residual: `232.902` bits.

The exact skeleton is therefore a stable atlas, not a decoder-side
generator. The target-oracle matching-source count is diagnostic only:
it grants the future copied chunk and cannot be used as a generation
rule without reintroducing target-text oracle access.

## Decision

- No skeleton decoder generator is promoted.
- Copy-source choices remain a declared dependency.
- Literal payload remains a declared dependency.
- This does not change the compression bound.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Skeleton decoder ambiguity gate](test_results/01_skeleton_decoder_ambiguity_gate.md)
