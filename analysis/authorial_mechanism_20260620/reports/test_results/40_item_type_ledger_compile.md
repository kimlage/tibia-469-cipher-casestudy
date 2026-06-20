# Item-Type Ledger Compile

Verdict: `controlled_item_type_ledger_improvement`. Translation delta: `NONE`.

This audit keeps the current repaired sequential LZ recipe fixed and
retells only the literal/copy item-type ledger. The active formula
charges one type bit per item. Candidate ledgers encode the same item
stream with a two-symbol adaptive Dirichlet model and charge the
declared integer `alpha`.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `9070.1` |
| Best type-coded formula bits | `8996.2` |
| Delta vs current | `-73.8` |
| Current item-type bits | `365.0` |
| Best item-type bits | `291.2` |
| Literal runs | `84` |
| Copy items | `281` |
| Best alpha | `2` |

## Best Alpha Values

| Rank | Alpha | Stream bits | Model bits | Type bits | Total bits | Delta |
|---:|---:|---:|---:|---:|---:|---:|
| `1` | `2` | `288.2` | `3` | `291.2` | `8996.2` | `-73.8` |
| `2` | `1` | `288.2` | `3` | `291.2` | `8996.3` | `-73.8` |
| `3` | `3` | `288.3` | `5` | `293.3` | `8998.4` | `-71.7` |
| `4` | `4` | `288.6` | `5` | `293.6` | `8998.6` | `-71.4` |
| `5` | `5` | `288.9` | `5` | `293.9` | `8998.9` | `-71.1` |
| `6` | `6` | `289.2` | `5` | `294.2` | `8999.3` | `-70.8` |
| `7` | `7` | `289.6` | `7` | `296.6` | `9001.6` | `-68.4` |
| `8` | `8` | `289.9` | `7` | `296.9` | `9002.0` | `-68.1` |
| `9` | `9` | `290.3` | `7` | `297.3` | `9002.3` | `-67.7` |
| `10` | `10` | `290.7` | `7` | `297.7` | `9002.7` | `-67.3` |
| `11` | `11` | `291.0` | `7` | `298.0` | `9003.1` | `-67.0` |
| `12` | `12` | `291.4` | `7` | `298.4` | `9003.5` | `-66.6` |
| `13` | `13` | `291.8` | `7` | `298.8` | `9003.8` | `-66.2` |
| `14` | `14` | `292.1` | `7` | `299.1` | `9004.2` | `-65.9` |
| `15` | `15` | `292.5` | `9` | `301.5` | `9006.6` | `-63.5` |
| `16` | `16` | `292.9` | `9` | `301.9` | `9006.9` | `-63.1` |

## Interpretation

The item stream is strongly imbalanced toward copies. Charging a fixed
one-bit tag per item is decodable but not the tightest ledger for the
already-fixed recipe. The adaptive two-symbol ledger is also decodable
because the decoder reads item types sequentially until each declared
book length is exhausted.

## Boundary

This is a mechanical ledger/cost improvement only. It does not alter
row0, introduce plaintext, or make an authorial-intent claim.
