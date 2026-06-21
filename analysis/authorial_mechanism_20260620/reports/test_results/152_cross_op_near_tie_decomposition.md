# 152. Cross-Op Near-Tie Decomposition

Classification: `cross_op_near_tie_explained_no_promotion`
Translation delta: `NONE`

## Purpose

Audit 151 found a very close rejected repair: the best cross-op optional
literal copy candidate was only `+0.027` bits worse than the active
formula. This audit decomposes that near tie under the same active ledger
to verify that it is a real loss, not a rounding or accounting artifact.

## Candidate

- Book/op/pos: `12` / `8` / `82`
- Source/copy length: `102` / `11`
- Crossed digits beyond original literal: `7`
- Candidate total bits: `8177.344087`
- Active total bits: `8177.316653`
- Total delta: `0.027434` bits

## Component Delta

| Component | Delta bits |
|---|---:|
| `fixed_bits` | `0.000000` |
| `literal_bits_no_payload` | `-4.000000` |
| `literal_payload_bits` | `-7.430519` |
| `item_type_stream_bits` | `-1.417248` |
| `copy_length_default_exception_bits` | `1.638663` |
| `copy_source_default_exception_bits` | `11.236537` |

- Component-sum delta: `0.027434` bits
- Accounting difference: `0.000000000000` bits

## Interpretation

The candidate saves literal structure/payload bits, but the added copy
ledger costs more than those savings under the active default/exception
source and length models. The near tie is therefore an actual local
cost boundary. It should not be promoted without a new charged model
that explains why this cross-op copy should be preferred.

## Decision

- Compression bound unchanged.
- Candidate not promoted.
- Row0 origin, plaintext, and semantic status unchanged.
