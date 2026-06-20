# Remaining-Short-Forces-Literal Item-Type Ledger Compile

Verdict: `controlled_remaining_short_forces_literal_type_ledger_improvement`. Translation delta: `NONE`.

This audit keeps the current literal-force item-type sequential LZ recipe
fixed and retells only the literal/copy item-type ledger. It charges two
deterministic type rules: literals force the next in-book item to copy,
and a remaining book suffix shorter than `min_len` forces literal because
a copy item cannot legally fit.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8966.7` |
| Best remaining-short type formula bits | `8953.9` |
| Delta vs current | `-12.8` |
| Current item-type bits | `261.7` |
| Best remaining-short item-type bits | `248.9` |
| Literal->copy forced transitions | `71` |
| Remaining<min_len forced literals | `8` |
| Rule violations | `0` |
| Best alpha | `2` |

## Best Alpha Values

| Rank | Alpha | Stream bits | Model bits | Type bits | Total bits | Delta |
|---:|---:|---:|---:|---:|---:|---:|
| `1` | `2` | `243.9` | `5` | `248.9` | `8953.9` | `-12.8` |
| `2` | `1` | `244.1` | `5` | `249.1` | `8954.2` | `-12.6` |
| `3` | `3` | `244.1` | `7` | `251.1` | `8956.1` | `-10.6` |
| `4` | `4` | `244.5` | `7` | `251.5` | `8956.5` | `-10.2` |
| `5` | `5` | `244.9` | `7` | `251.9` | `8957.0` | `-9.8` |
| `6` | `6` | `245.4` | `7` | `252.4` | `8957.4` | `-9.3` |
| `7` | `7` | `245.9` | `9` | `254.9` | `8959.9` | `-6.8` |
| `8` | `8` | `246.4` | `9` | `255.4` | `8960.4` | `-6.3` |
| `9` | `9` | `246.8` | `9` | `255.8` | `8960.9` | `-5.8` |
| `10` | `10` | `247.3` | `9` | `256.3` | `8961.4` | `-5.4` |
| `11` | `11` | `247.8` | `9` | `256.8` | `8961.9` | `-4.9` |
| `12` | `12` | `248.3` | `9` | `257.3` | `8962.3` | `-4.4` |
| `13` | `13` | `248.7` | `9` | `257.7` | `8962.8` | `-4.0` |
| `14` | `14` | `249.2` | `9` | `258.2` | `8963.2` | `-3.5` |
| `15` | `15` | `249.6` | `11` | `260.6` | `8965.6` | `-1.1` |
| `16` | `16` | `250.0` | `11` | `261.0` | `8966.1` | `-0.7` |

## Transition Counts

| Transition | Count |
|---|---:|
| `BOS->copy` | `56` |
| `BOS->literal` | `14` |
| `copy->copy` | `154` |
| `copy->literal` | `62` |
| `literal->copy` | `71` |
| `remaining_lt_min->literal` | `8` |

## Interpretation

The second rule is decodable because each book length and `min_len` are
already declared. If fewer than `min_len` digits remain in the current
book, a copy item cannot be legal, so the item type is forced to
literal. This tightens the item-type ledger without changing any
recipe item, copy source, length, payload digit, or book order.

## Boundary

This is a mechanical ledger/cost improvement only. It does not alter
row0, introduce plaintext, or make an authorial-intent claim.
