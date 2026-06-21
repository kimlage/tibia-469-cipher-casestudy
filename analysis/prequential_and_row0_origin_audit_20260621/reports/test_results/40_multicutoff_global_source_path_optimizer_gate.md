# Multi-Cutoff Global Source Path Optimizer Gate

Classification: `global_source_path_optimizer_improves_fixed_segmentation_unpromoted`
Translation delta: `NONE`

## Purpose

Gate 39 showed that greedy local source substitution changes no sources.
This gate tests the next stronger fixed-segmentation hypothesis: an exact
dynamic program over copy-source choices, where a locally expensive source
may be chosen if its `previous_copy_end` state makes later sources cheaper.
Segmentation and copy lengths remain fixed.

## Summary

- All cutoffs roundtrip: `True`.
- All books beat raw digit coding: `True`.
- Aggregate beats repricing at cutoffs: `5/5`.
- Total optimized bits: `11974.209`.
- Total repriced bits: `12016.569`.
- Total optimized minus repriced bits: `-42.359`.
- Total optimized minus uniform-address bits: `-155.328`.
- Changed sources: `10/514`.
- Defaults/exceptions: `21` / `493`.
- Max DP state count: `14`.
- Total DP transitions: `4215`.

## Cutoff Rows

| Cutoff | Books | Copy events | Candidates | Changed | States max | Optimized bits | Reprice bits | Delta vs reprice | Delta vs uniform | Defaults | Exceptions |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `10` | `60` | `205` | `581` | `3` | `14` | `4868.940` | `4881.058` | `-12.118` | `-45.185` | `7` | `198` |
| `20` | `50` | `151` | `443` | `3` | `14` | `3440.546` | `3448.112` | `-7.567` | `-36.157` | `5` | `146` |
| `35` | `35` | `92` | `275` | `2` | `13` | `2176.660` | `2183.611` | `-6.951` | `-38.619` | `5` | `87` |
| `50` | `20` | `48` | `128` | `1` | `11` | `1127.652` | `1135.608` | `-7.956` | `-17.358` | `2` | `46` |
| `60` | `10` | `18` | `45` | `1` | `5` | `360.412` | `368.180` | `-7.768` | `-18.008` | `2` | `16` |

## Interpretation

This is the first global source-path test under `previous_copy_end`.
It determines whether fixed deterministic copy events can be improved
by choosing sources for future state value rather than immediate cost.

It remains a partial parser: copy/literal segmentation and copy lengths
are fixed from deterministic reparse, and no compression bound is
promoted.

## Boundary

- No compression-bound change is introduced.
- No complete active parser or global recipe-discovery promotion is introduced.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
