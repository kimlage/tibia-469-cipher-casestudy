# Seed Coverage Audit

Classification: `AUDIT_ONLY_COMPRESSION`
Translation delta: `NONE`

## Scope

- Minimum copy length: `5`.
- Parse policy: `dynamic_programming_over_longest_available_copy_at_each_position`.
- Copy source is restricted to declared seed books only.
- Copies cannot cross seed-book boundaries.
- Target self-copy and derived-to-derived copy are disabled.
- Random controls per k: `100`.
- Permuted-prefix controls per k: `100`.

## Operational 0-9

- Seed books: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`.
- Copied digits explained: `8664` / `9567`.
- Literal digits required: `903`.
- Copy items required: `397`.
- Coverage rate: `0.905613`.
- Random copied-digit percentile: `0.210000`.
- Gain vs random median after declaration: `-1132.777` bits.

## Best k=10 Candidate

- Label: `greedy_coverage`.
- Seed books: `[7, 8, 9, 13, 17, 20, 25, 39, 54, 67]`.
- Copied digits explained: `9734`.
- Literal digits required: `247`.
- Coverage rate: `0.975253`.
- Alternative better than operational: `True`.

## Best By k

| k | label | copied | literal | copies | coverage | seed books |
|---:|---|---:|---:|---:|---:|---|
| 5 | `greedy_coverage` | 10011 | 353 | 459 | 0.965940 | `[8, 9, 13, 17, 25]` |
| 10 | `greedy_coverage` | 9734 | 247 | 388 | 0.975253 | `[7, 8, 9, 13, 17, 20, 25, 39, 54, 67]` |
| 15 | `greedy_coverage` | 9328 | 100 | 279 | 0.989393 | `[1, 7, 8, 9, 12, 13, 17, 18, 20, 25, 39, 49, 54, 55, 67]` |
| 20 | `greedy_coverage` | 8721 | 82 | 252 | 0.990685 | `[1, 7, 8, 9, 12, 13, 14, 17, 18, 20, 24, 25, 27, 34, 39, 49, 54, 55, 63, 67]` |

## Decision

- Books 0-9 special as seed: `False`.
- Alternative k=10 seed better: `True`.
- Gain over random survives declaration cost: `False`.
- Mechanical primary core signal: `not_promoted_posthoc_alternatives_exist`.
- Authorial seed claim: `BLOCKED_NEEDS_EXTERNAL_SOURCE`.
- Row0 remains unchanged and exogenous.
- Translation/plaintext status remains `NONE`.
