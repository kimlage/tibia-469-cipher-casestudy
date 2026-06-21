# Operation Count Generation Gate

Classification: `operation_count_generator_rejected`
Translation delta: `NONE`

## Purpose

Test whether the per-book operation count in the source-free skeleton
can be generated from book id and book length, before any cutpoint
or source choice is considered.

## Summary

- Books tested: `60`.
- Operation total: `261`.
- Model candidates: `229`.
- Best model: `context_book_mod10_x_length_bucket`.
- Best exact books: `40/60`.
- Best absolute error: `98`.
- Best paid records: `55` vs exact atlas `60`.
- Paid-record delta vs exact atlas: `-5`.
- Random mean/p95/max exact books: `8.143` / `13` / `18`.
- Prefix/holdout cover-all cells: `0/5`.
- Prefix/holdout beats-random-p95 exact cells: `0/5`.

## Top Models

| Model | Exact books | Abs error | Paid records | Payload |
| --- | ---: | ---: | ---: | ---: |
| `context_book_mod10_x_length_bucket` | `40/60` | `98` | `55` | `35` |
| `context_book_mod10` | `23/60` | `163` | `48` | `11` |
| `context_book_mod5` | `18/60` | `167` | `48` | `6` |
| `book_length_floor_div_72` | `17/60` | `174` | `44` | `1` |
| `context_book_length_bucket` | `17/60` | `176` | `49` | `6` |
| `book_length_floor_div_73` | `16/60` | `175` | `45` | `1` |
| `book_length_floor_div_71` | `16/60` | `175` | `45` | `1` |
| `book_length_floor_div_74` | `16/60` | `176` | `45` | `1` |
| `book_length_floor_div_75` | `16/60` | `177` | `45` | `1` |
| `context_book_decade` | `16/60` | `177` | `51` | `7` |
| `book_length_floor_div_76` | `15/60` | `181` | `46` | `1` |
| `book_length_floor_div_80` | `15/60` | `182` | `46` | `1` |

## Prefix/Holdout

| Cutoff | Selected model | Test exact | Test abs error | Random mean exact | Random p95 exact | Beats p95 | Cover all |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| `20` | `context_book_mod10_x_length_bucket` | `6/50` | `204` | `3.980` | `7` | `False` | `False` |
| `30` | `context_book_mod10_x_length_bucket` | `7/40` | `120` | `4.428` | `8` | `False` | `False` |
| `40` | `context_book_mod10_x_length_bucket` | `6/30` | `85` | `3.546` | `6` | `False` | `False` |
| `50` | `context_book_mod10_x_length_bucket` | `4/20` | `42` | `2.735` | `5` | `False` | `False` |
| `60` | `context_book_mod10_x_length_bucket` | `2/10` | `19` | `1.571` | `3` | `False` | `False` |

## Decision

- Promotes operation-count generator: `False`.
- Audit-only paid-record reduction: `True`.
- The operation-count field remains a retained skeleton dependency unless a later gate derives it jointly with cutpoints.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
