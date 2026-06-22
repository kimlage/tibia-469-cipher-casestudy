# Skeleton Decoder Ambiguity Gate

Classification: `skeleton_decoder_ambiguity_blocks_generator`
Translation delta: `NONE`

## Purpose

Grant the exact source-free operation skeleton and measure what a decoder
still cannot emit without copy-source choices and literal payload.

## Summary

- Books tested: `60`.
- Skeleton operations/copies/literals: `261` / `208` / `53`.
- Copied/literal digits: `9301` / `266`.
- Seed payload digits granted operationally: `1696`.
- Legal source branching lower bound: `2550.594` bits.
- Literal payload branching: `883.633` bits.
- Combined decoder ambiguity lower bound after skeleton: `3434.227` bits.
- Equivalent lower-bound decimal choices: `10^1033.805`.
- Copy events with unique target-oracle source: `78/208`.
- Target-oracle source-choice residual: `232.902` bits.

## Source Candidate Counts

| Metric | Legal source count | Target-oracle matching source count |
| --- | ---: | ---: |
| Min | `1426` | `1` |
| Median | `4996.0` | `2.0` |
| Mean | `5542.111` | `2.870` |
| Max | `10984` | `14` |

## Decision

- Promotes skeleton decoder generator: `False`.
- The exact skeleton is a stable atlas, but it is not enough for decoder-side generation.
- Literal payload and copy-source choice remain external dependencies.
- The target-oracle matching-source row is diagnostic only; using it as a rule would depend on the future target chunk.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
