# Latent Transducer Beam Gate

Classification: `latent_transducer_first_gate_not_promoted`
Translation delta: `NONE`

## Purpose

Test the first joint literal/copy/boundary transducer route. The decoder
trains parameters on prefix books, freezes them, then parses future books
with a beam that chooses literal spans or available copy spans in one pass.

This is not a closed-loop digit generator yet: the target digit stream is
teacher-forced so that the gate can isolate whether the operation skeleton
emerges from joint transduction rather than a declared atlas.

## Summary

- Prefix cutoffs tested: `5`.
- Beam width: `80`.
- Aggregate exact books: `34`.
- Aggregate nontrivial exact books: `0`.
- Aggregate cutpoint hits: `224/343`.
- Cells beating random cutpoint p95: `5/5`.
- Aggregate source+length hits: `131/421`.
- Aggregate cutpoint atlas bits: `2063.661`.
- Aggregate cutpoint correction bits: `1387.992`.
- Aggregate cutpoint saving vs atlas: `675.669`.
- Predicted literal digits: `202`.
- Canonical literal digits: `354`.
- Promotes latent transducer generator: `False`.

This first joint transducer gate decodes operations from a shared literal/copy/boundary cost model under prefix holdout, but it still uses the target digit stream as teacher-forced input. Promotion requires nontrivial exact books plus random-control survival.

## Cutoff Rows

| Cutoff | Exact books | Nontrivial exact | Cutpoint hits | Random p95 | Cutpoint saving | Source+length | Literal digits |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `10/50` | `0` | `94/132` | `21.000` | `284.215` | `53/155` | `70/126` |
| `30` | `8/40` | `0` | `65/100` | `15.000` | `199.817` | `37/119` | `57/97` |
| `40` | `7/30` | `0` | `40/65` | `11.000` | `112.051` | `23/80` | `52/82` |
| `50` | `5/20` | `0` | `21/36` | `6.000` | `65.666` | `12/49` | `21/45` |
| `60` | `4/10` | `0` | `4/10` | `2.000` | `13.919` | `6/18` | `2/4` |

## Decision

- The first latent-transducer beam is not promoted as a generator unless the JSON summary says otherwise.
- This gate tests the right joint object but remains target-stream teacher-forced.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
