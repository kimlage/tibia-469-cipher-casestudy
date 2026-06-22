# Final Target-Conditioned Source Collapse Audit

Status: `analysis_only`
Classification: `TARGET_CONDITIONED_SOURCE_COLLAPSE_CLUE`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

If a separate target-stream mechanism supplies copied chunks, does
copy-source choice collapse to a small canonical rule?

## Result

- Copy events: `208`.
- Earliest matching source: `200/208` (`0.962`).
- Non-earliest exceptions: `8`.
- Legal source bits without target stream: `2550.594`.
- Oracle rank bits among matching sources: `232.902`.
- Earliest+exception total bits: `58.085`.
- Delta vs oracle rank bits: `-174.817` bits.
- Delta vs legal source bits: `-2492.509` bits.
- Random earliest-hit mean/p95/max: `120.011` / `129.000` / `139`.
- P(random earliest hits >= observed): `0.0000`.

This is a real mechanical clue about source choice under a target-conditioned
view. It is not a decoder-side generator because the rule grants the future
copied chunk. The practical implication is that source choice may be
downstream of the missing target-stream mechanism rather than an independent
primary blocker.

## Decision

- Promote as target-conditioned mechanical clue: `True`.
- Promote as source generator: `False`.
- The next generator blocker remains target-stream/skeleton-payload derivation.
- This does not change the compression bound.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Target-conditioned source collapse gate](test_results/01_target_conditioned_source_collapse_gate.md)
