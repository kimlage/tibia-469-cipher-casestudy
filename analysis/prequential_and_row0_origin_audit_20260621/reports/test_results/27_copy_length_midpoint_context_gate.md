# Copy Length Midpoint Context Gate

Classification: `copy_length_midpoint_context_generalizes_searched_cutoff_rejected`
Translation delta: `NONE`

## Purpose

The active copy-length default/exception stream uses the declared context
`book_id < 35` versus `book_id >= 35`. This gate checks whether that
midpoint split is a supported mechanical context or a removable/posthoc
parameter, and whether the searched cutoff `37` should replace it.

## Summary

- Copy-length events: `261`.
- Global stream bits: `1354.644`.
- Midpoint-35 stream bits: `1340.806`.
- Midpoint gain vs global: `13.839` bits.
- Best searched cutoff: `37`.
- Best cutoff gain vs global: `14.095` bits.
- Best cutoff delta vs midpoint: `0.256` bits.
- Midpoint rank among one-cut boundaries: `2`.
- Prefix-frozen midpoint wins: `5/5`.
- Prefix-frozen midpoint-minus-global min/mean/max: `-26.416` / `-15.415` / `-5.493` bits.
- P(permuted midpoint gain >= observed): `0.0033`.
- P(permuted best-boundary gain >= observed): `0.0033`.

## Interpretation

The midpoint context is retained as a real mechanical component: it beats
the global copy-length context by `13.839` bits, wins all `5/5`
prefix-frozen future-suffix checks, and is unusual under 300 book-id
permutation controls. The searched cutoff `37` is only `0.256` bits
better than the natural midpoint, so promoting it would add ad-hoc
description cost for a sub-bit local gain.

## Boundary

- No compression bound is promoted.
- Recipe discovery remains partial; this validates one learned component.
- No plaintext, translation, semantic reading, row0 change, or case reopening is introduced.
