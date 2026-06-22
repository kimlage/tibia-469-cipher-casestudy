# Unanchored Copy-Origin Representation Gate

Classification: `PROMOTED_UNANCHORED_COPY_ORIGIN_REPRESENTATION`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can the v4 neither-endpoint copy blocker be reduced by changing the source origin representation, rather than tuning endpoint activation?

## Source Endpoint Memory

- V4 residual bits: `3232.726`.
- Source-endpoint memory residual bits: `3219.336`.
- Representation declaration bits: `1.585`.
- Delta vs v4: `-13.390`.
- Delta after declaration vs v4: `-11.805`.
- Class counts: `{'fallback': 101, 'end_only': 55, 'both_endpoint_interval': 52}`.
- Shuffled residual p05: `3229.804`.
- Shuffled interval-hit p95: `35`.
- Beats shuffled p05: `True`.

## Hit-Only Source Endpoint Memory

- Residual bits: `3230.940`.
- Delta vs v4: `-1.787`.
- Class counts: `{'fallback': 123, 'end_only': 56, 'both_endpoint_interval': 29}`.

## Within Prior Span Interval

- Fitting copy ops: `116/208`.
- Paid bits on fitting ops: `2257.880`.
- Copy-hint bits on fitting ops: `976.759`.
- Delta on fitting ops: `1281.121`.

## Decision

`PROMOTED_UNANCHORED_COPY_ORIGIN_REPRESENTATION`.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
