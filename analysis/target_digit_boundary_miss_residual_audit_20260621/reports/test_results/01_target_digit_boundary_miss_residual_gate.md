# Target Digit Boundary Miss Residual Gate

Classification: `target_digit_boundary_miss_residual_weak_not_promoted`
Translation delta: `NONE`

## Purpose

Test whether the `107` cutpoints missed by the promoted `right_ge:4`
boundary threshold have a second-stage source-free candidate structure.

## Summary

- Books/candidates/actual cutpoints: `60` / `9507` / `201`.
- Primary policy: `right_ge:4`.
- Residual policies tested: `93`.
- Best residual policy: `near_primary:1`.
- Threshold gate saving after policy charge: `645.694` bits.
- Residual saving after primary+residual policy charge: `715.155` bits.
- Delta vs threshold: `69.462` bits.
- Random residual delta p95: `49.103` bits.
- Primary inside TP/FP: `94` / `841`.
- Outside actual cutpoints: `107`.
- Residual selected/TP/FP/FN: `1452` / `38` / `1414` / `69`.
- Residual precision/recall: `0.026171` / `0.355140`.
- Exact outside books: `0/60`.
- Prefix-selected positive delta cells: `4/5`.

The best rule is still broad: it selects many residual candidates and does
not generate exact endpoints. Full-fit evidence is positive, but the
prefix-selected validation fails one cell, so this is not promoted.

## Top Residual Policies

| Policy | Delta vs threshold | Residual TP | Residual FP | Residual FN | Selected |
| --- | ---: | ---: | ---: | ---: | ---: |
| `near_primary:1` | `69.462` | `38` | `1414` | `69` | `1452` |
| `outside_right_ge:2` | `68.862` | `59` | `3058` | `48` | `3117` |
| `position_bucket:0_of_5` | `64.228` | `30` | `1653` | `77` | `1683` |
| `near_primary:2` | `60.578` | `51` | `2504` | `56` | `2555` |
| `position_mod:2_1` | `60.508` | `58` | `4237` | `49` | `4295` |
| `position_mod:2_0` | `60.508` | `49` | `4228` | `58` | `4277` |
| `position_mod:3_0` | `59.745` | `40` | `2791` | `67` | `2831` |
| `outside_rank_band:0.1_0.3` | `58.867` | `37` | `1705` | `70` | `1742` |

## Decision

- Promotes dependency reduction: `False`.
- Endpoint generator promoted: `False`.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
