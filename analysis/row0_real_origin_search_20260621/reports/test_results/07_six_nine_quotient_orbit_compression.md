# six_nine_quotient_orbit_compression

Classification: `WEAK_CLUE`.

Algorithm: Quotient unordered pair cells by the fixed 6<->9 digit orbit and test whether orbit structure predicts labels.

Description cost: quotient/orbit clue only; full label table still needs residual lookup

Holdout labels predicted: `0`.

Coverage: 51/55 primary quotient hits.

Bits below lookup after costs: `0.0`.

39/93/19/91: partly touches 39/93 but does not explain the directed absence/conflict.

Controls: fixed-swap control p=0.0152; weak signal, not full formula.

Contradictions: Mixed non-singleton orbits remain; the quotient does not assign all labels.

Evidence: `analysis/generator_search_20260618/digit_orbit_robust_control_results.json`.
