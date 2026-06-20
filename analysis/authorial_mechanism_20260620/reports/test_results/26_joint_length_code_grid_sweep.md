# Joint Length Code Grid Sweep

Verdict: `joint_length_grid_retains_rice_k4_literal_rice_k3_min_len_5`. Translation delta: `NONE`.

This audit tests the interaction between copy-length and literal-run
length codes under the same sequential LZ dynamic parse. It covers
`min_len=3..7`, gamma/delta, and Rice `k=0..8` for both length
families while keeping numeric book order and absolute source
addresses fixed.

## Best Joint Models

| Rank | min_len | Copy length | Literal length | Model bits | Total bits | Delta vs current | Copy items | Literal runs | Literal digits | Roundtrip |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| `1` | `5` | `rice_k4` | `rice_k3` | `10` | `9545.5` | `0.0` | `279` | `83` | `794` | `70/70` |
| `2` | `5` | `rice_k4` | `rice_k2` | `8` | `9552.2` | `6.7` | `286` | `90` | `756` | `70/70` |
| `3` | `4` | `rice_k4` | `rice_k3` | `10` | `9554.6` | `9.1` | `284` | `78` | `775` | `70/70` |
| `4` | `6` | `rice_k4` | `rice_k3` | `10` | `9558.5` | `13.0` | `268` | `85` | `849` | `70/70` |
| `5` | `5` | `rice_k5` | `rice_k3` | `10` | `9559.7` | `14.2` | `275` | `81` | `815` | `70/70` |
| `6` | `4` | `rice_k4` | `rice_k2` | `8` | `9562.2` | `16.7` | `290` | `86` | `740` | `70/70` |
| `7` | `3` | `rice_k4` | `rice_k3` | `10` | `9563.6` | `18.0` | `284` | `78` | `775` | `70/70` |
| `8` | `4` | `rice_k5` | `rice_k3` | `10` | `9565.5` | `19.9` | `276` | `80` | `811` | `70/70` |
| `9` | `3` | `rice_k5` | `rice_k3` | `10` | `9567.5` | `21.9` | `276` | `80` | `811` | `70/70` |
| `10` | `6` | `rice_k4` | `rice_k2` | `8` | `9570.4` | `24.9` | `272` | `89` | `825` | `70/70` |
| `11` | `3` | `rice_k4` | `rice_k2` | `8` | `9571.2` | `25.6` | `290` | `86` | `740` | `70/70` |
| `12` | `5` | `rice_k5` | `rice_k2` | `8` | `9571.4` | `25.9` | `279` | `86` | `791` | `70/70` |
| `13` | `6` | `rice_k5` | `rice_k3` | `10` | `9573.4` | `27.9` | `265` | `83` | `866` | `70/70` |
| `14` | `4` | `rice_k5` | `rice_k2` | `8` | `9577.2` | `31.6` | `280` | `85` | `787` | `70/70` |
| `15` | `3` | `rice_k5` | `rice_k2` | `8` | `9579.2` | `33.6` | `280` | `85` | `787` | `70/70` |
| `16` | `5` | `rice_k4` | `rice_k4` | `10` | `9582.2` | `36.6` | `275` | `76` | `822` | `70/70` |
| `17` | `4` | `rice_k4` | `rice_k4` | `10` | `9585.6` | `40.1` | `281` | `70` | `798` | `70/70` |
| `18` | `6` | `rice_k5` | `rice_k2` | `8` | `9589.1` | `43.5` | `269` | `87` | `842` | `70/70` |
| `19` | `5` | `rice_k5` | `rice_k4` | `10` | `9590.9` | `45.4` | `271` | `77` | `839` | `70/70` |
| `20` | `3` | `rice_k4` | `rice_k4` | `10` | `9593.4` | `47.8` | `283` | `68` | `792` | `70/70` |

## Interpretation

The current formula uses `rice_k4` copy lengths,
`rice_k3` literal-run lengths, and
`min_len=5` at `9545.5` bits.
The best joint-grid model is `rice_k4` /
`rice_k3` with `min_len=5`
at `9545.5` bits, delta
`0.0`.

## Boundary

This is a mechanical length-code interaction audit only. It does not
alter row0, introduce plaintext, or make an authorial-intent claim.
