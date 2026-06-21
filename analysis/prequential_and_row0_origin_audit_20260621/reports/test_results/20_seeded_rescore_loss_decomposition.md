# Seeded Rescore Loss Decomposition

Classification: `seed_rescore_loss_explained_by_literal_payload_penalty`
Translation delta: `NONE`

## Purpose

Audit 19 rejected the book-0 seed policy as a full-formula promotion.
This audit decomposes that rejection by component so the local-vs-full
scorer mismatch is explicit.

## Summary

- Local bootstrap saving from audit 18: `10.499` bits.
- Seeded formula delta vs online: `0.979` bits.
- Seeded literal-payload penalty: `37.821` bits.
- Seeded non-payload savings: `36.842` bits.
- Payload penalty exceeds local seed saving: `True`.
- Book-bounded seeded delta vs online: `305.198` bits.

## Seeded Online Formula

| Component | Effect | Delta bits |
|---|---|---:|
| `literal_length_or_structure` | `saving` | `-8.000` |
| `literal_payload` | `penalty` | `37.821` |
| `copy_address` | `saving` | `-19.480` |
| `copy_length` | `saving` | `-7.770` |
| `item_type` | `saving` | `-1.593` |

## Book-Bounded Seeded Formula

| Component | Effect | Delta bits |
|---|---|---:|
| `literal_length_or_structure` | `saving` | `-8.000` |
| `literal_payload` | `penalty` | `104.400` |
| `copy_address` | `penalty` | `136.412` |
| `copy_length` | `penalty` | `69.818` |
| `item_type` | `penalty` | `2.568` |

## Decision

- The seed policy fails full rescoring because literal payload cost dominates the local seed saving.
- This clarifies the boundary between local bootstrap accounting and complete formula promotion.
- No plaintext, translation, row0-origin change, or case reopening is introduced.
