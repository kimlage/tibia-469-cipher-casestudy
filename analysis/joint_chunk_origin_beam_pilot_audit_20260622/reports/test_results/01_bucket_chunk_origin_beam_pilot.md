# Bucket Chunk-Origin Beam Pilot

Classification: `WEAK_JOINT_CHUNK_ORIGIN_BEAM_CLUE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test the first concrete joint chunk-origin route: replace exact-length copy-source/hint selection with a rank over prior chunks inside the granted coarse length bucket.

## Summary

- Copy ops: `208`.
- Copy digits: `9301`.
- Selected policy: `long_freq_recent`.
- Exact-length copy hint bits: `1873.768`.
- Raw source-address bits: `2550.594`.
- Bucket chunk-origin rank bits: `2649.756`.
- Delta vs exact-length copy hint: `775.988` bits.
- Delta vs raw source address: `99.162` bits.
- Saving vs uniform bucket candidates: `507.351` bits.
- Candidate count median/mean/max: `31983` / `103813.981` / `1275643`.
- Top-80 hits: `5/208`.

## Random Rank Controls

- Trials: `500`.
- Random rank bits p05/p50/p95: `2827.207` / `2858.548` / `2894.211`.
- Observed beats random p05: `True`.
- Prefix holdout cells beating random p05: `5/5`.

## Prefix Holdouts

| Cutoff | Policy | Test ops | Rank bits | Delta vs exact hint | Delta vs source | Beats random p05 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `20` | `long_freq_recent` | `155` | `2022.840` | `588.667` | `70.338` | `True` |
| `30` | `long_freq_recent` | `119` | `1570.705` | `456.331` | `46.965` | `True` |
| `40` | `freq_recent_long` | `80` | `1104.747` | `329.795` | `63.183` | `True` |
| `50` | `freq_recent_long` | `49` | `700.399` | `208.630` | `54.531` | `True` |
| `60` | `freq_recent_long` | `18` | `263.450` | `79.861` | `23.700` | `True` |

## Decision

The bucket-level chunk-origin representation contains a real ranking signal against random candidate ranks, but it is not promoted as an executable program component. Removing the exact copy-length grant adds more cost than the current exact-length copy hint/source ledger. The next blocker is a stronger target-free length/chunk prior, not another local source selector.
