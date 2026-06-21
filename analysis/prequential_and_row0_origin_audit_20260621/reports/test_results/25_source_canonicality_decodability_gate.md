# Source Canonicality Decodability Gate

Classification: `earliest_source_canonicality_encoder_side_only`
Translation delta: `NONE`

## Purpose

Audit 135 found that every declared copy source is the earliest legal
occurrence of the copied chunk at the declared length. This gate checks
whether that canonicality actually removes source from the decoder, or
whether it only regularizes the encoder's choice after the target chunk
is already known.

## Summary

- Copy items: `261`.
- Earliest exact-chunk sources: `261/261`.
- Unique source choices at declared length: `123/261`.
- Ambiguous source choices at declared length: `138/261`.
- Candidate count mean/max: `2.441` / `14`.
- Earliest exact-chunk rule decoder-computable: `False`.
- Source dependency removed by canonicality: `False`.
- Decodable default/exception source model: `5` defaults and `256` exceptions.
- Default/exception gain already promoted upstream: `28.862` bits.
- Source-free oracle delta at the cross-op near tie: `-11.209` bits.
- Simple source context promoted: `False`.

## Interpretation

Earliest-source canonicality is real, but it is not a decoder rule. The
rule asks for the earliest prior occurrence of the chunk that will be
copied; the decoder does not know that future chunk until the source and
length have already been resolved. The current valid representation
therefore remains the decodable default/exception source ledger, not a
source-free earliest-occurrence rule.

## Boundary

- No compression bound is promoted.
- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0/table origin remains exogenous.
