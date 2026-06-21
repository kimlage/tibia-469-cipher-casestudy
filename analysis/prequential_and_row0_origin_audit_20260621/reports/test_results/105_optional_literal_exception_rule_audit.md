# Optional Literal Exception Rule Audit

Classification: `optional_literal_exception_rule_audit_only`
Translation delta: `NONE`

## Purpose

Gate 103 reduced operation type to target-dependent copy availability plus
`17` optional literal exceptions. This audit tests whether those exceptions
are explained by simple non-book-id rules over skeleton fields.

## Result

- Available-copy rows: `225`.
- Optional literal exceptions: `17`.
- Availability baseline errors: `17`.
- Primitive / total deduped rules: `112` / `7070`.
- Best rule: `(length_le_5 and remaining_ge_10)`.
- Best rule errors: `3`.
- Best rule TP/FP/FN: `17` / `3` / `0`.
- Best single rule/errors: `length_le_4` / `4`.
- Error delta vs availability baseline: `-14`.
- Rule-conditioned skeleton records: `264`.
- Record delta vs gate 103 conditioned skeleton: `-14`.

## Controls

- Shuffled-label min/median/mean/max best errors: `12` / `16.0` / `15.844` / `18`.
- Empirical p(min errors <= observed): `0.000000`.

## Decision

- Promotes exception rule: `False`.
- A short target-dependent rule explains most optional literal exceptions: available-copy rows with length <= 5 and remaining >= 10 account for all 17 optional literals but incorrectly mark 3 copy rows. This is far better than shuffled controls, but it still depends on target copy availability and on the external length atlas, so it is a structural clue rather than a promoted generator.
- Taxonomy: `AUDIT_ONLY`.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
