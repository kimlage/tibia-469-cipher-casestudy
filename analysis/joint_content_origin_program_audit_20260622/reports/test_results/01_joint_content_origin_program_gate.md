# Joint Content-Origin Program Gate

Classification: `PROMOTED_LITERAL_SPAN_CONTENT_ORIGIN_SUBPROGRAM`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- V5 fallback copy events: `101`.
- Baseline copy-hint bits: `891.118`.
- Best model: `literal_span_offset`.
- Best delta after declaration: `-32.320` bits.
- Candidate external bits excluding seed: `4065.013`.
- Holdout positive splits: `4/5`.
- Source inside seed spans: `56`.
- Source inside prior literal spans: `11`.
- Seed/literal span hits: `67`.
- Prior-op span hits: `101`.
- Literal nearest exact-mark count: `6`.
- Literal nearest median abs offset: `394`.

## Model Costs

| Model | Coverage | Missing | Bits after declaration | Delta vs copy-hint |
| --- | ---: | ---: | ---: | ---: |
| `literal_start_end_nearest` | `101` | `0` | `1323.691` | `432.573` |
| `literal_span_offset` | `11` | `90` | `858.798` | `-32.320` |
| `seed_or_literal_span_offset` | `67` | `34` | `1083.882` | `192.764` |
| `prior_op_span_offset` | `101` | `0` | `1232.381` | `341.263` |
| `prior_op_start_end_nearest` | `101` | `0` | `1049.179` | `158.061` |

## Prefix Holdout

| Cutoff | Selected model | Test rows | Test delta |
| ---: | --- | ---: | ---: |
| `20` | `literal_span_offset` | `73` | `-31.424` |
| `30` | `literal_span_offset` | `58` | `-16.414` |
| `40` | `literal_span_offset` | `42` | `-9.017` |
| `50` | `literal_span_offset` | `27` | `-9.017` |
| `60` | `literal_span_offset` | `9` | `1.876` |

## Control

- Best-model observed bits after declaration: `858.798`.
- Random source-position p05/p50/p95: `875.078` / `887.298` / `894.954`.
- Beats p05: `True`.

## Decision

`PROMOTED_LITERAL_SPAN_CONTENT_ORIGIN_SUBPROGRAM`: limited executable reduction for fallback copy origins that start inside prior literal innovation spans.

This is not a complete generator: most fallback copy origins, literal payload, seed payload, and row0 remain external.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
