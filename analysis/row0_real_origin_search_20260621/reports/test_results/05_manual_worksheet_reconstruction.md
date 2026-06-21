# manual_worksheet_reconstruction

Classification: `WEAK_CLUE`.

Algorithm: Treat row0 as a worksheet: freeze rare/surface/diagonal anchors, encode all remaining pair labels by lookup.

Description cost: 13 anchors reduce residual lookup from 160.521 to 106.343 before paying anchor costs

Holdout labels predicted: `0`.

Coverage: 13/55 anchors before residual lookup.

Bits below lookup after costs: `-11.851749041416053`.

39/93/19/91: captures 39/19 as declared anchors, not as a rule.

Controls: paid-anchor gate rejects the explicit pair+label version; rare singletons only break even.

Contradictions: A worksheet model is honest as provenance shape, but the chosen cells remain exogenous.

Evidence: `analysis/row0_origin_parallel_20260621/reports/test_results/156_row0_partial_worksheet_model.json`.
