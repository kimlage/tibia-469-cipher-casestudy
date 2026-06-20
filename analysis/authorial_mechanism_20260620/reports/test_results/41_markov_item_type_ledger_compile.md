# Markov Item-Type Ledger Compile

Verdict: `controlled_markov_item_type_ledger_improvement`. Translation delta: `NONE`.

This audit keeps the current item-type-coded sequential LZ recipe fixed
and retells only the literal/copy item-type ledger. The previous ledger
uses an adaptive two-symbol iid model. Candidate ledgers condition the
next item type on the previous item type, charge the declared integer
`alpha`, and charge one bit for the first item type.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8996.2` |
| Best Markov type formula bits | `8977.6` |
| Delta vs current | `-18.6` |
| Current item-type bits | `291.2` |
| Best Markov item-type bits | `272.5` |
| Item count | `365` |
| Literal items | `84` |
| Copy items | `281` |
| Best alpha | `1` |

## Best Alpha Values

| Rank | Alpha | Stream bits | Model bits | Type bits | Total bits | Delta |
|---:|---:|---:|---:|---:|---:|---:|
| `1` | `1` | `269.5` | `3` | `272.5` | `8977.6` | `-18.6` |
| `2` | `2` | `271.1` | `3` | `274.1` | `8979.2` | `-17.0` |
| `3` | `3` | `273.0` | `5` | `278.0` | `8983.1` | `-13.1` |
| `4` | `4` | `274.9` | `5` | `279.9` | `8984.9` | `-11.3` |
| `5` | `5` | `276.7` | `5` | `281.7` | `8986.7` | `-9.5` |
| `6` | `6` | `278.4` | `5` | `283.4` | `8988.4` | `-7.8` |
| `7` | `7` | `280.0` | `7` | `287.0` | `8992.0` | `-4.2` |
| `8` | `8` | `281.5` | `7` | `288.5` | `8993.6` | `-2.6` |
| `9` | `9` | `283.0` | `7` | `290.0` | `8995.0` | `-1.2` |
| `10` | `10` | `284.4` | `7` | `291.4` | `8996.4` | `0.2` |
| `11` | `11` | `285.7` | `7` | `292.7` | `8997.7` | `1.5` |
| `12` | `12` | `286.9` | `7` | `293.9` | `8999.0` | `2.8` |
| `13` | `13` | `288.2` | `7` | `295.2` | `9000.2` | `4.0` |
| `14` | `14` | `289.3` | `7` | `296.3` | `9001.4` | `5.2` |
| `15` | `15` | `290.4` | `9` | `299.4` | `9004.5` | `8.3` |
| `16` | `16` | `291.5` | `9` | `300.5` | `9005.5` | `9.3` |

## Transition Counts

| Transition | Count |
|---|---:|
| `copy->copy` | `200` |
| `copy->literal` | `80` |
| `literal->copy` | `81` |
| `literal->literal` | `3` |

## Diagnostics

RLE over the same stream has `162`
runs and is not promoted by this audit; the best tested Markov ledger
is the only cheaper decodable replacement for the current iid ledger.

## Boundary

This is a mechanical ledger/cost improvement only. It does not alter
row0, introduce plaintext, or make an authorial-intent claim.
