# Multi-Cutoff Source Choice Optimizer Gate

Classification: `multicutoff_source_choice_optimizer_no_change_boundary`
Translation delta: `NONE`

## Purpose

Gate 38 only repriced the deterministic reparse sources under the
`previous_copy_end` source ledger. This gate makes the first source-aware
recipe edit: for each fixed copy segment, it greedily chooses the cheapest
legal source position that reproduces the same chunk. Segmentation and copy
lengths remain fixed.

## Summary

- All cutoffs roundtrip: `True`.
- All books beat raw digit coding: `True`.
- Aggregate beats source-state repricing at cutoffs: `0/5`.
- Aggregate beats uniform-address reparse at cutoffs: `5/5`.
- Total optimized bits: `12016.569`.
- Total source-state reprice bits: `12016.569`.
- Total uniform-address reparse bits: `12129.537`.
- Total optimized minus reprice bits: `+0.000`.
- Total optimized minus uniform-address bits: `-112.968`.
- Changed sources: `0/514`.
- Defaults/exceptions: `15` / `499`.

## Cutoff Rows

| Cutoff | Books | Roundtrip | Raw wins | Reprice wins | Uniform wins | Optimized bits | Reprice bits | Delta vs reprice | Delta vs uniform | Changed sources | Defaults | Exceptions |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `10` | `60` | `60` | `60` | `0` | `12` | `4881.058` | `4881.058` | `+0.000` | `-33.067` | `0` | `5` | `200` |
| `20` | `50` | `50` | `50` | `0` | `10` | `3448.112` | `3448.112` | `+0.000` | `-28.591` | `0` | `4` | `147` |
| `35` | `35` | `35` | `35` | `0` | `12` | `2183.611` | `2183.611` | `+0.000` | `-31.668` | `0` | `4` | `88` |
| `50` | `20` | `20` | `20` | `0` | `5` | `1135.608` | `1135.608` | `+0.000` | `-9.402` | `0` | `1` | `47` |
| `60` | `10` | `10` | `10` | `0` | `4` | `368.180` | `368.180` | `+0.000` | `-10.241` | `0` | `1` | `17` |

## Interpretation

The fixed-segmentation source-choice hypothesis closes negative:
the greedy optimizer finds no cheaper alternate source positions for
the deterministic reparse copies. The original reparse sources are
already locally optimal under this immediate `previous_copy_end` cost.

This is still useful progress because it falsifies a simple source-only
recipe-improvement path. Future active-parser work must change
segmentation, copy lengths, or use a non-greedy/global source-state
objective.

## Boundary

- No compression-bound change is introduced.
- No complete active parser or global recipe-discovery promotion is introduced.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
