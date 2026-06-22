# Paid-Control Context Payload Codec Gate

Classification: `PAID_CONTROL_CONTEXT_PAYLOAD_CODEC_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether already-paid/derived control contexts reduce residual payload streams without adding a new book-mode header.

## Summary

| Target | Saving | Global bits | Context bits | Positive splits | Shuffled p95 | Beats p95 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `literal_payload_digits` | `-61.049` | `1544.176` | `1605.225` | `1/20` | `-14.049` | `False` |
| `copy_hint_rank_bucket` | `-61.147` | `1766.592` | `1827.740` | `0/20` | `-56.147` | `False` |
| `composition_quantile10` | `-60.345` | `464.948` | `525.293` | `1/20` | `-49.337` | `False` |

## Decision

Promotion requires positive context-code savings and shuffled-target p95. A promoted target reduces a residual payload stream only under already-paid control context; it does not generate the stream from scratch.
