# Source Substitution Saturation Audit

Classification: `local_source_substitution_frontier_saturated_stop_mainline`
Translation delta: `NONE`

## Purpose

This audit stops treating repeated same-chunk source substitutions as a
mainline generation search. It reads gates 41-45 and applies an explicit
stop rule to the local fixed-recipe source frontier. No fifth pass is run.

## Pass Ledger

| Gate | Active bits | Candidate bits | Gain bits | Positive singles | Positive pairs | Pair candidates | Selector floor bits |
|---|---:|---:|---:|---:|---:|---:|---:|
| `source_path_formula` | `8177.316653` | `8162.412054` | `+14.904599` | `` | `` | `` |  |
| `source_substitution_frontier` | `8162.412054` | `8160.827092` | `+1.584963` | `12` | `2686` | `69849` | `16.092` |
| `source_substitution_second_pass` | `8160.827092` | `8160.826421` | `+0.000671` | `10` | `2091` | `69849` | `16.092` |
| `source_substitution_third_pass` | `8160.826421` | `8160.825917` | `+0.000503` | `7` | `1371` | `69849` | `16.092` |
| `source_substitution_fourth_pass` | `8160.825917` | `8160.825608` | `+0.000310` | `3` | `509` | `69849` | `16.092` |

## Stop Rule

- Last three pass gains: `[0.0006711103651468875, 0.000503472318087006, 0.0003095543997915229]`.
- Last three cumulative gain: `0.001484` bits.
- Last pass positive-pair fraction: `0.007287`.
- Last pass pair candidates per gained bit: `225643699.612`.
- Minimum pair-selector floor for the last pass: `16.092` bits.
- Selector floor minus last gain: `16.092` bits.
- Tail selector floor minus tail gain: `48.274` bits.
- Stop rule booleans: `{'last_three_passes_all_below_0_001_bits': True, 'last_three_cumulative_gain_below_0_002_bits': True, 'positive_pair_counts_strictly_decrease': True, 'positive_single_counts_strictly_decrease_after_second_pass': True, 'same_pair_search_size_each_pass': True, 'last_gain_smaller_than_minimum_pair_selector_floor': True, 'tail_gain_smaller_than_minimum_tail_selector_floor': True}`.

## Decision

- Current local-source compression bound: `8160.825608` bits.
- The local same-chunk single/pair source frontier is saturated as a mainline path.
- This is a falsification of continued unpriced local-source micro-sweeps as generation evidence, not a new formula claim.
- Future progress should require structural source/length derivation, holdout-predictive parser improvement, or row0-origin evidence.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- Segmentation and copy lengths remain fixed in all source-substitution passes considered.
- This audit does not search a fifth pass or emit a new formula.
