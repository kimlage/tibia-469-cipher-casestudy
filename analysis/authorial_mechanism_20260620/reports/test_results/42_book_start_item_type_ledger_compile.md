# Book-Start Item-Type Ledger Compile

Verdict: `controlled_book_start_item_type_ledger_improvement`. Translation delta: `NONE`.

This audit keeps the current Markov item-type sequential LZ recipe fixed
and retells only the literal/copy item-type ledger. The current ledger
conditions on the previous item globally. The tested ledger uses a
`BOS` context at each declared book start, then conditions on the
previous item type inside the book.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8977.6` |
| Best book-start type formula bits | `8972.2` |
| Delta vs current | `-5.3` |
| Current item-type bits | `272.5` |
| Best book-start item-type bits | `267.2` |
| Books | `70` |
| Item count | `365` |
| Book starts with literal | `14` |
| Book starts with copy | `56` |
| Best alpha | `1` |

## Best Alpha Values

| Rank | Alpha | Stream bits | Model bits | Type bits | Total bits | Delta |
|---:|---:|---:|---:|---:|---:|---:|
| `1` | `1` | `264.2` | `3` | `267.2` | `8972.2` | `-5.3` |
| `2` | `2` | `267.5` | `3` | `270.5` | `8975.6` | `-2.0` |
| `3` | `3` | `270.6` | `5` | `275.6` | `8980.7` | `3.1` |
| `4` | `4` | `273.5` | `5` | `278.5` | `8983.5` | `6.0` |
| `5` | `5` | `276.1` | `5` | `281.1` | `8986.1` | `8.6` |
| `6` | `6` | `278.5` | `5` | `283.5` | `8988.5` | `11.0` |
| `7` | `7` | `280.7` | `7` | `287.7` | `8992.8` | `15.2` |
| `8` | `8` | `282.8` | `7` | `289.8` | `8994.8` | `17.3` |
| `9` | `9` | `284.7` | `7` | `291.7` | `8996.8` | `19.2` |
| `10` | `10` | `286.5` | `7` | `293.5` | `8998.6` | `21.0` |
| `11` | `11` | `288.3` | `7` | `295.3` | `9000.3` | `22.7` |
| `12` | `12` | `289.9` | `7` | `296.9` | `9001.9` | `24.4` |
| `13` | `13` | `291.4` | `7` | `298.4` | `9003.5` | `25.9` |
| `14` | `14` | `292.9` | `7` | `299.9` | `9004.9` | `27.4` |
| `15` | `15` | `294.3` | `9` | `303.3` | `9008.3` | `30.7` |
| `16` | `16` | `295.6` | `9` | `304.6` | `9009.6` | `32.1` |

## Transition Counts

| Transition | Count |
|---|---:|
| `BOS->copy` | `56` |
| `BOS->literal` | `14` |
| `copy->copy` | `154` |
| `copy->literal` | `70` |
| `literal->copy` | `71` |

## Diagnostics

The gain comes from using already-declared book boundaries as item-type
context. It does not add a new order, source, or plaintext channel.
Higher-order book-start diagnostics are recorded in JSON but not
promoted unless they beat this ledger under the same declaration cost.

## Boundary

This is a mechanical ledger/cost improvement only. It does not alter
row0, introduce plaintext, or make an authorial-intent claim.
