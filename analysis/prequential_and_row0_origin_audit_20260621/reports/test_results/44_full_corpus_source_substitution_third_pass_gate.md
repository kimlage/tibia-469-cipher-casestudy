# Full-Corpus Source Substitution Third-Pass Gate

Classification: `full_corpus_source_substitution_third_pass_improves_bound`
Translation delta: `NONE`

## Purpose

Gate 43 found only a microscopic second-pass source substitution gain.
This gate reruns the exact single/pair frontier on the promoted
`8160.826421` bit formula to check whether the local source frontier is
now effectively closed. Segmentation and copy lengths remain fixed.

## Summary

- Active total bits: `8160.826421`.
- Candidate total bits: `8160.825917`.
- Candidate gain: `+0.000503` bits.
- Active copy-source bits: `2986.347828`.
- Candidate copy-source bits: `2986.347324`.
- Copy events: `261`.
- Candidate source options: `637`.
- Single substitutions searched: `376`.
- Positive singles: `7`.
- Pair substitutions searched: `69849`.
- Positive pairs: `1371`.
- Best arity: `2`.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_third_pass_formula_469.json](../../../authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_third_pass_formula_469.json)

## Best Substitutions

| Event | Book | Op | Length | Old source | New source | Gain bits |
|---:|---:|---:|---:|---:|---:|---:|
| `166` | `34` | `6` | `5` | `183` | `522` | `+0.000503` |
| `171` | `36` | `1` | `10` | `890` | `1026` | `+0.000503` |

## Interpretation

This remains a fixed-recipe local source frontier. A positive result
updates the compression bound only; it does not strengthen the generation
explanation because segmentation, copy lengths, and higher-order
substitutions are still outside this gate.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- Recipe segmentation and copy lengths remain fixed.
- Triple and higher-order source substitutions are outside this gate.
