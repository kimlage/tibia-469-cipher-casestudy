# DP Min-Length Sweep Control

Verdict: `dp_min_len_sweep_retains_min_len_6`. Translation delta: `NONE`.

This audit varies the DP sequential LZ `min_len` parameter under the
same literal-run plus absolute-source copy cost model. It holds numeric
book order fixed for the main sweep, then runs focused digit-shuffle and
book-order-shuffle controls for the two closest settings: `min_len=5`
and `min_len=6`.

## Sweep

| min_len | Total bits | Delta vs current | Copy items | Copied digits | Literal runs | Literal digits | Roundtrip |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `3` | `9982.2` | `158.9` | `341` | `10681` | `63` | `582` | `70/70` |
| `4` | `9867.3` | `44.0` | `334` | `10687` | `80` | `576` | `70/70` |
| `5` | `9827.7` | `4.4` | `305` | `10580` | `86` | `683` | `70/70` |
| `6` | `9823.3` | `0.0` | `281` | `10468` | `84` | `795` | `70/70` |
| `7` | `9871.6` | `48.3` | `257` | `10334` | `78` | `929` | `70/70` |
| `8` | `9977.5` | `154.2` | `237` | `10206` | `77` | `1057` | `70/70` |
| `9` | `10055.6` | `232.3` | `226` | `10125` | `78` | `1138` | `70/70` |
| `10` | `10312.6` | `489.3` | `208` | `9971` | `81` | `1292` | `70/70` |
| `11` | `10462.9` | `639.6` | `194` | `9855` | `79` | `1408` | `70/70` |
| `12` | `10694.3` | `871.0` | `183` | `9734` | `79` | `1529` | `70/70` |

## Focused Controls

| min_len | Control | Runs | Min bits | Mean bits | Count <= observed |
|---:|---|---:|---:|---:|---:|
| `5` | digit shuffle, preserve book lengths | `20` | `39508.4` | `39526.2` | `0` |
| `5` | book order shuffle | `20` | `9761.3` | `10021.3` | `1` |
| `6` | digit shuffle, preserve book lengths | `20` | `39533.0` | `39546.8` | `0` |
| `6` | book order shuffle | `20` | `9744.9` | `10039.5` | `1` |

## Interpretation

The current `min_len=6` setting remains the best DP
sequential LZ configuration in the tested range. The nearest alternate
is `min_len=5` at `9827.7` bits, `4.4` bits worse.
No new formula is promoted from this sweep.
The book-order shuffle rows are diagnostic only: occasional gross
wins do not supply a zero-cost external order and therefore do not
override the earlier permutation-cost order audit.

## Boundary

This is a mechanical parameter audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
