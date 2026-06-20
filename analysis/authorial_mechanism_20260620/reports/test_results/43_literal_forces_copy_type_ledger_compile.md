# Literal-Forces-Copy Item-Type Ledger Compile

Verdict: `controlled_literal_forces_copy_type_ledger_improvement`. Translation delta: `NONE`.

This audit keeps the current book-start item-type sequential LZ recipe
fixed and retells only the literal/copy item-type ledger. The tested
ledger charges an explicit one-bit deterministic rule: after a literal
item, if the declared book length is not yet complete, the next item type
is copy. Other item-type choices are still encoded by the adaptive
book-start Markov ledger.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8972.2` |
| Best literal-force type formula bits | `8966.7` |
| Delta vs current | `-5.5` |
| Current item-type bits | `267.2` |
| Best literal-force item-type bits | `261.7` |
| Forced literal->copy transitions | `71` |
| Rule violations | `0` |
| Best alpha | `2` |

## Best Alpha Values

| Rank | Alpha | Stream bits | Model bits | Type bits | Total bits | Delta |
|---:|---:|---:|---:|---:|---:|---:|
| `1` | `2` | `257.7` | `4` | `261.7` | `8966.7` | `-5.5` |
| `2` | `1` | `258.0` | `4` | `262.0` | `8967.1` | `-5.2` |
| `3` | `3` | `257.8` | `6` | `263.8` | `8968.9` | `-3.3` |
| `4` | `4` | `258.1` | `6` | `264.1` | `8969.2` | `-3.0` |
| `5` | `5` | `258.5` | `6` | `264.5` | `8969.6` | `-2.7` |
| `6` | `6` | `258.9` | `6` | `264.9` | `8970.0` | `-2.2` |
| `7` | `7` | `259.4` | `8` | `267.4` | `8972.4` | `0.2` |
| `8` | `8` | `259.8` | `8` | `267.8` | `8972.9` | `0.6` |
| `9` | `9` | `260.2` | `8` | `268.2` | `8973.3` | `1.0` |
| `10` | `10` | `260.7` | `8` | `268.7` | `8973.7` | `1.5` |
| `11` | `11` | `261.1` | `8` | `269.1` | `8974.1` | `1.9` |
| `12` | `12` | `261.5` | `8` | `269.5` | `8974.5` | `2.3` |
| `13` | `13` | `261.9` | `8` | `269.9` | `8974.9` | `2.7` |
| `14` | `14` | `262.3` | `8` | `270.3` | `8975.3` | `3.1` |
| `15` | `15` | `262.7` | `10` | `272.7` | `8977.7` | `5.5` |
| `16` | `16` | `263.0` | `10` | `273.0` | `8978.1` | `5.8` |

## Transition Counts

| Transition | Count |
|---|---:|
| `BOS->copy` | `56` |
| `BOS->literal` | `14` |
| `copy->copy` | `154` |
| `copy->literal` | `70` |
| `literal->copy` | `71` |

## Interpretation

The rule is decodable because book lengths are already declared: the
decoder knows when a book is complete, so it only applies the forced
literal->copy transition when another item is still needed inside the
same book. The result tightens the item-type ledger without changing
any recipe item, copy source, length, payload digit, or book order.

## Boundary

This is a mechanical ledger/cost improvement only. It does not alter
row0, introduce plaintext, or make an authorial-intent claim.
