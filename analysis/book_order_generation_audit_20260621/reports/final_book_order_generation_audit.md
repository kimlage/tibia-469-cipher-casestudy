# Final Book Order Generation Audit

Status: `analysis_only`
Classification: `BOOK_ORDER_CANONICAL_RETAINED_NOT_GENERATED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Is numeric book order a generated mechanical rule, a compact canonical
order retained by the formula, or replaceable by a searched non-numeric
order?

## Consolidated Evidence

- Prefix-trained components beat uniform in `5` cutoffs.
- Numeric prefixes are order-specific in `0` online/frozen cutoffs at p<=0.05.
- Numeric online frontier has `69/69` after-bootstrap raw wins.
- The same frontier criterion is not unique: `10` tested orders and `6` random orders are also perfect after bootstrap.
- The frontier best order is `random_04` at `+61.452` bits versus numeric on that local metric.
- Under the full formula, best raw and charged order are both `numeric`.
- Promotable non-numeric orders: `0`.
- `random_04` is `+521.038` bits worse than numeric after full-formula and descriptor costs.
- Online reparse random raw/charged orders <= numeric: `0` / `0`.

## Decision

- Numeric order remains the compact canonical order used by the formula.
- Numeric order is not promoted as a generated mechanical rule.
- Arbitrary searched non-numeric order is not promoted.
- Order-dependent parser evidence remains predictive/diagnostic, not authorial-origin evidence.
- This does not change the compression bound.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Book order dependency gate](test_results/01_book_order_dependency_gate.md)
- [Prequential order control audit](../../authorial_mechanism_20260620/reports/test_results/120_prequential_order_control_audit.md)
- [Online order frontier controls](../../prequential_and_row0_origin_audit_20260621/reports/test_results/22_online_order_frontier_controls.md)
- [Order frontier promotion gate](../../prequential_and_row0_origin_audit_20260621/reports/test_results/23_order_frontier_promotion_gate.md)
- [Online reparse order control audit](../../authorial_mechanism_20260620/reports/test_results/130_online_reparse_order_control_audit.md)
