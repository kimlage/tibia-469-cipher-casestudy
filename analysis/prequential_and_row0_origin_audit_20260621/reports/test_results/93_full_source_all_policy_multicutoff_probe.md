# Full Source All-Policy Multi-Cutoff Probe

Classification: `full_source_all_policy_multicutoff_stable`
Translation delta: `NONE`

## Purpose

Gate 92 tested the most disruptive `latest_source` policy on cutoffs
`50/60`. This probe adds `earliest_source` and
`prefer_previous_end_then_earliest` on the same exposed-source frontier,
reusing the validated latest-source row from gate 92.

## Policy Scoreboard

| Policy | Stable books | Roundtrip | Raw-positive | Non-earliest sources | Hidden candidates | Primary bits | Source |
|---|---:|---:|---:|---:|---:|---:|---|
| earliest_source | 10/10 | 30/30 | 30/30 | 3 | 1246561 | 1460.593924 | computed_gate93 |
| latest_source | 10/10 | 30/30 | 30/30 | 35 | 1246561 | 1460.629276 | gate92_reused |
| prefer_previous_end_then_earliest | 10/10 | 30/30 | 30/30 | 3 | 1246561 | 1460.593924 | computed_gate93 |

## Decision

- All policies roundtrip: `True`.
- All policies raw-positive: `True`.
- All policies multi-cutoff stable: `True`.
- Any non-earliest sources selected: `True`.
- All three source tie policies are compared on cutoffs 50 and 60 with every same-length source candidate exposed. This checks whether the partial multi-cutoff stability from gate 92 depends on the latest-source tie policy.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
