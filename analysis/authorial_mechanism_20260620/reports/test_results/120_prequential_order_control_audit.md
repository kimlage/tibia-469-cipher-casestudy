# 120. Prequential Order Control Audit

Classification: `prequential_predictive_not_numeric_order_specific`
Translation delta: `NONE`

## Purpose

Audit 118 showed that prefix-trained learned components beat uniform on
future books. This control asks whether the numeric prefixes `0..N` are
special, or whether random same-size training sets provide the same or
better learned distributions.

Lower `vs uniform` values are better because they save more bits.

## Results

| Train books | Prefix online vs uniform | Control online mean | Online p(control <= prefix) | Prefix frozen vs uniform | Control frozen mean | Frozen p(control <= prefix) |
|---:|---:|---:|---:|---:|---:|---:|
| `10` | `-154.382` | `-247.203` | `1.0000` | `-116.442` | `-132.760` | `0.6623` |
| `20` | `-86.057` | `-221.761` | `1.0000` | `-62.497` | `-159.715` | `0.9940` |
| `35` | `-48.145` | `-165.553` | `1.0000` | `-36.022` | `-144.027` | `1.0000` |
| `50` | `-37.583` | `-101.061` | `0.9830` | `-35.063` | `-95.595` | `0.9850` |
| `60` | `-10.316` | `-51.800` | `0.9750` | `-11.070` | `-50.792` | `0.9670` |

## Interpretation

The prefix-trained components still beat uniform on every cutoff, so
the learned payload/copy-length/item-type distributions are not empty.
However, numeric prefixes are not unusually strong compared with random
same-size train sets; in these controls, random sets usually save more
bits because they sample the full corpus distribution more evenly.

Therefore the prequential result should be kept as partial learned-
component evidence, not as a proof that the books were authored or
generated in numeric order.

## Boundary

- `compression_bound` remains `8561.792` bits.
- No row0/table origin formula is promoted.
- No plaintext, glossary, or authorial-intent claim is introduced.
