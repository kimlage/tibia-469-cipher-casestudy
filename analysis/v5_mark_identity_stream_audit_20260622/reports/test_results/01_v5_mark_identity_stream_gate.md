# V5 Mark-Identity Stream Gate

Classification: `V5_MARK_IDENTITY_STREAM_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- Rows: `101`.
- Copy-hint bits: `891.118`.
- Source mark rank median: `705`.
- Global rank-delta median: `274`.
- Best valid model: `global_delta_rank_plus_offset`.
- Best valid delta vs copy-hint: `105.634` bits.

## Model Deltas

| Model | Bits | Delta vs copy-hint |
| --- | ---: | ---: |
| `absolute_rank_plus_offset` | `1044.148` | `153.030` |
| `global_delta_rank_plus_offset` | `996.752` | `105.634` |
| `book_delta_rank_plus_offset` | `1018.968` | `127.850` |
| `invalid_rank_bucket_plus_offset_lower_bound` | `455.870` | `-435.248` |

## Decision

`V5_MARK_IDENTITY_STREAM_NOT_PROMOTED`: valid exact-rank streams remain more expensive than copy-hints.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
