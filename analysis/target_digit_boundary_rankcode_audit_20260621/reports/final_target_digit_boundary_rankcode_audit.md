# Final Target Digit Boundary Rank-Code Audit

Status: `analysis_only`
Classification: `TARGET_DIGIT_BOUNDARY_RANKCODE_WEAK_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Does the whole `prev2_digits` boundary rank distribution reduce the
declared cutpoint atlas beyond a single high-surprisal band?

## Result

- Books/cutpoints/candidate positions: `60` / `201` / `9507`.
- Best scheme: `top5_10_20_50`.
- Best bin totals: `[63, 23, 27, 43, 45]`.
- Baseline cutpoint bits: `1137.308`.
- Model bits after scheme charge: `1018.908`.
- Saving after scheme charge: `118.400` bits.
- Random saving p95 for best scheme: `-57.822` bits.
- Prefix-selected positive test-saving cells after scheme charge: `4/5`.

The rank-code view is useful but does not pass the stricter promotion
gate. It improves the full-fit paid atlas relative to the one-band
pruning code, but prefix-selected suffix validation fails in the last
cell. The prior boundary-pruning clue remains the promoted result.

## Decision

- No boundary rank-code clue is promoted.
- No endpoint generator is promoted.
- This records a weak diagnostic and a promotion boundary.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Target digit boundary rank-code gate](test_results/01_target_digit_boundary_rankcode_gate.md)
