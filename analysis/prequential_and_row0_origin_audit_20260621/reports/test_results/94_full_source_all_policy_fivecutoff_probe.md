# Full Source All-Policy Five-Cutoff Probe

Classification: `full_source_all_policy_fivecutoff_stable`
Translation delta: `NONE`

## Purpose

Gate 93 compared all source tie policies only on cutoffs `50/60`.
This probe repeats the exposed-source test across the five prequential
cutoffs `10/20/35/50/60`, without changing the parser or cost model.

## Policy Scoreboard

| Policy | Multi-cutoff stable books | Roundtrip | Raw-positive | Non-earliest sources | Hidden candidates | Primary bits | Unstable books |
|---|---:|---:|---:|---:|---:|---:|---|
| earliest_source | 50/50 | 175/175 | 175/175 | 20 | 5060831 | 11439.811840 | `[]` |
| latest_source | 50/50 | 175/175 | 175/175 | 312 | 5060831 | 11439.900221 | `[]` |
| prefer_previous_end_then_earliest | 50/50 | 175/175 | 175/175 | 20 | 5060831 | 11439.811840 | `[]` |

## Decision

- All policies roundtrip: `True`.
- All policies raw-positive: `True`.
- All policies five-cutoff stable: `True`.
- Unstable multi-cutoff books across policies: `0/150`.
- Any non-earliest sources selected: `True`.
- All three source tie policies are tested across the five prequential cutoffs with every same-length source candidate exposed. This checks whether the exposed-source parser robustness from cutoffs 50/60 survives the full cutoff grid.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
