# Post-Target-Max Source Substitution Second-Pass Gate

Classification: `post_targetmax_source_substitution_second_pass_improves_bound`
Translation delta: `NONE`

## Purpose

Gate 56 found a microscopic post-target-max source-substitution pair.
This gate reruns the exact single/pair same-chunk source frontier on
that promoted formula to test whether the post-target-max source path
is saturated. Segmentation and copy lengths remain fixed.

## Summary

- Active total bits: `8156.050167`.
- Candidate total bits: `8156.049986`.
- Candidate gain: `+0.000181` bits.
- Active copy-source bits: `2985.351560`.
- Candidate copy-source bits: `2985.351380`.
- Copy events: `261`.
- Candidate source options: `641`.
- Single substitutions searched: `380`.
- Positive singles: `1`.
- Pair substitutions searched: `71321`.
- Positive pairs: `151`.
- Best arity: `2`.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_formula_469.json](../../../authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_formula_469.json)

## Best Substitutions

| Event | Book | Op | Length | Old source | New source | Gain bits |
|---:|---:|---:|---:|---:|---:|---:|
| `206` | `49` | `3` | `17` | `864` | `5129` | `+0.000181` |
| `212` | `49` | `11` | `5` | `2053` | `5124` | `+0.000181` |

## Interpretation

This is a fixed-recipe local source frontier. A positive result updates
only the mechanical compression bound; a closed result would freeze
this post-target-max source path under single/pair substitutions.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- Recipe segmentation and copy lengths remain fixed.
- Triple and higher-order source substitutions are outside this gate.
