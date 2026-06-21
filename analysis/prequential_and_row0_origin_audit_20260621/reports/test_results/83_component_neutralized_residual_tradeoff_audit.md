# Component-Neutralized Residual Tradeoff Audit

Classification: `component_neutralization_tradeoff_localized`
Translation delta: `NONE`

## Purpose

Gate 82 improved exact multi-cutoff path stability from `38/50` to
`48/50`. This audit identifies which books were resolved, which remain
unstable, and which instability was introduced by the structural
simplification.

## Summary

- Active unstable books: `[21, 24, 28, 30, 34, 35, 39, 46, 51, 56, 61, 65]`.
- Best-mode unstable books: `[26, 34]`.
- Resolved by best mode: `11` books.
- Persistent in best mode: `[34]`.
- Introduced by best mode: `[26]`.
- Best-mode parser-bit delta vs active: `67.605622`.
- Full-source extra cost vs best: `367.448154`.

## Affected Books

| Book | Status | Active signatures | Best signatures | Full-source signatures |
|---:|---|---:|---:|---:|
| 21 | `resolved_by_best` | 2 | 1 | 1 |
| 24 | `resolved_by_best` | 2 | 1 | 1 |
| 26 | `introduced_by_best` | 1 | 2 | 1 |
| 28 | `resolved_by_best` | 2 | 1 | 1 |
| 30 | `resolved_by_best` | 2 | 1 | 1 |
| 34 | `persistent_in_best` | 2 | 2 | 1 |
| 35 | `resolved_by_best` | 2 | 1 | 2 |
| 39 | `resolved_by_best` | 2 | 1 | 1 |
| 45 | `full_source_only_residual` | 1 | 1 | 2 |
| 46 | `resolved_by_best` | 2 | 1 | 1 |
| 51 | `resolved_by_best` | 2 | 1 | 1 |
| 56 | `resolved_by_best` | 2 | 1 | 1 |
| 61 | `resolved_by_best` | 2 | 1 | 1 |
| 65 | `resolved_by_best` | 4 | 1 | 1 |

## Decision

- Uniform copy-length/source-exception scoring resolves most active learned-path instabilities, but the gain is not a full mechanism closure: book 34 remains unstable and book 26 becomes newly unstable. Full source uniformization changes the residual pair but costs far more, so the source flag is not promoted as the next simplification.
- No compression-bound change is introduced.
- No corpus-wide formula promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
