# 135. Copy Source Canonicality Audit

Classification: `copy_sources_are_earliest_exact_chunk_occurrences`
Translation delta: `NONE`

## Purpose

The compact online formula still declares copy source and copy length.
This audit checks whether the declared copy source is arbitrary or
canonical relative to the copied chunk: for every copy, it enumerates all
legal prior occurrences of the copied chunk at the same length.

## Result

- Active bits: `8343.062`
- Recomputed bits: `8343.062`
- Roundtrip: `70/70`
- Copy items: `261`
- Earliest-source copies: `261/261`
- Unique-source copies: `123/261`
- Latest-source copies: `123/261`
- Candidate count min/mean/max: `1` / `2.441` / `14`
- Length equals target-max extension: `238/261`

## Interpretation

Every declared source is the earliest legal occurrence of the
actual copied chunk at the declared copy length. This supports a
canonical encoder-side source rule, not arbitrary source choice.
It does not remove the decoder dependency on copy source, because
the copied chunk is not otherwise available at decode time.

## Boundary

- No plaintext or translation is introduced.
- Row0/table origin is unchanged.
- Copy source remains a declared decoding dependency.
