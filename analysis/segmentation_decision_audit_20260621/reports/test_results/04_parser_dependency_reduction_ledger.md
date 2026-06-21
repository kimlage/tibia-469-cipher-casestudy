# Parser Dependency Reduction Ledger

Classification: `conditional_parser_dependency_reduction_not_source_free_generator`
Translation delta: `NONE`

## Purpose

This gate asks whether the segmentation parser clue can reduce declared
`(source,length)` dependency records, and where that reduction stops.
It does not change the compression bound and does not emit a source-free
generator.

## Ledger

| Representation | Operation/skeleton records | Literal chunks | Copy/source exception records | Parser rule records | Total materialized records |
|---|---:|---:|---:|---:|---:|
| Exact skeleton ledger | `261` | `53` | `208` | `0` | `522` |
| Target-text parser projection | `262` | `54` | `1` | `1` | `318` |

## Delta

- Materialized record delta vs exact skeleton: `-204`.
- Conditional copy `(source,length)` fields removed: `414`.
- Copy `(source,length)` fields retained as exceptions: `2`.
- Literal chunk delta: `1`.
- Operation record delta: `1`.

## Full Greedy Parser Control

Control parser: at each target position, if a prior match exists, choose
the longest previous target match with earliest-source tie; otherwise emit
literal digits until the next match becomes available.

- Exact books: `39/60`.
- Mismatch books: `21/60`.
- Mismatch book ids: `[10, 12, 13, 14, 16, 17, 23, 25, 26, 32, 34, 38, 39, 42, 44, 49, 52, 55, 57, 58, 65]`.

## Decision

- The parser rule conditionally removes most copy source/length declarations when target text and copy starts are granted.
- It does not remove the segmentation/op-start atlas: the full greedy parser fails on `21/60` non-seed books.
- The result is a genuine generation-explanation improvement, but only for target-text-aware parsing.
- Source-free book generation is not promoted.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
