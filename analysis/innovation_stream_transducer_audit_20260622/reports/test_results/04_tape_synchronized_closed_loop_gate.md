# Tape Synchronized Closed Loop Gate

Classification: `tape_synchronization_weak_clue`
Translation delta: `NONE`

## Purpose

Test whether the structured innovation tape can synchronize a closed-loop
copy transducer. The decoder is granted book length, true prior material,
and the canonical tape start for the book. It is not granted the target
digits inside the book.

## Summary

- Literal tape digits: `266`.
- Books tested: `60`.
- Beam width: `240`.
- Copy candidate limit: `80`.
- Top-1 exact books: `0`.
- Exact books in finished beam: `0`.
- Exact-in-beam shuffled p95: `0.0`.
- True-prefix survival books: `19`.
- True-prefix survival shuffled p95: `7.449999999999999`.
- Mean true-prefix max fraction: `0.002495`.
- Mean true-prefix max shuffled p95: `0.001134`.
- Mean top prefix-match fraction: `0.000950`.
- Mean top tape digits consumed: `0.066667`.
- Promotes tape-synchronized generator: `False`.
- Weak tape synchronization clue: `True`.

This gate tests the constructive synchronization hypothesis: with canonical tape positions, book lengths, and true prior material granted, can a closed-loop beam produce the books using only next tape digit emissions and copies from prior material?

## Decision

- A generator is promoted only if exact books survive above shuffled-tape controls.
- A weak clue is recorded only if prefix survival beats controls.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
