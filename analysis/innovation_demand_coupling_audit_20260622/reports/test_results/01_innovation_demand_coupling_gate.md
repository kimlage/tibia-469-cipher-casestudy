# Innovation Demand Coupling Gate

Classification: `innovation_demand_within_segment_weak_clue_not_program`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This gate tests whether innovation replay events are synchronized to the downstream consumer segments that use the innovation tape as seed payload and literal payload.

| Metric | Value |
| --- | ---: |
| Stream digits | `1962` |
| Innovation events | `62` |
| Consumer segments | `63` |
| Event-boundary demand hits | `4/61` |
| Events within one consumer segment | `54/62` |
| Demand-boundary saving bits | `-2.366` |
| Weak within-segment clue | `True` |
| Boundary program promoted | `False` |

## Controls

| Control | Value |
| --- | ---: |
| Random boundary hit p95 | `4` |
| Random boundary hit mean | `1.921` |
| Permuted event-length hit p95 | `5` |
| Permuted event-length hit mean | `2.032` |
| Permuted event-length within p95 | `52` |
| Permuted event-length within mean | `46.297` |
| Shuffled consumer-segment hit p95 | `5` |

## Decision

`consumer-demand boundaries do not explain replay event boundaries after paid boundary coding and controls; within-segment containment is only a weak clue`

Next blocker: `innovation replay policy remains external; demand surface is not sufficient as the missing causal state`

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
