# Full Source Policy Invariance Boundary

Classification: `full_source_policy_stable_but_source_variant`
Translation delta: `NONE`

## Purpose

Gate 94 showed that all three source tie policies are stable across the
five prequential cutoffs when every same-length source candidate is
exposed. This audit tests the stronger dependency question: whether the
source-bearing exact signatures are invariant across policies.

## Result

- Cases compared: `175` `(cutoff, book)` pairs.
- Exact signature invariant cases: `48/175`.
- Exact signature variant cases: `127/175`.
- Shape invariant cases: `175/175`.
- Shape variant cases: `0/175`.
- Source-sum invariant cases: `48/175`.
- Pure source-choice variation cases: `127/175`.
- Parser-cost ties: `165/175`.
- Parser-cost near ties (`<=0.1` bit): `165/175`.
- Max source-sum span: `33865` at cutoff `10`, book `49`.
- Max parser-bit span: `8.214528` at cutoff `50`, book `64`.

## Decision

- Source dependency removed: `False`.
- Gate 94 shows every policy is stable across five cutoffs. This boundary audit checks the stronger condition needed to demote source choice itself: exact source-bearing signatures must be policy-invariant. They are not.
- The gate 94 result is therefore parser robustness, not source-choice demotion.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
