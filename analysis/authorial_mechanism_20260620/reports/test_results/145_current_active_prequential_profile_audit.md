# 145. Current Active Prequential Profile Audit

Classification: `current_active_components_predictive_under_tested_holdouts_recipe_fixed`
Translation delta: `NONE`

## Purpose

Audits 141, 143, and 144 tested current components separately. This audit
consolidates the active `8177.317` bit formula into one prequential
profile: copy length, copy source, literal payload, and item type are
scored on train/test splits without retuning parameters.

## Full-Corpus Accounting

- Active compression bound: `8177.317` bits
- Learned component streams: `7157.317` bits (`87.526%`)
- Fixed recipe/declaration remainder: `1020.000` bits (`12.474%`)

| Component | Stream bits | Events |
|---|---:|---:|
| `copy_length` | `1340.806` | `261` |
| `copy_source` | `2990.838` | `261` |
| `literal_payload` | `2613.661` | `857` |
| `item_type` | `212.012` | `265` |

## Prefix Future-Suffix Splits

| Split | Train books | Test books | Online gain | Frozen gain | Gap/event frozen |
|---|---:|---:|---:|---:|---:|
| `prefix_10_future_suffix` | `10` | `60` | `417.164` | `355.410` | `1.4433` |
| `prefix_20_future_suffix` | `20` | `50` | `287.954` | `246.932` | `1.5888` |
| `prefix_35_future_suffix` | `35` | `35` | `189.180` | `169.261` | `1.3471` |
| `prefix_50_future_suffix` | `50` | `20` | `111.323` | `107.308` | `1.2457` |
| `prefix_60_future_suffix` | `60` | `10` | `63.502` | `62.103` | `1.3116` |

## Holdout Summaries

- Prefix frozen gain summary: `{'n': 5, 'min': 62.10262401821575, 'median': 169.26126122375126, 'mean': 188.20271396250922, 'max': 355.40969609368494}`
- Block frozen gain summary: `{'n': 7, 'min': 50.36084501663345, 'median': 66.58052705252203, 'mean': 85.39698859763605, 'max': 160.86231176960473}`
- Family frozen gain summary: `{'n': 19, 'min': 6.269436093812175, 'median': 17.46564849467299, 'mean': 26.32771642232084, 'max': 136.50343717818464}`
- Family nonpositive failures: `[]`

## Random Same-Size Train Controls

| Cutoff | Observed prefix online gain | Random median | p(random >= observed) |
|---:|---:|---:|---:|
| `10` | `417.164` | `492.939` | `1.0000` |
| `20` | `287.954` | `441.171` | `1.0000` |
| `35` | `189.180` | `330.121` | `1.0000` |
| `50` | `111.323` | `188.226` | `1.0000` |
| `60` | `63.502` | `100.517` | `0.8500` |

## Decision

- The active learned streams beat uniform under all tested prefix, block, and public-bookcase family holdouts.
- This strengthens component-level predictive validation for the current `8177.317` bit formula.
- Random same-size train controls show the signal is not specific evidence for numeric book order.
- Recipe discovery is still not proved: literal/copy segmentation and copy-source rows are extracted from the full active recipe before splitting.
- No compression-bound, row0-origin, plaintext, or semantic claim is changed.
