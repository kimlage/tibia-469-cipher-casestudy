# Executable v6 Literal-Span Origin Gate

Classification: `PROMOTED_EXECUTABLE_V6_LITERAL_SPAN_ORIGIN_LEDGER`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- Roundtrip: `70/70`.
- V5 external bits excluding seed: `4097.333`.
- V6 external bits excluding seed: `4065.013`.
- Delta vs v5: `-32.320` bits.
- Literal-span source events: `11`.
- Derived literal-span sources matching raw: `11`.
- Copy-hint bits replaced: `111.547`.
- Copy-hint bits remaining: `779.571`.
- Class counts: `{'both_endpoint_interval': 52, 'end_only': 55, 'fallback': 90, 'literal_span_source': 11}`.

## V6 Tape Breakdown

- Online x64 coarse-control: `876.412`.
- Copy tape after v6: `1863.425`.
- Literal-span origin program: `858.798` (`76.905` before declaration plus remaining fallback copy-hints).
- Residual length composition: `439.959`.
- Literal payload: `883.633`.
- Seed payload: `5633.990`.

## Decision

`PROMOTED_EXECUTABLE_V6_LITERAL_SPAN_ORIGIN_LEDGER`.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
