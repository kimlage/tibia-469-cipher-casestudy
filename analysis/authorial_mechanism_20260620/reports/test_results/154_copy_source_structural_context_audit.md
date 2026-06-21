# 154. Copy Source Structural Context Audit

Classification: `copy_source_structural_contexts_rejected_global_retained`
Translation delta: `NONE`

## Purpose

Audits 152-153 showed that the tight cross-op near miss is blocked by
copy-source cost. This audit tests whether simple mechanical contexts
for the source exception prior reduce that ledger, or whether they just
over-split sparse source positions.

## Full-Corpus Models

| Context | Stream bits | Delta vs global | Contexts | Default hits |
|---|---:|---:|---:|---:|
| `global` | `2990.838` | `0.000` | `1` | `5/261` |
| `book_half` | `2996.710` | `5.872` | `2` | `5/261` |
| `copy_length_bucket` | `2998.489` | `7.651` | `3` | `5/261` |
| `book_position_bucket` | `2999.642` | `8.804` | `3` | `5/261` |
| `book_half_x_length_bucket` | `3001.242` | `10.404` | `6` | `5/261` |
| `copy_length_exact` | `3006.078` | `15.240` | `78` | `5/261` |

- Best non-global context: `book_half`
- Best non-global penalty: `5.872` bits

## Prefix Frozen Check

Best non-global candidate tested against global: `book_half`.

| Split | Test events | Global frozen | Candidate frozen | Candidate - global |
|---|---:|---:|---:|---:|
| `prefix_10_future_suffix` | `204` | `2470.698` | `2470.760` | `0.063` |
| `prefix_20_future_suffix` | `152` | `1889.260` | `1890.491` | `1.231` |
| `prefix_35_future_suffix` | `93` | `1173.755` | `1180.030` | `6.274` |
| `prefix_50_future_suffix` | `48` | `623.858` | `624.243` | `0.385` |
| `prefix_60_future_suffix` | `18` | `229.692` | `230.885` | `1.193` |

## Interpretation

The active global source exception prior remains best. Book half, copy
length bucket, exact copy length, book position, and combined
book-half/length-bucket contexts all add bits. The best structural
context is still worse on the full corpus and in prefix-frozen checks.
This means the source ledger blocking the near tie is not fixed by a
simple declared context; a future improvement needs a genuinely new
source derivation or a better source representation.

## Decision

- Compression bound unchanged.
- Global copy-source exception context retained.
- No plaintext, row0, or semantic change.
