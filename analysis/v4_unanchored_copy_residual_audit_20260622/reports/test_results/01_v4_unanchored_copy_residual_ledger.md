# V4 Unanchored Copy Residual Ledger

Classification: `V4_UNANCHORED_COPY_RESIDUAL_BLOCKER_LEDGER`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

After executable v4 and the weak start-anchor gates, where is the copy residual actually concentrated?

## Summary

- Copy ops: `208`.
- Class counts: `{'start_only_weak_not_promoted': 40, 'end_only_promoted_v4': 56, 'neither_endpoint_anchored': 83, 'both_endpoints_anchored': 29}`.
- Copy bits by class: `{'start_only_weak_not_promoted': 375.85285497159896, 'end_only_promoted_v4': 491.113670935193, 'neither_endpoint_anchored': 693.0892500495785, 'both_endpoints_anchored': 275.07668282114065}`.
- Remaining fallback copy-hint bits: `1068.942`.
- Start-only weak count/bits: `40` / `375.853`.
- Neither-endpoint count/bits: `83` / `693.089`.
- Start-anchor random control cleared: `False`.
- Route decision: `representation_change_required_for_unanchored_copy_origin`.

## Top Remaining Copy-Hint Burden By Book

| Book | Copy-hint bits |
| ---: | ---: |
| `56` | `57.531` |
| `31` | `55.587` |
| `34` | `52.064` |
| `55` | `40.920` |
| `30` | `40.651` |
| `15` | `38.336` |
| `17` | `35.181` |
| `49` | `34.906` |
| `12` | `32.141` |
| `23` | `31.056` |
| `41` | `30.720` |
| `42` | `29.269` |
| `29` | `27.214` |
| `16` | `26.775` |
| `19` | `26.089` |

## Length Buckets By Class

```json
{
  "both_endpoints_anchored": {
    "len_0008": 4,
    "len_0016": 8,
    "len_0032": 5,
    "len_0064": 6,
    "len_0128": 2,
    "len_0256p": 4
  },
  "end_only_promoted_v4": {
    "len_0008": 10,
    "len_0016": 11,
    "len_0032": 10,
    "len_0064": 10,
    "len_0128": 12,
    "len_0256p": 3
  },
  "neither_endpoint_anchored": {
    "len_0008": 13,
    "len_0016": 21,
    "len_0032": 15,
    "len_0064": 20,
    "len_0128": 8,
    "len_0256p": 6
  },
  "start_only_weak_not_promoted": {
    "len_0008": 6,
    "len_0016": 11,
    "len_0032": 6,
    "len_0064": 7,
    "len_0128": 4,
    "len_0256p": 6
  }
}
```

## Decision

`V4_UNANCHORED_COPY_RESIDUAL_BLOCKER_LEDGER`: v4 remains promoted; start-only activation remains a weak clue, and the dominant remaining copy blocker is the neither-endpoint class.

The next constructive route should not be another endpoint activation selector. It needs a representation that creates or derives source-side boundary/chunk-origin marks for neither-endpoint copy intervals, or it must attack the still-external literal/seed payloads.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
