# Copy Hint Stream Structure Gate

Classification: `copy_hint_rank_structure_not_promoted`
Translation delta: `NONE`

## Purpose

Test whether the paid copy-hint rank stream from gate 08 has simple
prequential structure. The gate codes rank buckets using prefix-trained
feature contexts and pays an in-bucket offset; it does not generate copy
choices directly.

## Summary

- Copy ops: `208`.
- Hint policy: `frequent_longest`.
- Total direct rank bits over cutoffs: `3998.858`.
- Best bucket+offset bits over cutoffs: `5162.759`.
- Total saving vs direct rank bits: `-1163.901`.
- Random shuffled-bucket saving p95: `-1048.351`.
- Beats random p95: `False`.
- Promotes hint structure: `False`.

This gate asks whether the paid copy-hint rank stream has simple prequential structure after the lower-bound grants. It models only rank buckets plus within-bucket offsets, so exact copy choice remains external unless the bucket model beats the direct rank code and shuffle controls.

## Cutoff Rows

| Cutoff | Train | Test | Best Feature | Rank Bits | Bucket+Offset Bits | Saving |
| ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `20` | `53` | `155` | `global` | `1434.174` | `1867.486` | `-433.312` |
| `30` | `89` | `119` | `target_start_bucket` | `1114.375` | `1449.674` | `-335.299` |
| `40` | `128` | `80` | `source_occurrence_bucket` | `774.952` | `990.091` | `-215.139` |
| `50` | `159` | `49` | `source_occurrence_bucket` | `491.769` | `623.336` | `-131.567` |
| `60` | `190` | `18` | `source_occurrence_bucket` | `183.590` | `232.172` | `-48.582` |

## Random Control

- Trials: `500`.
- Saving mean/p95/max: `-1083.809` / `-1048.351` / `-1013.419`.

## Decision

- This does not promote a generator or source rule.
- If promoted, it promotes only weak structure in the paid copy-hint stream.
- If not promoted, the copy hint remains an external stream after the gate-08 grants.
- Row0, plaintext, translation, and compression bound remain unchanged.
