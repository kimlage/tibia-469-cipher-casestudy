# Final Target Digit Boundary Audit

Status: `analysis_only`
Classification: `TARGET_DIGIT_BOUNDARY_MARKOV_CLUE_PROMOTED_NOT_GENERATOR`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Does the promoted `prev2_digits` clue help explain operation endpoints,
or does it only compress target payload after endpoints are declared?

## Result

- Books tested: `60`.
- Internal operation cutpoints: `201`.
- Candidate boundary positions: `9507`.
- Mean right-surprisal at real cutpoints: `3.808645`.
- Random right-surprisal mean/p95: `2.128341` / `2.293949`.
- Right-surprisal top10 hits: `88/201` (`0.437811`), above random p95 `0.139303`.
- Right-surprisal top-k selector hits: `57/201` (`0.283582`), exact nontrivial books `0/48`.
- Zero-cutpoint books: `12`.
- Delta right-left mean vs p95 control: `1.584790` / `0.207621`.

The result links the digit-process clue to segmentation: internal
operation cutpoints are strongly enriched immediately before high
surprisal digits under a prequential second-order digit model. This
is a real mechanical clue, not a compression micro-sweep. It is not a
generator: selecting the top-k surprisal positions recovers only a
minority of cutpoints and does not reconstruct full book skeletons.

## Decision

- A target-digit boundary Markov clue is promoted.
- No endpoint generator is promoted.
- The skeleton remains an atlas/dependency, but now with a stronger structural diagnostic.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Target digit boundary gate](test_results/01_target_digit_boundary_gate.md)
