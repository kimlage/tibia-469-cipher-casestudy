# Cutoff-60 Sparse Suffix Source/Length Parser Gate

Classification: `cutoff60_sparse_suffix_source_length_parser_roundtrips`
Translation delta: `NONE`

## Purpose

Gate 74 proved sparse Dijkstra on the cutoff-60 hard book `66`.
This gate runs the same sparse source/length parser across the full
cutoff-60 suffix, carrying `previous_copy_end` from each parsed book
into the next book.

## Summary

- Books parsed: `10` (`60..69`).
- Roundtrip books: `10/10`.
- Same-policy roundtrip books: `10/10`.
- Books beating raw digit uniform: `10/10`.
- Total parser bits: `368.531807`.
- Total same-policy reprice bits: `368.531807`.
- Parser minus same-policy reprice: `+0.000000` bits.
- Total raw-uniform gain: `4478.161` bits.
- Parser better/tie/worse than same policy: `0` / `10` / `0`.
- Total transition evaluations: `383548`.
- Total visited states: `114815`.
- Hardest parsed book by transitions: `65` (`113299` transitions).
- Elapsed wall time: `1.740` seconds.

## Book Rows

| Book | Digits | Parser bits | Same-policy | Delta | Raw gain | Ops | Copies | Literals | Transitions | States | Prev end in->out | Seconds |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 60 | 151 | 104.741 | 104.741 | +0.000 | 396.871 | 6 | 5 | 1 | 62683 | 13461 | `121` -> `7047` | 0.043 |
| 61 | 145 | 37.039 | 37.039 | +0.000 | 444.641 | 2 | 2 | 0 | 43209 | 9824 | `7047` -> `3066` | 0.028 |
| 62 | 126 | 20.319 | 20.319 | +0.000 | 398.244 | 1 | 1 | 0 | 7114 | 3397 | `3066` -> `550` | 0.006 |
| 63 | 126 | 38.997 | 38.997 | +0.000 | 379.566 | 2 | 2 | 0 | 32857 | 10825 | `550` -> `1326` | 0.023 |
| 64 | 151 | 34.311 | 34.311 | +0.000 | 467.300 | 2 | 2 | 0 | 36612 | 14896 | `1326` -> `7100` | 0.030 |
| 65 | 169 | 46.826 | 46.826 | +0.000 | 514.580 | 3 | 2 | 1 | 113299 | 18861 | `7100` -> `7083` | 0.081 |
| 66 | 210 | 21.974 | 21.974 | +0.000 | 675.631 | 1 | 1 | 0 | 41832 | 20932 | `7083` -> `1906` | 0.032 |
| 67 | 98 | 21.126 | 21.126 | +0.000 | 304.423 | 1 | 1 | 0 | 8657 | 4219 | `1906` -> `303` | 0.008 |
| 68 | 143 | 21.611 | 21.611 | +0.000 | 453.424 | 1 | 1 | 0 | 19052 | 9387 | `303` -> `3012` | 0.015 |
| 69 | 140 | 21.588 | 21.588 | +0.000 | 443.482 | 1 | 1 | 0 | 18233 | 9013 | `3012` -> `1686` | 0.013 |

## Decision

- Sparse Dijkstra now executes the full cutoff-60 held-out suffix with previous-copy-end state carried between books. This is a real parser implementation step, but not a new compression bound or final authorial method because the train counts remain fixed at one cutoff and the result is still a local suffix gate.
- No compression-bound change is introduced.
- No corpus-wide parser or recipe-discovery promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
