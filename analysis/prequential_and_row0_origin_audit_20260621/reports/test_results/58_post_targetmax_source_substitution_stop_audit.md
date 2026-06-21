# Post-Target-Max Source Substitution Stop Audit

Classification: `post_targetmax_source_substitution_micro_frontier_stop_mainline`
Translation delta: `NONE`

## Purpose

Gates 56 and 57 found only microscopic post-target-max same-chunk
source-substitution gains. This audit applies an explicit stop rule
and does not run a third post-target-max source-substitution pass.

## Pass Ledger

| Gate | Active bits | Candidate bits | Gain bits | Positive singles | Positive pairs | Pair candidates | Selector floor bits |
|---|---:|---:|---:|---:|---:|---:|---:|
| `post_targetmax_source_frontier` | `8156.050355` | `8156.050167` | `+0.000188` | `1` | `152` | `71321` | `16.122` |
| `post_targetmax_source_second_pass` | `8156.050167` | `8156.049986` | `+0.000181` | `1` | `151` | `71321` | `16.122` |

## Stop Rule

- Pass gains: `[0.0001877897875601775, 0.00018086818090523593]`.
- Cumulative gain: `0.000369` bits.
- Last pass positive-pair fraction: `0.002117`.
- Last pass pair candidates per gained bit: `394325854.570`.
- Minimum pair-selector floor for the last pass: `16.122` bits.
- Selector floor minus last gain: `16.122` bits.
- Total selector floor minus cumulative gain: `32.244` bits.
- Stop rule booleans: `{'all_post_targetmax_source_passes_below_0_001_bits': True, 'cumulative_post_targetmax_gain_below_0_0005_bits': True, 'positive_pair_counts_nonincreasing': True, 'positive_single_counts_nonincreasing': True, 'same_pair_search_size_each_pass': True, 'last_gain_smaller_than_pair_selector_floor': True, 'cumulative_gain_smaller_than_selector_floor_total': True}`.

## Decision

- Current compression bound remains `8156.049986` bits.
- Do not treat further unpriced same-chunk source substitutions as a mainline generation search.
- Future progress should require structural source/length derivation, holdout-predictive parser improvement, or row0-origin evidence.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- Segmentation and copy lengths remain fixed in all source-substitution passes considered.
- This audit does not emit a new formula.
