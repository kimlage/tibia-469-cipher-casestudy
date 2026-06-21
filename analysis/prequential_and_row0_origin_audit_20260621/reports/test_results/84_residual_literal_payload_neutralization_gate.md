# Residual Literal-Payload Neutralization Gate

Classification: `literal_payload_neutralization_improves_residual_stability`
Translation delta: `NONE`

## Purpose

Gate 83 localized the best neutralized parser residuals to books `26`
and `34`. This gate adds uniform literal-payload cost on top of the
uniform copy-length/source-exception mode to test whether learned
payload pressure is the remaining instability driver.

## Summary

- Base stable exact-path books: `48`.
- Payload-neutralized stable exact-path books: `49`.
- Stable delta vs base: `1`.
- Payload-mode unstable books: `[49]`.
- Resolved vs base: `[26, 34]`.
- Persistent vs base: `[]`.
- Introduced vs base: `[49]`.
- Parser-bit delta vs base: `170.606311`.
- Raw-positive evaluations: `175/175`.

## Decision

- Uniform literal-payload cost tests whether the remaining neutralized-parser residuals are caused by learned payload pressure. Promotion would require improved global path stability without introducing a worse residual frontier.
- No compression-bound change is introduced.
- No corpus-wide formula promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
