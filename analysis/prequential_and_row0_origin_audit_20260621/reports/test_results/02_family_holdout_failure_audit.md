# Family Holdout Failure Audit

Classification: `family_holdout_failures_are_component_and_sample_specific`
Translation delta: `NONE`

## Purpose

This audit explains the public-bookcase family failures from the
prequential/row0 origin audit. It does not search for a lower bit count,
derive `row0`, or test plaintext. It decomposes each family split into
copy-length, literal-payload, and item-type gains against uniform.

## Summary

- Family splits: `19`
- Failures: `3`
- Failure labels: `['hellgate_public_bookcase_33', 'hellgate_public_bookcase_6', 'hellgate_public_bookcase_8']`
- Copy-only failures: `2`
- Item-type failures: `1`
- Copy-length failures: `2`
- Family event totals min/median/max: `4` / `19` / `364`

## Failure Rows

| Family | Books | Events | Online gain | Frozen gain | Negative components | Reason |
|---|---|---:|---:|---:|---|---|
| `hellgate_public_bookcase_33` | `[18, 19]` | `10` | `-2.966` | `-2.940` | `['copy_length']` | `small_copy_only_family_copy_length_under_uniform` |
| `hellgate_public_bookcase_6` | `[38, 39]` | `15` | `0.161` | `-0.395` | `['item_type']` | `small_family_item_type_under_uniform` |
| `hellgate_public_bookcase_8` | `[68, 69]` | `4` | `-0.166` | `-0.167` | `['copy_length']` | `small_copy_only_family_copy_length_under_uniform` |

## Component Decomposition

| Family | Component | Uniform | Online | Online gain | Frozen | Frozen gain |
|---|---|---:|---:|---:|---:|---:|
| `hellgate_public_bookcase_33` | `copy_length` | `30.523` | `36.820` | `-6.297` | `36.779` | `-6.256` |
| `hellgate_public_bookcase_33` | `literal_payload` | `0.000` | `0.000` | `0.000` | `0.000` | `0.000` |
| `hellgate_public_bookcase_33` | `item_type` | `5.000` | `1.668` | `3.332` | `1.684` | `3.316` |
| `hellgate_public_bookcase_6` | `copy_length` | `23.362` | `22.461` | `0.901` | `22.980` | `0.383` |
| `hellgate_public_bookcase_6` | `literal_payload` | `16.610` | `14.703` | `1.906` | `14.703` | `1.906` |
| `hellgate_public_bookcase_6` | `item_type` | `5.000` | `7.647` | `-2.647` | `7.684` | `-2.684` |
| `hellgate_public_bookcase_8` | `copy_length` | `14.206` | `15.710` | `-1.503` | `15.710` | `-1.503` |
| `hellgate_public_bookcase_8` | `literal_payload` | `0.000` | `0.000` | `0.000` | `0.000` | `0.000` |
| `hellgate_public_bookcase_8` | `item_type` | `2.000` | `0.663` | `1.337` | `0.664` | `1.336` |

## Decision

- The family failures are component/sample-size stress cases, not a new row0-origin signal.
- The strongest failure is `hellgate_public_bookcase_33`: copy-length loses `6.297` bits online against uniform, while item-type saves only `3.332` bits.
- `hellgate_public_bookcase_8` is also copy-only and has only two copy events; the net loss is small.
- `hellgate_public_bookcase_6` is online-positive but frozen-negative because item-type loses to uniform under frozen counts.
- These failures keep the model at partial predictive structure; they do not support promoting a final authorial generation method.
- `translation_delta`: `NONE`; `row0` remains exogenous.
