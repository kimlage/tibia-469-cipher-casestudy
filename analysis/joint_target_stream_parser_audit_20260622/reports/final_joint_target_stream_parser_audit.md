# Final Joint Target Stream Parser Audit

Status: `analysis_only`
Classification: `JOINT_TARGET_STREAM_PARSER_FIRST_GATES_MIXED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Do first-pass joint target-stream/parser models reduce dependency by
emitting boundary state along with the digit stream under prefix holdout?

## Result

- Pair-token best model: `joint_pair_context_order0`.
- Pair-token aggregate gain vs baseline: `-29.950` bits.
- Pair-token positive cells: `2/5`.
- Hazard-state best feature: `age_bucket`.
- Hazard-state gain after feature charge: `170.175` bits.
- Hazard-state positive cells: `5/5`.
- Hazard-state random p95 before feature charge: `167.705` bits.
- Hazard endpoint decoder hits: `9/343`.
- Hazard endpoint cells beating random p95: `0/5`.

The pair-token model is rejected: pairing the boundary flag with the
current digit is not enough. A simple sequential hazard state is promoted
as a boundary dependency reducer: age since the last emitted boundary
beats same-count random boundary controls under prefix holdout. It is not
an exact parser: when decoded into exact endpoints with true op-count
granted, it does not beat same-count random endpoint controls.

## Decision

- Simple joint boundary+digit pair emission is rejected.
- Sequential boundary hazard state is promoted as a dependency reducer.
- Hazard endpoint decoding is rejected.
- No exact parser/generator is promoted.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Joint boundary digit gate](test_results/01_joint_boundary_digit_gate.md)
- [Boundary hazard state gate](test_results/02_boundary_hazard_state_gate.md)
- [Boundary hazard endpoint decoder gate](test_results/03_boundary_hazard_endpoint_decoder_gate.md)
