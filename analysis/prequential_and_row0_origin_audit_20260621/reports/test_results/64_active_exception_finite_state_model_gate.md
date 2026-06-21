# Active Exception Finite-State Model Gate

Classification: `active_exception_finite_state_not_promotable`
Translation delta: `NONE`

## Purpose

Gate 63 rejects simple stop-rule separators for the residual
target-max exceptions. This gate asks whether a compact finite-state
context model over online, decoder-valid features can explain the same
exception stream better than an explicit exception list.

## Summary

- Copy events: `261`.
- Target-max exceptions: `19`.
- Context models tested: `231`.
- Uniform label cost: `261.000000` bits.
- Global KT label cost: `102.551512` bits.
- Explicit exception-list cost: `94.806385` bits.

## Best Finite-State Context Model

- Features: `['source_previous_end']`.
- Contexts used: `3`.
- Data bits: `104.897714`.
- Descriptor bits: `7.851749`.
- Total bits: `112.749463`.
- Delta versus explicit exception list: `+17.943077` bits.
- Densest context: `['no']` with `19` / `253` exceptions.

## Controls

- Permutation trials: `1000`.
- Permuted best-total min/median/max: `101.514618` / `112.218163` / `112.785912`.
- P(permuted best total <= observed): `0.638000`.
- Permuted models beating explicit-list cost: `0`.

## Decision

- Interpretation: The best online finite-state context model does not provide a controlled, compact replacement for the explicit residual exception list. Residual target-max boundaries remain nonlocal/ad hoc under the current evidence.
- Current compression bound remains `8156.049986` bits.
- Copy length remains a declared dependency.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- No new formula is emitted.
