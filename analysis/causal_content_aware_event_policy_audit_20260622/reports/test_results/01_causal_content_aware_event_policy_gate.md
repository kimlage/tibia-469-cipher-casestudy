# Causal Content-Aware Event Policy Gate

Classification: `causal_content_aware_event_policy_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This gate ranks literal/copy event candidates using only emitted content, literal tape position, and copy-lineage features.

| Cutoff | Policy | Events | Saving Bits | Top1 | Top5 | Top20 | Beam Exact | Max Survives |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | `literal_long_then_copy` | 42 | 166.897 | 1 | 1 | 2 | 0 | 0 |
| 35 | `literal_long_then_copy` | 27 | 114.844 | 1 | 1 | 2 | 0 | 0 |
| 50 | `literal_long_then_copy` | 12 | 71.901 | 1 | 1 | 2 | 0 | 0 |

## Totals

- Total saving bits vs raw candidate choice: `353.641`.
- Positive splits: `3/3`.
- Exact suffix beam splits: `0/3`.
- Top-20 true event hits: `6`.

## Decision

`content-aware ranking does not produce a complete event decoder; true suffixes do not survive finite beams`

No v9 reduction is integrated in this run.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
