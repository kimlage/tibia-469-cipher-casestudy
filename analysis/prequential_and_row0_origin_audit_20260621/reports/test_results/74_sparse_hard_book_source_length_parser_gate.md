# Sparse Hard-Book Source/Length Parser Gate

Classification: `sparse_hard_book_source_length_parser_roundtrips`
Translation delta: `NONE`

## Purpose

Gate 73 left book `66` as the immediate cutoff-60 hard case. This gate
switches the parser from dense dynamic programming over the full
previous-end domain to sparse Dijkstra over actually reachable states,
with source and length costs cached.

## Result

- Book: `66`.
- Digits: `210`.
- Roundtrip: `True`.
- Parser bits: `21.974212`.
- Gain versus raw digit uniform: `675.631` bits.
- Ops: `1`.
- Copy/literal ops: `1` / `0`.
- Transition evaluations: `41832`.
- Gate-72 transition proxy: `26096904`.
- Transition reduction vs proxy: `623.9x`.
- Visited states: `20932`.
- Heap pops/pushes: `211` / `21341`.
- Cache entries source/length/item/literal-length: `231` / `21321` / `3` / `206`.
- Elapsed: `0.033` seconds.

## Decision

- Sparse Dijkstra over reachable states turns the cutoff-60 hard book from a transition-proxy blocker into an executable exact book-local parser. This is implementation progress for the source/length parser, not a formula promotion.
- No compression-bound change is introduced.
- No parser or recipe-discovery promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
