# Target Digit Boundary Gate

Classification: `target_digit_boundary_markov_clue_promoted_not_generator`
Translation delta: `NONE`

## Purpose

Test whether internal operation cutpoints are aligned with surprisal
under the prequential `prev2_digits` target digit process.

## Summary

- Books tested: `60`.
- Internal cutpoints: `201`.
- Candidate boundary positions: `9507`.
- Right-surprisal mean at real cutpoints: `3.808645`.
- Right-surprisal random mean/p95: `2.128341` / `2.293949`.
- Right-surprisal top10 hits: `88/201` (`0.437811`), random p95 `0.139303`.
- Right-surprisal top-k selector hits: `57/201` (`0.283582`), exact nontrivial books `0/48`.
- Zero-cutpoint books: `12`.
- Delta right-left mean/p95 control: `1.584790` / `0.207621`.

## Metric Table

| Metric | Observed mean | Random p95 | Top10 fraction | Top10 random p95 | Top-k hits | Top-k random p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `right_surprisal` | `3.808645` | `2.293949` | `0.437811` | `0.139303` | `57/201` | `0.069652` |
| `left_surprisal` | `2.223855` | `2.295141` | `0.129353` | `0.139303` | `8/201` | `0.069652` |
| `sum2_surprisal` | `6.032501` | `4.512938` | `0.348259` | `0.139303` | `29/201` | `0.069652` |
| `delta_right_left` | `1.584790` | `0.207621` | `0.383085` | `0.139303` | `50/201` | `0.069652` |

## Decision

- Promotes target digit boundary Markov clue: `True`.
- Promotes target digit boundary generator: `False`.
- Real cutpoints are strongly enriched before high-surprisal `prev2` digits.
- Top-k surprisal selection does not reconstruct the skeleton: it hits a minority of cutpoints and does not solve full books.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
