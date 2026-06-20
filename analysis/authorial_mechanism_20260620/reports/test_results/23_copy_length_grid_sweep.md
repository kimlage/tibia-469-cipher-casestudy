# Copy Length Grid Sweep

Verdict: `copy_length_grid_retains_rice_k4_min_len_5`. Translation delta: `NONE`.

This audit broadens the previous copy-length reparse by testing
`min_len=3..12` against gamma, delta, unary, and Rice `k=0..10` length
codes. It uses the same DP encoder as the promoted Rice-length formula.

## Best Models

| Rank | min_len | Length model | Total bits | Delta vs current | Copy items | Copied digits | Literal digits | Roundtrip |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `1` | `5` | `rice_k4` | `9596.5` | `0.0` | `278` | `10455` | `808` | `70/70` |
| `2` | `4` | `rice_k4` | `9600.0` | `3.5` | `284` | `10479` | `784` | `70/70` |
| `3` | `5` | `rice_k5` | `9605.0` | `8.4` | `268` | `10403` | `860` | `70/70` |
| `4` | `3` | `rice_k4` | `9607.7` | `11.2` | `286` | `10485` | `778` | `70/70` |
| `5` | `4` | `rice_k5` | `9607.9` | `11.4` | `272` | `10419` | `844` | `70/70` |
| `6` | `3` | `rice_k5` | `9609.9` | `13.4` | `272` | `10419` | `844` | `70/70` |
| `7` | `6` | `rice_k4` | `9612.2` | `15.7` | `260` | `10362` | `901` | `70/70` |
| `8` | `6` | `rice_k5` | `9620.1` | `23.6` | `259` | `10356` | `907` | `70/70` |
| `9` | `7` | `rice_k4` | `9664.9` | `68.4` | `248` | `10294` | `969` | `70/70` |
| `10` | `7` | `rice_k5` | `9666.3` | `69.8` | `247` | `10287` | `976` | `70/70` |
| `11` | `5` | `rice_k6` | `9739.8` | `143.2` | `261` | `10365` | `898` | `70/70` |
| `12` | `4` | `rice_k6` | `9740.5` | `144.0` | `262` | `10369` | `894` | `70/70` |
| `13` | `3` | `rice_k6` | `9740.5` | `144.0` | `262` | `10369` | `894` | `70/70` |
| `14` | `6` | `rice_k6` | `9749.4` | `152.9` | `256` | `10340` | `923` | `70/70` |
| `15` | `8` | `rice_k5` | `9761.7` | `165.1` | `232` | `10186` | `1077` | `70/70` |
| `16` | `6` | `delta` | `9763.8` | `167.2` | `278` | `10447` | `816` | `70/70` |

## Interpretation

The promoted `rice_k4` / `min_len=5`
formula remains best at `9596.5` bits. The nearest
non-current model is `rice_k4` with
`min_len=4` at
`9600.0` bits,
`3.5` bits worse.
No new formula is promoted by this broader grid.

## Boundary

This is a mechanical parameter-grid audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
