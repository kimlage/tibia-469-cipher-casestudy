# 143. Current Literal Payload Profile Audit

Classification: `literal_payload_order2_retained_for_current_profile`
Translation delta: `NONE`

## Purpose

Audit 121 previously found that literal payload order-1 generalized better
than the then-active order-2 context. This audit retests that claim on the
current online-reparse/default-exception formula before carrying it into
the current generation-explanation profile.

## Full Corpus

| Order | Bits | Contexts | Delta vs order2 |
|---:|---:|---:|---:|
| `0` | `2842.432` | `1` | `+228.771` |
| `1` | `2709.628` | `11` | `+95.968` |
| `2` | `2613.661` | `98` | `+0.000` |
| `3` | `2706.054` | `407` | `+92.393` |

## Prefix Splits

| Cutoff | Order1 online gain | Order2 online gain | Order1 frozen gain | Order2 frozen gain |
|---:|---:|---:|---:|---:|
| `10` | `88.467` | `134.170` | `82.526` | `118.070` |
| `20` | `46.951` | `49.722` | `46.641` | `45.653` |
| `35` | `25.332` | `21.624` | `25.651` | `18.733` |
| `50` | `14.195` | `15.725` | `13.107` | `13.027` |
| `60` | `1.618` | `2.668` | `1.618` | `2.668` |

## Decision

- Order1 full-corpus delta vs order2: `+95.968` bits.
- Order1 aggregate online delta vs order2: `+47.346` bits.
- Order1 aggregate frozen delta vs order2: `+28.609` bits.
- Order1 frozen win cutoffs: `[20, 35, 50]`.
- Current profile retains literal payload order2.
- Compression bound and frozen-prefix generation profile are unchanged.
- `row0` and semantics are unchanged.
