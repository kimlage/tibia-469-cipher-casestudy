# Operation Shape Count Generation Gate

Classification: `operation_shape_count_generator_rejected`
Translation delta: `NONE`

## Purpose

Test whether each book's coarse operation shape, `(op_count, literal_count)`,
can be generated from book id and book length before exact type sequence,
cutpoints, or source choice.

## Summary

- Books tested: `60`.
- Operation total: `261`.
- Literal operation total: `53`.
- Model candidates: `2416`.
- Best model: `context_book_mod10_x_length_bucket`.
- Best exact shape books: `37/60`.
- Best op-count exact books: `38/60`.
- Best literal-count exact books: `45/60`.
- Best total shape error: `140`.
- Best paid records: `58` vs exact shape atlas `60`.
- Paid-record delta vs exact atlas: `-2`.
- Random mean/p95/max exact books: `5.580` / `9` / `12`.
- Prefix/holdout cover-all cells: `0/5`.
- Prefix/holdout beats-random-p95 exact cells: `0/5`.

## Top Models

| Model | Exact shape | Op exact | Literal exact | Error | Paid records | Payload |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `context_book_mod10_x_length_bucket` | `37/60` | `38/60` | `45/60` | `140` | `58` | `35` |
| `context_book_mod5_x_length_bucket` | `25/60` | `26/60` | `39/60` | `196` | `56` | `21` |
| `context_book_mod10` | `19/60` | `22/60` | `35/60` | `224` | `52` | `11` |
| `context_book_mod5` | `16/60` | `18/60` | `34/60` | `220` | `50` | `6` |
| `context_book_decade` | `15/60` | `15/60` | `36/60` | `220` | `52` | `7` |
| `context_book_length_bucket` | `15/60` | `17/60` | `35/60` | `225` | `51` | `6` |
| `constant_shape_mode` | `12/60` | `12/60` | `35/60` | `254` | `49` | `1` |
| `length_div_ops_23_lit_60` | `4/60` | `6/60` | `7/60` | `361` | `58` | `2` |
| `length_div_ops_23_lit_55` | `4/60` | `6/60` | `7/60` | `373` | `58` | `2` |
| `length_div_ops_22_lit_60` | `4/60` | `5/60` | `7/60` | `377` | `58` | `2` |
| `length_div_ops_22_lit_55` | `4/60` | `5/60` | `7/60` | `389` | `58` | `2` |
| `length_div_ops_53_lit_180` | `3/60` | `7/60` | `10/60` | `231` | `59` | `2` |

## Prefix/Holdout

| Cutoff | Selected model | Test exact | Test error | Random mean exact | Random p95 exact | Beats p95 | Cover all |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| `20` | `context_book_mod10_x_length_bucket` | `0/50` | `570` | `1.621` | `4` | `False` | `False` |
| `30` | `context_book_mod10_x_length_bucket` | `4/40` | `154` | `2.313` | `5` | `False` | `False` |
| `40` | `context_book_mod10_x_length_bucket` | `5/30` | `121` | `2.171` | `5` | `False` | `False` |
| `50` | `context_book_mod10_x_length_bucket` | `3/20` | `55` | `1.765` | `4` | `False` | `False` |
| `60` | `context_book_mod10_x_length_bucket` | `2/10` | `23` | `1.061` | `3` | `False` | `False` |

## Decision

- Promotes operation-shape-count generator: `False`.
- Audit-only paid-record reduction: `True`.
- Coarse operation shape remains retained unless a later joint parser derives it with cutpoints.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
