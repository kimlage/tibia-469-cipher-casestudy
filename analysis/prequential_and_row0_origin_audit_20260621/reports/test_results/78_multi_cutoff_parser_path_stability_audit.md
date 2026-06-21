# Multi-Cutoff Parser Path Stability Audit

Classification: `multi_cutoff_parser_paths_partially_stable`
Translation delta: `NONE`

## Purpose

Gate 77 showed that sparse source/length parsing roundtrips every
tested suffix across cutoffs. This gate asks whether the exact parser
paths are stable for the same book when the frozen training prefix
changes.

## Summary

- Parser evaluations replayed: `175`.
- Books with multiple cutoff views: `50`.
- Stable exact-path books: `38`.
- Unstable exact-path books: `12`.
- Stable exact-path fraction: `0.760`.
- Max signatures for one book: `4`.
- Unique book signatures across tested books: `64`.
- Total transition evaluations: `12714003`.
- Total visited states: `2952367`.
- Elapsed wall time: `10.737` seconds.

## Most Unstable Books

| Book | Cutoffs | Signatures | Dominant cutoffs | Variant cutoffs |
|---:|---|---:|---|---|
| 65 | `[10, 20, 35, 50, 60]` | 4 | `[10, 20]` | `[[10, 20], [35], [50], [60]]` |
| 21 | `[10, 20]` | 2 | `[10]` | `[[10], [20]]` |
| 24 | `[10, 20]` | 2 | `[10]` | `[[10], [20]]` |
| 28 | `[10, 20]` | 2 | `[10]` | `[[10], [20]]` |
| 30 | `[10, 20]` | 2 | `[10]` | `[[10], [20]]` |
| 34 | `[10, 20]` | 2 | `[10]` | `[[10], [20]]` |
| 35 | `[10, 20, 35]` | 2 | `[10, 20]` | `[[10, 20], [35]]` |
| 39 | `[10, 20, 35]` | 2 | `[10, 20]` | `[[10, 20], [35]]` |
| 46 | `[10, 20, 35]` | 2 | `[20, 35]` | `[[20, 35], [10]]` |
| 51 | `[10, 20, 35, 50]` | 2 | `[10, 20, 35]` | `[[10, 20, 35], [50]]` |

## Decision

- The sparse parser is executable and predictive across cutoffs, but exact operation paths are only partially stable under different frozen prefixes. Stable books support a reusable mechanism; unstable books identify where the current objective still depends on learned stream weights and tie-breaking rather than a prefix-invariant authorial recipe.
- No compression-bound change is introduced.
- No corpus-wide formula promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
