# Full-Corpus Source Substitution Fourth-Pass Gate

Classification: `full_corpus_source_substitution_fourth_pass_improves_bound`
Translation delta: `NONE`

## Purpose

Gate 44 found another microscopic third-pass source substitution gain.
This gate reruns the exact single/pair frontier on the promoted
`8160.825917` bit formula to test whether a fourth local source update
still survives adaptive rescore. Segmentation and copy lengths remain fixed.

## Summary

- Active total bits: `8160.825917`.
- Candidate total bits: `8160.825608`.
- Candidate gain: `+0.000310` bits.
- Active copy-source bits: `2986.347324`.
- Candidate copy-source bits: `2986.347015`.
- Copy events: `261`.
- Candidate source options: `637`.
- Single substitutions searched: `376`.
- Positive singles: `3`.
- Pair substitutions searched: `69849`.
- Positive pairs: `509`.
- Best arity: `2`.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469.json](../../../authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469.json)

## Best Substitutions

| Event | Book | Op | Length | Old source | New source | Gain bits |
|---:|---:|---:|---:|---:|---:|---:|
| `141` | `28` | `4` | `18` | `2397` | `3084` | `+0.000310` |
| `227` | `56` | `5` | `12` | `2234` | `2260` | `+0.000310` |

## Interpretation

This remains a fixed-recipe local source frontier. Any positive result
updates the compression bound only; it does not strengthen the generation
explanation because segmentation, copy lengths, and higher-order
substitutions remain outside this gate.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- Recipe segmentation and copy lengths remain fixed.
- Triple and higher-order source substitutions are outside this gate.
