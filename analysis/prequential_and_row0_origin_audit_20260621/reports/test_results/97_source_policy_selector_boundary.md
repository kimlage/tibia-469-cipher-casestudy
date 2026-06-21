# Source Policy Selector Boundary

Classification: `book_specific_policy_selector_audit_only`
Translation delta: `NONE`

## Purpose

Gate 96 rejected a single static source tie policy. This audit tests the
minimal obvious selector: use `latest_source` only where it is strictly
cheaper than `earliest_source`, otherwise keep `earliest_source`.

## Result

- Cases compared: `175`.
- Target books represented: `60`.
- Selector books: `[63]`.
- Selected alternate cases: `5`.
- Selector matches per-case minimum: `True`.
- Static primary extra bits vs per-case min: `39.331294937145`.
- Selector extra bits vs per-case min: `0.000000000000`.
- Savings vs static primary: `39.331294937145`.
- Paid selector floor: `6.906891` bits.
- Net bits vs static primary after selector floor: `32.424404`.

## Decision

- Source fields removed: `False`.
- Promotes generation explanation: `False`.
- A selector that uses latest_source only for book 63 and earliest_source otherwise matches the per-case policy minimum, but it is a book-specific selector over an already source-dependent parser. It can be kept as an audit-only compression boundary, not as a generation explanation.
- This does not promote a decoder-side source rule.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
