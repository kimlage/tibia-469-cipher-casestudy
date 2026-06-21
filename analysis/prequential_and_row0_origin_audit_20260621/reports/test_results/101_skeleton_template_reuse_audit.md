# Skeleton Template Reuse Audit

Classification: `skeleton_template_reuse_sparse`
Translation delta: `NONE`

## Purpose

Gate 100 rejected simple rules for generating the skeleton. This audit
checks whether the remaining skeleton atlas can be reduced by exact
template reuse or type-sequence motif reuse across books.

## Result

- Books: `60`.
- Exact skeleton unique templates: `58`.
- Exact reused clusters/books: `2` / `4`.
- Exact largest cluster: `2`.
- Type-sequence unique templates: `28`.
- Type-sequence reused books: `39`.
- Type-sequence largest cluster: `12`.
- Exact reused clusters: `[[43, 50], [47, 62]]`.
- Type-sequence reused clusters: `[[22, 27, 33, 43, 47, 50, 53, 62, 66, 67, 68, 69], [18, 35, 37, 48, 51, 54, 61, 63, 64], [19, 21, 24, 45, 46, 59], [10, 25, 44, 52], [29, 41, 55], [32, 39, 58], [30, 36]]`.

## Decision

- Template reuse promotable: `False`.
- Exact skeleton template reuse is sparse: most books still need their own length/target skeleton. Type-sequence motifs repeat, but length-bearing templates do not repeat enough to replace the skeleton atlas with a small template library.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
