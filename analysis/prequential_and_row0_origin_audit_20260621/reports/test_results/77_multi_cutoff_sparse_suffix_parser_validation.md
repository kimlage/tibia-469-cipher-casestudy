# Multi-Cutoff Sparse Suffix Parser Validation

Classification: `multi_cutoff_sparse_suffix_parser_roundtrips`
Translation delta: `NONE`

## Purpose

Gate 76 proved the sparse source/length parser on the cutoff-60 suffix.
This gate repeats the same sequential suffix parse at cutoffs `10`,
`20`, `35`, `50`, and `60`, freezing train counts at each prefix and
carrying `previous_copy_end` between held-out books.

## Summary

- Cutoffs: `10, 20, 35, 50, 60`.
- Suffix book evaluations: `175`.
- Roundtrip evaluations: `175/175`.
- Same-policy roundtrip evaluations: `175/175`.
- Raw-positive evaluations: `175/175`.
- Parser better/tie/worse than same policy: `12` / `163` / `0`.
- Total parser bits: `11992.210882`.
- Total same-policy reprice bits: `12004.390933`.
- Parser minus same-policy reprice: `-12.180052` bits.
- Total raw-uniform gain: `81935.306` bits.
- Total transition evaluations: `12714003`.
- Total visited states: `2952367`.
- Hardest parsed cell: cutoff `10`, book `17`, `463456` transitions.
- Elapsed wall time: `38.795` seconds.

## Cutoff Rows

| Cutoff | Books | Roundtrip | Raw-positive | Parser bits | Same-policy | Delta | Transitions | Max book | Seconds |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 60 | 60/60 | 60/60 | 4871.363 | 4877.736 | -6.374 | 4548802 | 17 | 12.382 |
| 20 | 50 | 50/50 | 50/50 | 3440.157 | 3443.850 | -3.693 | 3471794 | 56 | 10.299 |
| 35 | 35 | 35/35 | 35/35 | 2177.292 | 2179.349 | -2.057 | 2698191 | 56 | 8.430 |
| 50 | 20 | 20/20 | 20/20 | 1134.867 | 1134.923 | -0.056 | 1611668 | 56 | 5.925 |
| 60 | 10 | 10/10 | 10/10 | 368.532 | 368.532 | +0.000 | 383548 | 65 | 1.729 |

## Decision

- Sparse source/length parsing now roundtrips every tested future suffix for cutoffs 10, 20, 35, 50, and 60 with train counts frozen at each prefix and previous-copy-end state carried online. This is stronger predictive/parser evidence, including a small aggregate improvement over same-policy reprice with no worse suffix cells. It does not promote a new compression bound or authorial final method because the rows are overlapping validation cuts rather than one charged corpus recipe.
- No compression-bound change is introduced.
- No corpus-wide formula promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
