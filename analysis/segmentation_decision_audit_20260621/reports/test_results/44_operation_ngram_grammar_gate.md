# Operation N-Gram Grammar Gate

Classification: `operation_ngram_grammar_rejected`
Translation delta: `NONE`

## Purpose

Gate 44 tests whether the remaining residual first-drift operations are
explained by a small operation-sequence grammar: unigram, op-index bucket,
previous operation types, previous operation labels, and previous-label plus
op-bucket contexts. The grammar is trained only on books already parsed
exactly by the active parser.

## Summary

- Exact parser books used for grammar training: `50`.
- Residual books tested: `10`.
- Residual decisions tested: `10`.
- Families tested: `9`.
- Best family: `prev2_op_bucket`.
- Best hits: `0/10`.
- Best false positives: `4`.
- Best unsupported residuals: `6`.
- Best context count: `145`.
- Best structural-family net bits vs lookup: `1645.726`.
- Lowest net family: `unigram` at `4.170` bits with `10` false positives.
- Prequential cells with held-out hit: `0/4`.
- Shuffle p_ge_observed: `1.0000`.
- Promotes operation n-gram grammar: `False`.

## Scoreboard

| family | hits | false positives | unsupported | contexts | net bits |
| --- | --- | --- | --- | --- | --- |
| prev2_op_bucket | 0 | 4 | 6 | 145 | 1645.726 |
| prev3 | 0 | 4 | 6 | 146 | 1658.523 |
| prev2 | 0 | 5 | 5 | 142 | 1607.393 |
| prev1_op_bucket | 0 | 6 | 4 | 124 | 1379.391 |
| prev1 | 0 | 7 | 3 | 67 | 685.813 |
| unigram | 0 | 10 | 0 | 1 | 4.170 |
| prev1_type | 0 | 10 | 0 | 3 | 17.265 |
| prev2_type | 0 | 10 | 0 | 6 | 40.529 |
| op_bucket | 0 | 10 | 0 | 9 | 66.059 |

## Best-Family Residual Rows

| book | op | active label | stable label | predicted label | status | support | choices |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | 0 | ('literal', 27) | ('literal', 39) | ('literal', 3) | false_positive | 3 | 39 |
| 16 | 9 | ('copy', 8) | ('literal', 1) | None | unsupported | 0 | 0 |
| 20 | 2 | ('literal', 3) | ('copy', 10) | None | unsupported | 0 | 0 |
| 21 | 0 | ('literal', 7) | ('copy', 9) | ('literal', 3) | false_positive | 3 | 39 |
| 26 | 0 | ('literal', 1) | ('copy', 11) | ('literal', 3) | false_positive | 3 | 39 |
| 34 | 7 | ('literal', 5) | ('copy', 5) | None | unsupported | 0 | 0 |
| 39 | 0 | ('literal', 7) | ('copy', 5) | ('literal', 3) | false_positive | 3 | 39 |
| 45 | 1 | ('literal', 1) | ('copy', 8) | None | unsupported | 0 | 0 |
| 55 | 2 | ('copy', 45) | ('copy', 44) | None | unsupported | 0 | 0 |
| 57 | 2 | ('literal', 17) | ('literal', 28) | None | unsupported | 0 | 0 |

## Prequential Rows

| cutoff | test residuals | hits | false positives | unsupported | net bits |
| --- | --- | --- | --- | --- | --- |
| 20 | 8 | 0 | 3 | 5 | 524.586 |
| 30 | 5 | 0 | 1 | 4 | 768.074 |
| 40 | 3 | 0 | 0 | 3 | 1069.129 |
| 50 | 2 | 0 | 0 | 2 | 1366.830 |
| 60 | 0 | 0 | 0 | 0 | 1543.710 |

## Shuffle Control

- Trials: `400`.
- Shuffle min/mean/max hits: `0` / `0.198` / `1`.
- Shuffle >= observed: `400`.
- p_ge_observed: `1.0000`.

## Decision

No operation n-gram grammar is promoted. The best family explains `0`
residuals; coarser grammars produce false positives and richer grammars become
unsupported. This rejects a compact operation-sequence grammar as the missing
latent path/state mechanism.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
