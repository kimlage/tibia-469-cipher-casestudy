# Boundary Policy Stability Gate

Classification: `simple_boundary_policies_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 79 showed that the remaining unstable parser paths are primarily
copy-boundary and segmentation choices. This gate tests fixed, simple
invariant boundary policies against the observed unstable variants,
repricing each observed variant in every cutoff view where the book
appears.

## Summary

- Unstable books tested: `12`.
- Cutoff observations tested: `37`.
- Policy promoted: `False`.

## Policy Scoreboard

| Policy | Exact matches | Match rate | Total regret bits | Mean regret bits | Max regret bits |
|---|---:|---:|---:|---:|---:|
| oracle_min_average_reprice | 18/37 | 0.486 | 7.849662 | 0.212153 | 2.238461 |
| lexicographic_length_min | 16/37 | 0.432 | 8.984788 | 0.242832 | 1.110496 |
| most_source_defaults | 16/37 | 0.432 | 8.984788 | 0.242832 | 1.110496 |
| back_loaded_copy_lengths | 15/37 | 0.405 | 9.903882 | 0.267672 | 1.384835 |
| fewest_literal_digits | 16/37 | 0.432 | 11.724525 | 0.316879 | 2.777311 |
| most_copied_digits | 16/37 | 0.432 | 11.724525 | 0.316879 | 2.777311 |
| earliest_sources | 16/37 | 0.432 | 12.200128 | 0.329733 | 2.777311 |
| latest_sources | 18/37 | 0.486 | 22.398333 | 0.605360 | 3.831839 |
| front_loaded_copy_lengths | 19/37 | 0.514 | 23.636863 | 0.638834 | 3.831839 |
| lexicographic_length_max | 19/37 | 0.514 | 26.376600 | 0.712881 | 3.831839 |

## Decision

- Best structural policy: `lexicographic_length_min` with `16/37` exact matches and `8.984788` total regret bits.
- Every tested simple invariant boundary policy leaves exact path mismatches and positive regret against the per-cutoff parser winners. The observed instability is therefore not explained by a cheap global rule such as front-loading copy lengths, back-loading copy lengths, choosing earliest/latest sources, or preserving source-default choices. Boundary selection remains a structural blocker rather than a closed mechanism.
- No compression-bound change is introduced.
- No corpus-wide formula promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
