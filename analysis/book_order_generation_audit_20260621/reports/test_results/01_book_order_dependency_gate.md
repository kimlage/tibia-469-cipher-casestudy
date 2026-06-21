# Book Order Dependency Gate

Classification: `book_order_dependency_retained`
Translation delta: `NONE`

## Purpose

Consolidate the existing order controls against the current generation
boundary: is numeric book order a generated mechanism, merely the
canonical compact order, or replaceable by an arbitrary order?

## Summary

- Prequential prefix online beats uniform cutoffs: `5`.
- Prequential numeric-order-specific cutoffs at p<=0.05: `0` online / `0` frozen.
- Numeric online frontier raw wins after bootstrap: `69/69`.
- Orders with perfect after-bootstrap frontier: `10`.
- Random orders with perfect after-bootstrap frontier: `6`.
- Frontier best total-gain order: `random_04` (`+61.452` bits vs numeric).
- Full-formula best raw/charged order: `numeric` / `numeric`.
- Promotable non-numeric orders: `0`.
- `random_04` full-formula charged delta vs numeric: `+521.038` bits.
- Online reparse random raw/charged <= numeric: `0` / `0`.

## Evidence Matrix

| Gate | Classification | Supports | Limits |
| --- | --- | --- | --- |
| `prequential_order_control` | `prequential_predictive_not_numeric_order_specific` | learned components beat uniform | numeric prefixes are not unusually strong against random same-size train sets |
| `online_frontier_controls` | `online_frontier_predictive_but_not_numeric_order_unique` | numeric online frontier is predictive after bootstrap | 10/11 tested orders and 6/6 random orders also have perfect after-bootstrap raw wins |
| `order_frontier_promotion` | `frontier_metric_not_formula_promotion_score` | frontier metric is not a promotion score | no tested non-numeric order promotes after full formula and descriptor costs |
| `online_reparse_order_control` | `numeric_online_reparse_survives_order_controls` | numeric order survives named/random full reparse controls | survival of canonical numeric order is not a derivation of that order |

## Decision

- Numeric order promoted as generator: `False`.
- Arbitrary order promoted: `False`.
- Numeric order remains the compact canonical order used by the formula, and arbitrary non-numeric orders are not promoted. But the predictive controls do not prove that numeric order is an authorial or mechanically generated order.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
