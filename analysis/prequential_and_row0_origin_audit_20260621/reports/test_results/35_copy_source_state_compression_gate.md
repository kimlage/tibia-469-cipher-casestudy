# Copy Source State Compression Gate

Classification: `copy_source_previous_end_state_compression_valid`
Translation delta: `NONE`

## Purpose

The active source default was previously described as depending on
`previous_copy_source` and `previous_copy_length`. This gate tests
whether that state can be compressed to the decoder-equivalent scalar
`previous_copy_end = previous_copy_source + previous_copy_length`
without changing default/exception classification.

## Summary

- Previous pair state key: `(book_pos, previous_item, previous_copy_source, previous_copy_length)`.
- Compressed state key: `(book_pos, previous_item, previous_copy_end)`.
- Source default stream bits preserved: `2990.838`.
- Default/exception counts preserved: `5` / `256`.
- End-default mismatches: `0`.
- Total candidate state proxy: `969111171` -> `26758611`.
- Total proxy reduction: `942352560` (`97.239%`).
- Cutoff-10 proxy: `302879952` -> `8286852`.
- Cutoff-10 proxy reduction: `294593100` (`97.264%`).
- Best fully state-free source default remains `state_free_back_current_length`, `15.186` bits worse.

## Interpretation

The active source default does not need the full previous copy pair for
future source-cost classification; `previous_copy_end` is sufficient.
This reduces the path-state proxy while preserving the same
default/exception ledger. It is still not a complete active parser:
recipe discovery remains unproved, and the state is compressed rather
than eliminated.

## Boundary

- No compression-bound change is introduced.
- No parser or recipe-discovery promotion is introduced.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
