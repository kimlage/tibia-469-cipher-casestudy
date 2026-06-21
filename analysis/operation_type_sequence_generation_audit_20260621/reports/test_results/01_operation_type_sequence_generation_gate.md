# Operation Type Sequence Generation Gate

Classification: `operation_type_sequence_generator_rejected`
Translation delta: `NONE`

## Purpose

Test whether the literal/copy type sequence within each book can be
generated after granting `(op_count, literal_count)`. This is
source-free and target-text-free.

## Summary

- Books/operations: `60` / `261`.
- Literal/copy totals: `53` / `208`.
- Models tested: `10`.
- Best model: `template_book_mod5_x_shape`.
- Best exact books: `60/60`.
- Best type hits: `261/261`.
- Best paid records: `235` vs exact sequence atlas `60`.
- Best paid records vs exact type fields: `235` vs `261`.
- Paid-record delta vs exact type fields: `-26`.
- Random mean/p95/max exact books: `39.449` / `42` / `44`.
- Random mean/p95/max type hits: `191.486` / `201` / `211`.
- Prefix/holdout cover-all cells: `0/5`.
- Prefix/holdout beats-random-p95 exact cells: `0/5`.

## Top Models

| Model | Kind | Exact books | Type hits | Paid records | Payload |
| --- | --- | ---: | ---: | ---: | ---: |
| `template_book_mod5_x_shape` | `template` | `60/60` | `261/261` | `235` | `235` |
| `template_book_mod10_x_shape` | `template` | `60/60` | `261/261` | `247` | `247` |
| `template_book_mod10_x_length_bucket_x_shape` | `template` | `60/60` | `261/261` | `258` | `258` |
| `template_length_bucket_x_shape` | `template` | `59/60` | `259/261` | `227` | `223` |
| `template_shape` | `template` | `56/60` | `249/261` | `193` | `162` |
| `front_literals` | `deterministic` | `41/60` | `201/261` | `153` | `1` |
| `alternating_from_start` | `deterministic` | `41/60` | `191/261` | `153` | `1` |
| `alternating_from_second` | `deterministic` | `40/60` | `201/261` | `152` | `1` |
| `even_literals` | `deterministic` | `40/60` | `193/261` | `152` | `1` |
| `back_literals` | `deterministic` | `35/60` | `183/261` | `170` | `1` |

## Prefix/Holdout

| Cutoff | Selected model | Test exact | Test hits | Random p95 exact | Random p95 hits | Beats exact | Beats hits | Cover all |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `20` | `template_length_bucket_x_shape` | `36/50` | `144/182` | `39` | `152` | `False` | `False` | `False` |
| `30` | `template_book_mod5_x_shape` | `28/40` | `112/140` | `31` | `118` | `False` | `False` | `False` |
| `40` | `template_length_bucket_x_shape` | `23/30` | `79/95` | `24` | `79` | `False` | `False` | `False` |
| `50` | `template_book_mod5_x_shape` | `16/20` | `48/56` | `17` | `50` | `False` | `False` | `False` |
| `60` | `template_book_mod5_x_shape` | `8/10` | `16/20` | `10` | `20` | `False` | `False` | `False` |

## Decision

- Promotes operation-type-sequence generator: `False`.
- Audit-only paid-record reduction: `True`.
- Literal/copy sequence remains retained unless a later joint parser derives it with lengths and copy availability.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
