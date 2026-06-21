# 144. Copy Source Distance Model Audit

Classification: `copy_source_backward_distance_rejected_absolute_source_retained`
Translation delta: `NONE`

## Purpose

Audit 137 retained an absolute copy-source default/exception model as a
compression-bound component. The corrected audit 141/142 profile keeps
that source model as prefix-frozen evidence while still marking the
generation claim partial because family holdouts fail. This audit tests
a structural alternative common in LZ descriptions: encode copy source
as backward distance from the current emitted length instead of as an
absolute source position.

## Full-Corpus Result

| Representation | Model | Stream bits | Gain vs uniform | Defaults | Replacement total |
|---|---|---:|---:|---:|---:|
| `absolute_source` | `adaptive` | `3012.311` | `19.389` | `n/a` | `n/a` |
| `absolute_source` | `default_exception` | `2990.838` | `40.862` | `5/261` | `8177.317` |
| `backward_distance` | `adaptive` | `3034.066` | `-2.366` | `n/a` | `n/a` |
| `backward_distance` | `default_exception` | `3016.389` | `15.310` | `5/261` | `8202.868` |

- Uniform legal source/distance bits: `3031.700`
- Active absolute default/exception stream: `2990.838` bits
- Backward-distance default/exception stream: `3016.389` bits
- Distance replacement total: `8202.868` bits
- Distance copy-address delta vs active: `25.551` bits

## Prefix Future-Suffix Controls

| Split | Test events | Absolute default frozen gain | Distance default frozen gain | Absolute adaptive frozen gain | Distance adaptive frozen gain |
|---|---:|---:|---:|---:|---:|
| `prefix_10_future_suffix` | `204` | `32.113` | `25.111` | `4.164` | `-3.836` |
| `prefix_20_future_suffix` | `152` | `26.544` | `20.540` | `1.956` | `-4.044` |
| `prefix_35_future_suffix` | `93` | `30.620` | `21.618` | `6.127` | `-2.873` |
| `prefix_50_future_suffix` | `48` | `9.402` | `5.817` | `3.022` | `-0.563` |
| `prefix_60_future_suffix` | `18` | `10.241` | `6.656` | `2.979` | `-0.606` |

## Interpretation

Backward distance is decodable and uses the same number of legal choices
as absolute source at each copy event. The test therefore isolates the
question of whether distances repeat or generalize better than absolute
source positions. They do not: both the adaptive distance stream and
the previous-distance default/exception stream are worse than the
corresponding absolute-source controls. The replacement would worsen
the active compression bound rather than improve validation.

## Decision

- Retain the active absolute copy-source default/exception model as the current compression-bound and prefix-frozen partial component.
- Reject backward-distance copy-source coding for the current formula.
- The generation claim remains partial because family/bookcase holdouts still have failures.
- No plaintext, translation, row0-origin, or authorial-intent claim is introduced.
