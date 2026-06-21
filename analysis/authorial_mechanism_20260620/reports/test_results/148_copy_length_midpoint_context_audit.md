# 148. Copy Length Midpoint Context Audit

Classification: `copy_length_midpoint_context_supported_not_formula_change`
Translation delta: `NONE`

## Purpose

The active copy-length default/exception ledger uses a fixed context:
`book_id < 35` versus `book_id >= 35`. This audit tests whether that
midpoint context is supported, removable, or merely a searched boundary.

## Full-Corpus Context Test

- Global stream bits: `1354.644`
- Midpoint-35 stream bits: `1340.806`
- Midpoint gain vs global: `13.839` bits
- Best searched boundary: cutoff `37` at `1340.550` bits
- Best searched boundary gain vs global: `14.095` bits
- Midpoint boundary rank among 69 cuts: `2`

| Rank | Cutoff | Stream bits | Gain vs global |
|---:|---:|---:|---:|
| `1` | `37` | `1340.550` | `14.095` |
| `2` | `35` | `1340.806` | `13.839` |
| `3` | `36` | `1341.973` | `12.671` |
| `4` | `29` | `1341.985` | `12.660` |
| `5` | `38` | `1342.688` | `11.957` |
| `6` | `33` | `1342.822` | `11.822` |
| `7` | `34` | `1343.845` | `10.799` |
| `8` | `27` | `1344.212` | `10.433` |
| `9` | `32` | `1344.703` | `9.942` |
| `10` | `30` | `1344.705` | `9.939` |

## Permutation Controls

- Controls: `300` random book-id permutations, seed `469`
- P(permuted midpoint gain >= observed): `0.0033`
- P(permuted best-boundary gain >= observed): `0.0033`
- Permuted midpoint gain summary: `{'n': 300, 'min': -31.72219632227575, 'median': -21.320364638333672, 'mean': -20.898385299603927, 'max': -8.333333262376073}`
- Permuted best-boundary gain summary: `{'n': 300, 'min': -7.762244836456603, 'median': 1.2365698681435333, 'mean': 1.5401375470166885, 'max': 10.977134125879957}`

## Prefix Future-Suffix Check

| Split | Train events | Test events | Global frozen | Midpoint frozen | Midpoint - global |
|---|---:|---:|---:|---:|---:|
| `prefix_10_future_suffix` | `57` | `204` | `1094.170` | `1067.755` | `-26.416` |
| `prefix_20_future_suffix` | `109` | `152` | `810.564` | `789.289` | `-21.275` |
| `prefix_35_future_suffix` | `168` | `93` | `503.875` | `490.919` | `-12.955` |
| `prefix_50_future_suffix` | `213` | `48` | `261.796` | `250.860` | `-10.936` |
| `prefix_60_future_suffix` | `243` | `18` | `82.260` | `76.767` | `-5.493` |

Frozen midpoint-minus-global summary: `{'n': 5, 'min': -26.41571288994669, 'median': -12.955352187949131, 'mean': -15.41506768288516, 'max': -5.49341349778112}`

## Interpretation

The midpoint context is not removed: it beats a global copy-length
exception stream by `13.839` bits and is second among all one-cut
boundaries. The best searched boundary is cutoff `37`, only `0.256`
bits better, so promoting that searched cutoff would add ad-hoc
description cost without a meaningful improvement. Permutation
controls show that the observed midpoint and best-boundary gains are
not typical under shuffled book ids.

Prefix-frozen scoring supports the same direction: midpoint beats
the global context in all tested future-suffix splits, with frozen
gaps from `5.493` to `26.416` bits. This strengthens the copy-length
context as a real mechanical component, while still leaving full
recipe discovery and row0 origin unchanged.

## Decision

- Keep the declared midpoint copy-length context.
- Do not promote the searched cutoff-37 boundary.
- Do not replace the context with a global model.
- Compression bound, row0 origin, plaintext, and semantic status remain unchanged.
