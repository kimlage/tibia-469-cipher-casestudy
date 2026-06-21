# Seed Exception Signal Cost Audit

Classification: `seed_exception_cannot_promote_under_nonnegative_signal_cost`
Translation delta: `NONE`

## Purpose

Audits 18-20 show that a raw seed for book `0` closes the local online
bootstrap failure but fails complete formula rescoring. This audit asks
whether any reasonable exception-signaling policy can rescue promotion.

## Summary

- Local seed saving: `10.499` bits.
- Zero-cost full-formula delta vs online: `0.979` bits.
- Descriptor threshold required for promotion: `< -0.979` bits.
- Nonnegative descriptor can promote: `False`.
- Literal-payload penalty: `37.821` bits.
- Non-payload savings: `36.842` bits.

## Policies

| Policy | Descriptor bits | Local net vs online | Full formula delta vs online | Promotes |
|---|---:|---:|---:|---|
| `zero_cost_deterministic_raw_if_online_loses` | `0.000` | `10.499` | `0.979` | `False` |
| `one_book_index_exception` | `6.129` | `4.370` | `7.108` | `False` |
| `exception_count_plus_one_book_index` | `12.279` | `-1.780` | `13.258` | `False` |
| `book_bitmask` | `70.000` | `-59.501` | `70.979` | `False` |

## Decision

- The best-case zero-cost fallback is already `0.979` bits worse than the existing online formula.
- Any real descriptor or exception signal makes the formula promotion strictly worse.
- The seed exception remains a bootstrap explanation only; no new compression bound, row0 derivation, plaintext claim, or case reopening is introduced.
