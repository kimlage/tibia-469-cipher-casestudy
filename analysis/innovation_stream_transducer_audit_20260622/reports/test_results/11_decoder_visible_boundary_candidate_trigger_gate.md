# Decoder Visible Boundary Candidate Trigger Gate

Classification: `decoder_visible_boundary_candidate_trigger_clue_promoted`
Translation delta: `NONE`

## Purpose

Test whether the `right_ge:4` boundary candidate trigger clue survives
after removing target-conditioned copy availability.

## Summary

- Candidate policy: `right_ge:4`.
- Candidate positions: `995`.
- Candidate nonstarts/literal/copy: `841` / `29` / `125`.
- Best overall feature: `book_start`.
- Best overall cutoff: `30`.
- Best overall exact candidates: `635/695`.
- Best overall start hits: `34/94`.
- Best overall saving vs three-way lookup: `87.064` bits.
- Best global exact/start hits: `140/153` / `0`.
- Best global saving vs three-way lookup: `-6.715` bits.
- Best feature over global: `book_start`.
- Best feature cutoff: `30`.
- Best feature exact candidates: `635/695`.
- Best feature start hits: `34/94`.
- Best feature literal/copy hits: `0` / `34`.
- Best feature predicted starts: `40`.
- Best feature errors: `60`.
- Best feature saving vs lookup: `87.064` bits.
- Same-cutoff global exact/start hits: `601` / `0`.
- Same-cutoff global saving vs lookup: `-42.580` bits.
- Best feature delta vs global: `129.644` bits.
- Best feature start-hit delta vs global: `34`.
- Target-conditioned candidate delta bits: `169.492`.
- Target-conditioning gap bits: `39.848`.
- Internal candidate positions: `935`.
- Internal best feature: `book_start`.
- Internal best feature exact candidates: `140/143`.
- Internal best feature start hits: `0/3`.
- Internal best feature literal/copy hits: `0` / `0`.
- Internal best feature saving vs lookup: `-8.044` bits.
- Internal best feature delta vs global: `-5.044` bits.
- Internal random delta bits p95: `-5.044`.
- Promotes internal decoder-visible trigger: `False`.
- Random delta bits p95: `-6.629`.
- Random start-hit delta p95: `0.000`.
- Promotes decoder-visible boundary candidate trigger: `True`.
- Weak decoder-visible boundary candidate trigger: `False`.

This gate repeats the boundary-candidate trigger test after removing target-conditioned copy availability. It keeps the right_ge:4 candidate set and asks whether decoder-visible boundary features can separate nonstarts, literal starts, and copy starts under prefix holdout.

## Best Rows

| Cutoff | Feature | Exact | Start hits | Lit/Copy hits | Pred starts | Errors | Saving | Delta bits | Delta starts | Contexts |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `30` | `book_start` | `635/695` | `34/94` | `0/34` | `40` | `60` | `87.064` | `129.644` | `34` | `2` |
| `30` | `target_start_bucket` | `635/695` | `34/94` | `0/34` | `40` | `60` | `80.724` | `123.305` | `34` | `6` |
| `30` | `book_start_x_rank` | `635/695` | `34/94` | `0/34` | `40` | `60` | `79.139` | `121.720` | `34` | `7` |
| `40` | `book_start` | `505/547` | `25/67` | `0/25` | `30` | `42` | `73.231` | `97.784` | `25` | `2` |
| `30` | `book_start_x_surprisal` | `630/695` | `35/94` | `0/35` | `49` | `65` | `52.739` | `95.319` | `35` | `10` |
| `40` | `target_start_bucket` | `505/547` | `25/67` | `0/25` | `30` | `42` | `66.891` | `91.444` | `25` | `6` |
| `40` | `book_start_x_rank` | `505/547` | `25/67` | `0/25` | `30` | `42` | `65.306` | `89.859` | `25` | `7` |
| `40` | `book_start_x_surprisal` | `502/547` | `27/67` | `0/27` | `38` | `45` | `46.997` | `71.550` | `27` | `10` |
| `20` | `surprisal_bucket` | `721/819` | `35/120` | `0/35` | `55` | `98` | `17.386` | `70.022` | `35` | `5` |
| `50` | `book_start` | `333/355` | `17/39` | `0/17` | `20` | `22` | `48.448` | `68.313` | `17` | `2` |
| `50` | `target_start_bucket` | `333/355` | `17/39` | `0/17` | `20` | `22` | `42.108` | `61.973` | `17` | `6` |
| `50` | `book_start_x_rank` | `333/355` | `17/39` | `0/17` | `20` | `22` | `38.938` | `58.803` | `17` | `8` |

## Decision

- This gate removes target-conditioned copy availability from the boundary-candidate trigger policy.
- Any promoted clue here is a target-free candidate-label dependency reducer, not a closed-loop generator.
- The internal-only decomposition is reported separately so book-start invariance is not overclaimed as internal skeleton generation.
- The `right_ge:4` candidate set still depends on the target digit stream and still misses canonical starts.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
