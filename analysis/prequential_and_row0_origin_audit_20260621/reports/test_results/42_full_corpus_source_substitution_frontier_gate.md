# Full-Corpus Source Substitution Frontier Gate

Classification: `full_corpus_source_substitution_frontier_improves_bound`
Translation delta: `NONE`

## Purpose

Gate 41 promoted a fixed-recipe source-path formula. This gate tests the
next local frontier: every single and pair same-chunk legal source
substitution is rescored under the real adaptive source default/exception
stream. Segmentation and copy lengths remain fixed.

## Summary

- Active total bits: `8162.412`.
- Candidate total bits: `8160.827`.
- Candidate gain: `+1.585` bits.
- Active copy-source bits: `2987.933`.
- Candidate copy-source bits: `2986.348`.
- Copy events: `261`.
- Candidate source options: `637`.
- Single substitutions searched: `376`.
- Positive singles: `12`.
- Pair substitutions searched: `69849`.
- Positive pairs: `2686`.
- Best arity: `2`.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_frontier_formula_469.json](../../../authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_frontier_formula_469.json)

## Best Substitutions

| Event | Book | Op | Length | Old source | New source | Gain bits |
|---:|---:|---:|---:|---:|---:|---:|
| `46` | `7` | `1` | `7` | `401` | `819` | `+1.585` |
| `79` | `14` | `2` | `26` | `154` | `1247` | `+1.585` |

## Interpretation

This is a local source frontier, not a complete parser. It can promote a
new compression bound only if a single or pair source substitution
improves the full adaptive source-stream score.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- Recipe segmentation and copy lengths remain fixed.
- Triple and higher-order source substitutions are outside this gate.
