# Copy Length Code Reparse

Verdict: `controlled_copy_length_code_improvement`. Translation delta: `NONE`.

This audit reparses the 70 numeric books with alternative copy-length
codes while preserving the same literal-run and absolute `source_pos`
copy vocabulary. The previous DP formula used Elias gamma for
`length-min_len+1`; this test includes Elias delta, unary, and Rice
codes with explicit parameter cost for `k`.

## Length-Code Sweep

| Rank | min_len | Length model | Model bits | Total bits | Delta vs current | Copy items | Copied digits | Length bits | Roundtrip |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `1` | `5` | `rice_k4` | `5` | `9596.5` | `-226.8` | `278` | `10455` | `1843` | `70/70` |
| `2` | `5` | `rice_k5` | `5` | `9605.0` | `-218.4` | `268` | `10403` | `1800` | `70/70` |
| `3` | `6` | `rice_k4` | `5` | `9612.2` | `-211.1` | `260` | `10362` | `1741` | `70/70` |
| `4` | `6` | `rice_k5` | `5` | `9620.1` | `-203.2` | `259` | `10356` | `1743` | `70/70` |
| `5` | `5` | `rice_k6` | `5` | `9739.8` | `-83.5` | `261` | `10365` | `1889` | `70/70` |
| `6` | `6` | `rice_k6` | `5` | `9749.4` | `-73.9` | `256` | `10340` | `1853` | `70/70` |
| `7` | `6` | `delta` | `0` | `9763.8` | `-59.6` | `278` | `10447` | `1951` | `70/70` |
| `8` | `5` | `delta` | `0` | `9783.0` | `-40.4` | `304` | `10576` | `2105` | `70/70` |
| `9` | `6` | `gamma` | `0` | `9823.3` | `0.0` | `281` | `10468` | `2021` | `70/70` |
| `10` | `5` | `gamma` | `0` | `9827.7` | `4.4` | `305` | `10580` | `2153` | `70/70` |
| `11` | `5` | `rice_k3` | `5` | `9875.5` | `52.1` | `281` | `10470` | `2135` | `70/70` |
| `12` | `6` | `rice_k3` | `5` | `9890.7` | `67.4` | `265` | `10390` | `2041` | `70/70` |

## Focused Controls

| Control | Runs | Min bits | Mean bits | Count <= observed |
|---|---:|---:|---:|---:|
| `digit_shuffle_preserve_book_lengths` | `20` | `39551.3` | `39559.0` | `0` |
| `book_order_shuffle` | `20` | `9663.6` | `9865.3` | `0` |

## Interpretation

The best tested copy-length model is `rice_k4` with
`min_len=5`, reaching `9596.5`
bits. That improves the previous DP gamma-length baseline by
`226.8` bits while preserving a
70/70 roundtrip. The digit-shuffle control stays far worse. As in
earlier order audits, book-order shuffles are diagnostic only unless
an external zero-cost order is supplied or permutation cost is paid.

## Boundary

This is a mechanical copy-length coding improvement. It does not alter
row0, introduce plaintext, or make an authorial-intent claim.
