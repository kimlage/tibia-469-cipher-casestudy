# 159. Row0 Paid Anchor Reduction Gate

Classification: `paid_partial_worksheet_anchor_reduction_not_promoted`
Translation delta: `NONE`

## Purpose

Audit 156 showed that freezing 13 worksheet-style anchors reduces the
residual lookup by `54.178` bits before paying anchor/source costs. This
gate asks whether that reduction survives paid encodings of the anchor
pairs and labels.

## Summary

- Lookup baseline: `160.521` bits.
- All anchors nominal reduction before cost: `54.178` bits.
- All anchors after paying pair identities only: `13.777` bits.
- All anchors after paying explicit pair+label data: `-11.852` bits.
- Rare-singleton nominal control p: `0.0004`.
- Rare-singleton explicit pair+label net: `0.000` bits.
- Diagonal-family paid net with label arrangement: `4.901` bits.
- Diagonal-family nominal control p: `0.9816`.

## Model Table

| Anchor model | k | Nominal reduction | Pair-only net | Explicit pair+label net | Family-paid+label net | Control p |
|---|---:|---:|---:|---:|---:|---:|
| `all_declared_worksheet_anchors` | `13` | `54.178` | `13.777` | `-11.852` | `-11.852` | `0.0014` |
| `promoted_surface_anchors_only` | `2` | `8.536` | `-2.000` | `-3.000` | `-3.000` | `0.2010` |
| `rare_singleton_anchors` | `5` | `28.637` | `6.907` | `0.000` | `0.000` | `0.0004` |
| `diagonal_E_pressure_anchors_all_pairs_cost` | `5` | `12.878` | `-8.852` | `-8.852` | `-8.852` | `0.9992` |
| `diagonal_E_pressure_anchors_diagonal_family_cost` | `5` | `12.878` | `-8.852` | `-8.852` | `4.901` | `0.9816` |
| `unique_star_anchor` | `1` | `5.781` | `0.000` | `0.000` | `0.000` | `0.1284` |
| `weak_anchors_only` | `10` | `40.800` | `6.032` | `-8.852` | `-8.852` | `0.0140` |

## Interpretation

The strongest apparent anchor signal is the rare-singleton group: random
subsets almost never match its nominal lookup reduction. But that is
exactly because the labels are rare. Once the rare labels are paid as
anchor data, the net is effectively zero. The full 13-anchor worksheet
model is worse than lookup after explicit pair+label cost. The diagonal
family has a positive narrow lower bound only when the diagonal family
is supplied, but its nominal reduction is ordinary under diagonal-subset
controls (`p=0.9816`). Therefore the partial worksheet hypothesis remains
a plausible description of how a human table could be organized, not a
promoted origin formula.

## Boundary

- No row0-origin formula is promoted.
- No book-generation compression bound is changed.
- No plaintext, translation, semantic reading, or case reopening is introduced.
