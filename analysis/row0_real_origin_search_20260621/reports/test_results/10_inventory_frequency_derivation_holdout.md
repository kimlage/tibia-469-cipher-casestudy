# inventory_frequency_derivation_holdout

Classification: `REJECTED_CONTROL`.

Algorithm: Use fixed/frequency-driven pair placement plus symbol inventory, then test the same rule on held-out books.

Description cost: inventory/order rule only; no paid row0 formula

Holdout labels predicted: `6`.

Coverage: 6/55 holdout hits.

Bits below lookup after costs: `0.0`.

39/93/19/91: no.

Controls: holdout control p=0.6614; fixed-order random control p=0.3337.

Contradictions: Train-selected order does not generalize; fixed orders top out at 8/55 observed hits.

Evidence: `analysis/row0_origin_parallel_20260621/reports/test_results/146_row0_fill_order_inventory_search.json`.
