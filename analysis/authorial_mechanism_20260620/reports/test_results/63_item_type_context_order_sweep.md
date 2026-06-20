# Item-Type Context Order Sweep

Verdict: `controlled_item_type_context_order_improvement`. Translation delta: `NONE`.

This audit keeps the book recipe, copy-address ledger, length ledgers,
forced literal-length rule, local repairs, and literal-payload model fixed.
It retests only the literal/copy item-type ledger.

The existing deterministic rules are retained: a literal item forces the
next in-book item to copy, and a remaining book suffix shorter than
`min_len` forces a literal. Forced emissions remain in the context history
but are not charged as coded item-type emissions.

## Model Ranking

| Rank | Order | Alpha | Stream bits | Model bits | Total bits | Delta vs active | Contexts |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `1` | `3` | `2` | `237.7` | `9` | `8803.5` | `-2.2` | `7` |
| `2` | `1` | `2` | `243.9` | `5` | `8805.7` | `0.0` | `2` |
| `3` | `2` | `2` | `241.7` | `9` | `8807.5` | `1.8` | `4` |
| `4` | `4` | `2` | `240.7` | `11` | `8808.5` | `2.8` | `12` |
| `5` | `5` | `2` | `242.6` | `11` | `8810.4` | `4.8` | `19` |
| `6` | `6` | `2` | `247.2` | `11` | `8815.0` | `9.3` | `31` |
| `7` | `7` | `2` | `248.4` | `11` | `8816.2` | `10.5` | `49` |

## Interpretation

The active formula is `8805.7` bits. The best item-type
context candidate is order `3` with `alpha=2`,
costing `8803.5` bits.

This is a mechanical ledger refinement only. It does not change row0,
introduce plaintext, or claim authorial intent.

## Promoted Formula

- [`sequential_lz_digit_address_forced_length_literal_context_order_type_context_formula_469.json`](../../sequential_lz_digit_address_forced_length_literal_context_order_type_context_formula_469.json)
