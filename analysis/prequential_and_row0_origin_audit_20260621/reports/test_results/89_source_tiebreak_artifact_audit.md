# Source Tie-Break Artifact Audit

Classification: `source_canonicality_tiebreak_not_resolved`
Translation delta: `NONE`

## Purpose

Gate 88 found that every projected copy source is the earliest target
match. This audit tests whether that is mechanical evidence or a parser
tie-break artifact by rerunning the stable no-item/no-literal-length
projection with alternate source tie policies under the same primary cost.

## Policy Scoreboard

| Policy | Stable books | Unstable books | Primary bits | Source sum | Source defaults | Copy items |
|---|---:|---:|---:|---:|---:|---:|
| earliest_source | 50/50 | 0/50 | 11459.765681 | 1218370 | 18 | 525 |
| latest_source | 50/50 | 0/50 | 11459.765681 | 1218370 | 18 | 525 |
| prefer_previous_end_then_earliest | 50/50 | 0/50 | 11459.765681 | 1218370 | 18 | 525 |

## Decision

- Same primary cost across policies: `True`.
- All policies stable at 50/50: `True`.
- Source-sum span across policies: `0`.
- Earliest-source signal treated as artifact: `False`.
- If alternate source tie policies keep the same primary parser cost and 50/50 path stability while changing selected sources, then the 208/208 earliest-target-match observation is a parser tie-break artifact, not an independent source-origin rule.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
