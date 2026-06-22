# Book Start Mode Gate

Classification: `book_start_mode_policy_rejected`
Translation delta: `NONE`

## Purpose

Test whether book-start operation mode (`literal` vs `copy`) has a
target-free rule beyond global majority.

## Summary

- Book starts: `60`.
- Literal/copy starts: `13` / `47`.
- Best global exact books: `34/40` at cutoff `30`.
- Best global saving vs mode lookup: `0.000` bits.
- Best feature: `book_decade`.
- Best feature cutoff: `20`.
- Best feature exact books: `8/50`.
- Best feature literal/copy hits: `8` / `0`.
- Best feature saving vs lookup: `-4.000` bits.
- Best feature delta vs global: `-4.000` bits.
- Best feature exact delta vs global: `0`.
- Positive feature cells: `0`.
- Stable positive feature cells: `0`.
- Random delta bits p95: `-4.000`.
- Random exact delta p95: `0.000`.
- Random positive cells p95: `0.000`.
- Promotes book-start mode: `False`.
- Weak book-start mode: `False`.

This gate tests whether the promoted book-start clue can be refined into a target-free first-operation mode parser. A promotion requires a non-global feature to beat shuffled controls and remain positive beyond the unstable earliest split.

## Best Rows

| Cutoff | Feature | Exact | Lit/Copy hits | Errors | Saving | Delta bits | Delta exact | Contexts |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `global_majority` | `8/50` | `8/0` | `42` | `-0.000` | `0.000` | `0` | `0` |
| `30` | `global_majority` | `34/40` | `0/34` | `6` | `0.000` | `0.000` | `0` | `0` |
| `40` | `global_majority` | `25/30` | `0/25` | `5` | `0.000` | `0.000` | `0` | `0` |
| `50` | `global_majority` | `17/20` | `0/17` | `3` | `0.000` | `0.000` | `0` | `0` |
| `60` | `global_majority` | `8/10` | `0/8` | `2` | `0.000` | `0.000` | `0` | `0` |
| `20` | `book_decade` | `8/50` | `8/0` | `42` | `-4.000` | `-4.000` | `0` | `1` |
| `30` | `book_decade` | `34/40` | `0/34` | `6` | `-5.000` | `-5.000` | `0` | `2` |
| `30` | `emitted_len_bucket` | `34/40` | `0/34` | `6` | `-6.000` | `-6.000` | `0` | `3` |
| `40` | `book_decade` | `25/30` | `0/25` | `5` | `-6.000` | `-6.000` | `0` | `3` |
| `50` | `book_decade` | `17/20` | `0/17` | `3` | `-7.000` | `-7.000` | `0` | `4` |
| `50` | `emitted_len_bucket` | `17/20` | `0/17` | `3` | `-7.000` | `-7.000` | `0` | `4` |
| `40` | `emitted_len_bucket` | `25/30` | `0/25` | `5` | `-7.000` | `-7.000` | `0` | `4` |

## Decision

- A book-start mode policy is promoted only if it beats shuffled controls and remains positive beyond the earliest unstable split.
- Under current features, the apparent `book_mod10` improvement is not promoted as a stable mode parser.
- The book-start clue remains structural: every derived book has a first operation, but its literal/copy mode remains externally declared.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
