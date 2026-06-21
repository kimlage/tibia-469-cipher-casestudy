# Branch Rank Exception Cost Gate

Classification: `branch_rank_exception_cost_rejected`
Translation delta: `NONE`

## Purpose

Gate 47 prices the weak branch-rank signal from gate 46. It asks whether
`balanced_ops_literals` still reduces ad hoc description after paying for the
ranker ID, residual misses, and the clean controls it breaks.

## Summary

- Baseline residual lookup: `79.361` bits.
- Ranker ID cost: `3.807` bits across `14` rankers.
- Residual hits/misses: `6` / `4`.
- Clean false changes: `20`.
- Global correction count: `24`.
- Global ranker lower bound: `111.897` bits before labels.
- Global ranker with labels: `175.858` bits.
- Residual-gated lower bound: `70.091` bits before miss labels.
- Residual-gated with labels: `74.676` bits.
- Residual-gated net vs lookup: `-4.684` bits, audit-only because residual sites are granted.
- Best promotable net vs lookup: `96.497` bits.
- Promotes branch-rank exception cost: `False`.

## Cost Rows

| model | bits | net vs lookup | boundary |
| --- | --- | --- | --- |
| gate41_first_drift_lookup | 79.361 | 0.000 | baseline explicit residual lookup |
| global_ranker_lower_bound_without_labels | 111.897 | 32.536 | optimistic lower bound; no correction labels charged |
| global_ranker_with_labels | 175.858 | 96.497 | ranker everywhere plus clean/residual corrections |
| residual_gated_ranker_lower_bound_without_labels | 70.091 | -9.269 | not source-free; residual site lookup granted |
| residual_gated_ranker_with_labels | 74.676 | -4.684 | not source-free; residual site lookup plus miss labels |

## Decision

The weak rank signal is not promoted. Applying the ranker globally creates too
many clean rollbacks. Applying it only at residual sites is cheaper than the
plain label lookup, but only after granting the residual site lookup the
hypothesis was meant to reduce; that row is audit-only and not a parser rule.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
