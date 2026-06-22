# Tales/LIBSearch Book Database Probe

Classification: `WEAK_PROVENANCE_CLUE_CORPUS_LOCATION_SURFACE_NOT_AUTHORING_CONTROL`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

The public Tales/LIBSearch database matches `70` canonical 469 books, including `60` derived books.
It supplies map coordinates for `71` matched records but only `2` unique coordinate(s).

It does not satisfy the clean topology contract: no root LICENSE file was observed, and the book records do not expose container identity or slot/read order.

## Heldout Diagnostics

| Target | Splits | Positive | Total Saving Bits | Decision |
| --- | ---: | ---: | ---: | --- |
| `coarse_control` | 5 | 0 | -84.396 | `audit_only_not_integrated` |
| `op_type` | 5 | 0 | -25.249 | `audit_only_not_integrated` |
| `copy_hint_rank_bucket` | 5 | 0 | -12.925 | `audit_only_not_integrated` |

## Decision

No `PROMOTED_EXTERNAL_CONTROL_SOURCE` and no v9 reduction.

This is a useful provenance clue because it gives high text coverage plus version/location/map links, but it remains a community corpus surface rather than an authoring/control surface.

## Sources

- https://github.com/s2ward/tibia
- https://raw.githubusercontent.com/s2ward/tibia/main/data/books/book_database.json
- https://talesoftibia.com/services/

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
