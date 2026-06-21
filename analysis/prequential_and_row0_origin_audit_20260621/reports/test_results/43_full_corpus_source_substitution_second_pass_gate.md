# Full-Corpus Source Substitution Second-Pass Gate

Classification: `full_corpus_source_substitution_second_pass_improves_bound`
Translation delta: `NONE`

## Purpose

Gate 42 promoted a single/pair source-substitution improvement. This gate
reruns the exact same local frontier on the promoted `8160.827` bit formula
to test whether another single or pair same-chunk source substitution remains.
Segmentation and copy lengths remain fixed.

## Summary

- Active total bits: `8160.827`.
- Candidate total bits: `8160.826`.
- Candidate gain: `+0.001` bits.
- Active copy-source bits: `2986.348`.
- Candidate copy-source bits: `2986.348`.
- Copy events: `261`.
- Candidate source options: `637`.
- Single substitutions searched: `376`.
- Positive singles: `10`.
- Pair substitutions searched: `69849`.
- Positive pairs: `2091`.
- Best arity: `2`.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_second_pass_formula_469.json](../../../authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_second_pass_formula_469.json)

## Best Substitutions

| Event | Book | Op | Length | Old source | New source | Gain bits |
|---:|---:|---:|---:|---:|---:|---:|
| `128` | `24` | `0` | `36` | `2119` | `3413` | `+0.001` |
| `208` | `49` | `6` | `8` | `867` | `2802` | `+0.001` |

## Interpretation

This is still a fixed-recipe local frontier. It can promote another
compression-bound step only if a second-pass single or pair source
substitution survives the full adaptive source-stream rescore.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- Recipe segmentation and copy lengths remain fixed.
- Triple and higher-order source substitutions are outside this gate.
