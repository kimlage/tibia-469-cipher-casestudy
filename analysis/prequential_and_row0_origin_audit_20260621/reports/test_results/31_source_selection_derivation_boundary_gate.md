# Source Selection Derivation Boundary Gate

Classification: `source_selection_encoder_canonical_decoder_dependency_retained`
Translation delta: `NONE`

## Purpose

Copy source is one of the remaining declared recipe dependencies. This
gate consolidates source canonicality, negative controls, the distance
model, and the source-state gates to decide whether source selection has
become a decoder-computable derivation or remains a declared ledger.

## Summary

- Copy items: `261`.
- Earliest-source hits: `261/261`.
- Latest-source hits: `123/261`.
- Previous-source hits: `0/261`.
- Previous-source-plus-length hits: `5/261`.
- Unique / ambiguous source-candidate ops: `123` / `138`.
- Random candidate expected hits: `169.473`.
- Probability all sources are earliest under uniform candidate choice: `5.990e-72`.
- Backward-distance replacement penalty: `25.551` bits.
- Backward-distance prefix losses: frozen `5/5`, online `5/5`.
- Earliest exact-chunk rule decoder-computable: `False`.
- Source dependency removed by canonicality: `False`.
- Required active source state: `(book_pos, previous_item, previous_copy_source, previous_copy_length)`.
- Best state-free default: `state_free_back_current_length` (`+15.186` bits).

## Interpretation

The source choice has a strong encoder-side rule: it is always the
earliest legal source for the copied target chunk. That is not enough to
derive the source during decoding, because the copied target chunk is not
known until source and length are resolved. Controls also reject simple
alternatives: latest/previous source rules do not match, backward
distance is worse on full corpus and all prefix splits, and state-free
defaults lose to the active previous-source-plus-length model.

## Boundary

- Source selection is canonical but still declared.
- No compression bound is promoted.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
