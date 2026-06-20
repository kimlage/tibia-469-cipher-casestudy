# Tape Inventory Self-Reference Search

Verdict: `controlled_inventory_reuse_order_not_promoted`. Translation delta: `NONE`.

This search asks whether the 16 tape components still contain a smaller
mechanical inventory layer. It encodes each component as literal runs plus
references to already emitted tape digits, charges source position and
length bits, and lets the real corpus and every control choose the best
minimum reference length from the same search set.

## Best Real Encoding

| Metric | Value |
|---|---:|
| Min reference length | `8` |
| Baseline tape inventory bits | `7165.4` |
| Self-reference inventory bits | `4437.7` |
| Rough saved bits | `2727.7` |
| Reference items | `62` |
| Referenced digits | `1316` |
| Literal digits | `841` |
| Literal runs | `38` |
| Component roundtrip | `True` |

## Previous-Component-Only Diagnostic

| Metric | Value |
|---|---:|
| Rough saved bits | `2172.2` |
| Reference items | `54` |
| Referenced digits | `1063` |

## Negative Controls

| Control | Runs | Mean saved bits | Max saved bits | p(>= observed) |
|---|---:|---:|---:|---:|
| `component_digit_shuffle` | `300` | `-144.0` | `-141.7` | `0.0033` |
| `random_same_lengths` | `300` | `-144.0` | `-141.7` | `0.0033` |
| `component_order_shuffle` | `300` | `2635.2` | `2777.8` | `0.1561` |

## Boundary

The result is a mechanical inventory refinement only. It does not explain
the 10x10 pair-table placement, does not translate the books, and does
not support private authorial-intent claims.
