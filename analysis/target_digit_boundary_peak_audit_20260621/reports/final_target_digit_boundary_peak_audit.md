# Final Target Digit Boundary Peak Audit

Status: `analysis_only`
Classification: `TARGET_DIGIT_BOUNDARY_PEAK_SUPPRESSION_WEAK_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Can the `prev2` boundary signal be sharpened into local peaks or
non-maximum-suppressed rank peaks, without granting op-count?

## Result

- Books/candidates/actual cutpoints: `60` / `9507` / `201`.
- Policies tested: `360`.
- Best peak policy: `nms_rank:top=0.05:gap=3`.
- Baseline full cutpoint atlas bits: `1570.073`.
- Correction bits after policy charge: `954.126`.
- Saving after policy charge: `615.947` bits.
- TP/FP/FN: `57` / `360` / `144`.
- Predicted boundaries/correction events: `417` / `504`.
- Precision/recall: `0.136691` / `0.283582`.
- Exact books: `0/60`.
- Prefix-selected positive test-saving cells: `5/5`.

## Comparison To Threshold Gate

- Prior threshold policy: `right_ge:4`.
- Saving delta vs threshold: `-29.746` bits.
- Correction-event delta vs threshold: `-444`.
- False-positive delta vs threshold: `-481`.
- False-negative delta vs threshold: `37`.

Peak suppression is a meaningful diagnostic because it cuts the correction
event count almost in half, but it is worse as a paid code: it discards too
many true cutpoints and still generates no exact book skeletons.

## Decision

- Local peak / non-maximum suppression replacement is not promoted.
- Endpoint generator is not promoted.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Target digit boundary peak gate](test_results/01_target_digit_boundary_peak_gate.md)
