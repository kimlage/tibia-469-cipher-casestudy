# paid_anchor_source_model

Classification: `REJECTED_CONTROL`.

Algorithm: Freeze 13 worksheet anchors, encode residual lookup, then charge exact anchor-pair set and anchor-label arrangement.

Description cost: 54.178 nominal reduction - 40.400 pair-set cost - 25.629 label-arrangement cost

Holdout labels predicted: `0`.

Coverage: 13 anchors plus residual lookup over 55 pairs.

Bits below lookup after costs: `-11.851749041416053`.

39/93/19/91: stores 19 and 39 as anchors; does not derive why 39 is missing, 93 present, or 19/91 conflict.

Controls: nominal random-subset p=0.0014; explicit paid model not promoted.

Contradictions: Anchor labels/source are unpaid in the nominal model; explicit pair+label payment makes the full model worse than lookup.

Evidence: `analysis/row0_origin_parallel_20260621/reports/test_results/159_row0_paid_anchor_reduction_gate.json`.
