# Chayenne Holdout Boundary Alignment Gate

Classification: `PROMOTED_CHAYENNE_SUBSPAN_MODULE_HOLDOUT_CLUE_NOT_EVENT_POLICY`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

| Metric | Value |
| --- | ---: |
| Chayenne copy spans | `2` |
| Replay-boundary aligned spans | `0` |
| Consumer-boundary aligned spans | `0` |
| Contained in one replay event | `2` |
| Contained in one consumer segment | `2` |

## Span Rows

| Copy | Source Span | Replay Event | Consumer Segment | Replay Boundary | Consumer Boundary |
| ---: | --- | --- | --- | ---: | ---: |
| `0` | `160-196` | `literal:0-242` | `seed_book_1:144-236` | `False` | `False` |
| `1` | `347-360` | `literal:250-420` | `seed_book_2:236-413` | `False` | `False` |

## Decision

`Chayenne validates subspans inside the innovation module bank, not replay event boundaries`

This preserves the positive external holdout result while locating it at subspan/module-bank level, not at replay-event-policy level.

Next blocker: `external holdout validation still does not derive the replay event policy or innovation origin`

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
