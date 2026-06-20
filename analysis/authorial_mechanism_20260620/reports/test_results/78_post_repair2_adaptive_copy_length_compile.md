# Post-Repair2 Adaptive Copy-Length Compile

Verdict: `controlled_post_repair2_adaptive_copy_length_improvement`. Translation delta: `NONE`.

This audit retests the copy-length ledger after the active post-repair2
formula. The recipe, copy-source addresses, payload model, item-type
model, forced rules, and book-length ledger are fixed. The candidate
replaces truncated binary over the legal length range with an adaptive
global model over the length index, restricted to currently legal indices.

## Best Alpha Models

| Rank | Alpha | Length bits | Model bits | Total bits | Delta vs current | Component delta |
|---:|---:|---:|---:|---:|---:|---:|
| `1` | `2` | `1639.213` | `8` | `8575.986` | `-33.787` | `-36.787` |
| `2` | `3` | `1641.339` | `10` | `8580.112` | `-29.661` | `-34.661` |
| `3` | `1` | `1646.623` | `8` | `8583.396` | `-26.377` | `-29.377` |
| `4` | `4` | `1644.905` | `10` | `8583.678` | `-26.095` | `-31.095` |
| `5` | `5` | `1648.483` | `10` | `8587.256` | `-22.517` | `-27.517` |
| `6` | `6` | `1651.755` | `10` | `8590.528` | `-19.245` | `-24.245` |
| `7` | `7` | `1654.672` | `12` | `8595.445` | `-14.328` | `-21.328` |
| `8` | `8` | `1657.257` | `12` | `8598.030` | `-11.743` | `-18.743` |
| `9` | `9` | `1659.549` | `12` | `8600.322` | `-9.451` | `-16.451` |
| `10` | `10` | `1661.588` | `12` | `8602.361` | `-7.412` | `-14.412` |
| `11` | `11` | `1663.412` | `12` | `8604.184` | `-5.588` | `-12.588` |
| `12` | `12` | `1665.049` | `12` | `8605.822` | `-3.951` | `-10.951` |

## Result

- Current formula bits: `8609.773`
- Best adaptive formula bits: `8575.986`
- Gain: `33.787` bits
- Current copy-length bits: `1676.000`
- Best adaptive copy-length bits: `1639.213`
- Best alpha: `2`
- Copy items: `283`

## Top Adaptive Savings

| Rank | Book | Op | Length | Legal symbols | Truncated bits | Adaptive bits | Delta |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `1` | `17` | `0` | `7` | `270` | `8.000` | `5.342` | `-2.658` |
| `2` | `26` | `2` | `5` | `145` | `7.000` | `4.765` | `-2.235` |
| `3` | `35` | `0` | `10` | `282` | `8.000` | `5.843` | `-2.157` |
| `4` | `11` | `1` | `7` | `127` | `7.000` | `4.853` | `-2.147` |
| `5` | `56` | `3` | `9` | `133` | `7.000` | `4.896` | `-2.104` |
| `6` | `36` | `1` | `10` | `125` | `7.000` | `4.934` | `-2.066` |
| `7` | `60` | `1` | `9` | `146` | `7.000` | `4.941` | `-2.059` |
| `8` | `23` | `5` | `7` | `78` | `6.000` | `4.052` | `-1.948` |
| `9` | `14` | `2` | `5` | `84` | `6.000` | `4.070` | `-1.930` |
| `10` | `52` | `0` | `8` | `133` | `7.000` | `5.251` | `-1.749` |
| `11` | `12` | `6` | `5` | `82` | `6.000` | `4.279` | `-1.721` |
| `12` | `32` | `0` | `11` | `133` | `7.000` | `5.309` | `-1.691` |

## Interpretation

The improvement is a copy-length coding refinement only. It is decodable
because the decoder knows prior length-index counts and the current
legal length range after the source address has been decoded. It does
not introduce plaintext, row0 meaning, or authorial intent.

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_formula_469.json)
