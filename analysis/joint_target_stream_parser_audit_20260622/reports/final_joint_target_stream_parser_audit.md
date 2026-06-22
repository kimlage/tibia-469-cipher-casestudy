# Final Joint Target Stream Parser Audit

Status: `analysis_only`
Classification: `JOINT_BOUNDARY_DIGIT_PAIR_MODEL_REJECTED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Does the simplest joint target-stream/parser model improve generation by
emitting `(boundary flag, digit)` pairs under prefix-trained contexts?

## Result

- Prefix cutoffs tested: `5`.
- Context orders tested: `[0, 1, 2, 3]`.
- Best nontrivial model: `joint_pair_context_order0`.
- Best aggregate gain vs baseline: `-29.950` bits.
- Positive cells for best model: `2/5`.
- Promotes joint parser: `False`.

The simplest joint model is rejected. Pairing the boundary flag with the
current digit is not enough; context sparsity overwhelms any boundary
signal. A future parser needs explicit latent state or another joint
mechanism, not just `(boundary,digit)` tokens.

## Decision

- Simple joint boundary+digit pair emission is rejected.
- No parser/generator is promoted.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Joint boundary digit gate](test_results/01_joint_boundary_digit_gate.md)
