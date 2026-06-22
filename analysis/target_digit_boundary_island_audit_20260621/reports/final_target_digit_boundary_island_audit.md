# Final Target Digit Boundary Island Audit

Status: `analysis_only`
Classification: `TARGET_DIGIT_BOUNDARY_ISLAND_CODE_REJECTED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Can high-surprisal boundary candidates be described as contiguous islands
plus offsets, rather than a flat candidate set, without granting op-count?

## Result

- Books/candidates/actual cutpoints: `60` / `9507` / `201`.
- Policies tested: `23`.
- Best island policy: `right_ge:4`.
- Baseline full cutpoint atlas bits: `1570.073`.
- Island correction bits after policy charge: `941.005`.
- Island saving after policy charge: `629.068` bits.
- Same-policy threshold saving: `645.694` bits.
- Island delta vs same-policy threshold: `16.625` bits.
- TP/FP/FN: `94` / `841` / `107`.
- Islands/occupied/multi-hit: `782` / `94` / `0`.
- Exact books: `0/60`.
- Prefix-selected island-beats-threshold cells: `2/5`.

## Comparison To Threshold Gate

- Threshold gate best policy: `right_ge:4`.
- Threshold gate saving after policy charge: `645.694` bits.
- Best island saving delta vs threshold gate: `-16.625` bits.
- Best island correction delta vs threshold gate: `16.625` bits.

The island view is structurally informative: the best policy's occupied
islands are single-hit. But it does not improve the paid code, does not
win prequentially against same-policy threshold coding, and does not
generate any exact book skeletons.

## Decision

- Island code is rejected as a replacement for the threshold gate.
- Endpoint generator is not promoted.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Target digit boundary island gate](test_results/01_target_digit_boundary_island_gate.md)
