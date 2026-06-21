# Full Source Exposure Audit

Classification: `full_source_exposure_preserves_stability_with_non_earliest_sources`
Translation delta: `NONE`

## Purpose

Gate 90 showed that `precompute_matches` collapses source candidates to
the earliest source per length. This audit reruns the cutoff-60 stable
projection while exposing every same-length source candidate, then
compares the result with the collapsed gate 89 frontier.

## Policy Scoreboard

| Policy | Stable books | Primary bits | Non-earliest sources | Hidden candidates | Delta bits vs collapsed | Delta source sum |
|---|---:|---:|---:|---:|---:|---:|
| earliest_source | 10/10 | 360.312088 | 0 | 406244 | +0.000000 | +0 |
| latest_source | 10/10 | 360.329764 | 10 | 406244 | +0.017676 | +38948 |
| prefer_previous_end_then_earliest | 10/10 | 360.312088 | 0 | 406244 | +0.000000 | +0 |

## Decision

- All policies roundtrip: `True`.
- All policies stable on tested cutoffs: `True`.
- Any non-earliest sources selected: `True`.
- Tested cutoffs: `[60]`.
- This audit exposes every same-length source candidate suppressed by precompute_matches. It tests whether the stable parser frontier survives without the earliest-only candidate collapse.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
