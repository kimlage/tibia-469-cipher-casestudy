# Order Frontier Promotion Gate

Classification: `frontier_metric_not_formula_promotion_score`
Translation delta: `NONE`

## Purpose

Audit 22 showed that the per-book online frontier is not numeric-order
unique: several simple and random order controls also beat raw coding
after their bootstrap position. This audit checks whether that local
frontier metric can promote a non-numeric order once the complete online
formula ledger and order-description cost are applied.

## Summary

- Frontier best total-gain order: `random_04`.
- Frontier best after-bootstrap mean order: `random_04`.
- Full-formula best raw order: `numeric`.
- Full-formula best charged order: `numeric`.
- Perfect after-bootstrap frontier orders: `10/11`.
- Promotable non-numeric orders: `0`.
- `random_04` frontier total delta vs numeric: `+61.452` bits.
- `random_04` full-formula raw delta vs numeric: `+188.584` bits.
- `random_04` full-formula charged delta vs numeric: `+521.038` bits.

## Gate Table

| Order | Frontier after bootstrap | Frontier total delta | Full raw delta | Descriptor | Charged delta | Promotable |
|---|---:|---:|---:|---:|---:|---|
| `numeric` | `69/69` | `+0.000` | `+0.000` | `0.000` | `+0.000` | `False` |
| `reverse_numeric` | `69/69` | `-507.068` | `+581.827` | `1.000` | `+582.827` | `False` |
| `evens_then_odds` | `69/69` | `-92.518` | `+377.975` | `2.000` | `+379.975` | `False` |
| `odds_then_evens` | `69/69` | `-29.890` | `+263.272` | `2.000` | `+265.272` | `False` |
| `length_ascending` | `67/69` | `-445.308` | `+612.969` | `332.453` | `+945.423` | `False` |
| `random_00` | `69/69` | `-185.853` | `+315.943` | `332.453` | `+648.396` | `False` |
| `random_01` | `69/69` | `-191.288` | `+436.130` | `332.453` | `+768.583` | `False` |
| `random_02` | `69/69` | `-154.788` | `+344.432` | `332.453` | `+676.885` | `False` |
| `random_03` | `69/69` | `-168.310` | `+378.509` | `332.453` | `+710.962` | `False` |
| `random_04` | `69/69` | `+61.452` | `+188.584` | `332.453` | `+521.038` | `False` |
| `random_05` | `69/69` | `-152.747` | `+329.939` | `332.453` | `+662.392` | `False` |

## Interpretation

The order-frontier metric is a predictive diagnostic, not a promotion
score. `random_04` is the clearest example: it is better than numeric
on the book-bounded frontier total, but it is worse by `188.584` bits
under the complete online formula before order cost and by `521.038`
bits after charging its arbitrary permutation descriptor. No tested
non-numeric order can lower the compression bound under a nonnegative
descriptor.

## Boundary

- No compression bound is promoted.
- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0/table origin remains exogenous.
