# Executable Decoder Contract

Status: `analysis_only`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Contract

This decoder reconstructs the numeric 469 books from explicit external tapes. It is a reproducible execution contract, not an authorial formula.

- Seed books: `seed books 0..9 digit payload`.
- Exact books: `70/70`.
- Derived operation count: `261`.
- Roundtrip: `True`.
- Stream digits: `11263`.

## External Tapes

- seed books 0..9 digit payload
- coarse type:length_bucket control stream
- book-level composition index for exact lengths
- literal innovation payload tape
- copy hint rank/source tape
- macro/template correction tape when program misses

## Target Dependencies

- literal payload tape is target digits
- copy hint ranks are computed against canonical target chunk/source availability
- composition index is computed from exact target lengths

## Decision

The executable contract is valid as an audit baseline. A later macro program must reduce these tapes after paying grammar/corrections before it can be promoted as generation progress.
