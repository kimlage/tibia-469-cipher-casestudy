# Post-Target-Max Source Substitution Frontier Gate

Classification: `post_targetmax_source_substitution_frontier_improves_bound`
Translation delta: `NONE`

## Purpose

Gate 55 saturated the local target-max resegmentation frontier. This
gate asks whether that resegmentation changed the adaptive source stream
enough to reopen the exact single/pair same-chunk source-substitution
frontier. Segmentation and copy lengths remain fixed.

## Summary

- Active total bits: `8156.050355`.
- Candidate total bits: `8156.050167`.
- Candidate gain: `+0.000188` bits.
- Active copy-source bits: `2985.351748`.
- Candidate copy-source bits: `2985.351560`.
- Copy events: `261`.
- Candidate source options: `641`.
- Single substitutions searched: `380`.
- Positive singles: `1`.
- Pair substitutions searched: `71321`.
- Positive pairs: `152`.
- Best arity: `2`.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_formula_469.json](../../../authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_formula_469.json)

## Best Substitutions

| Event | Book | Op | Length | Old source | New source | Gain bits |
|---:|---:|---:|---:|---:|---:|---:|
| `201` | `46` | `2` | `112` | `699` | `1406` | `+0.000188` |
| `202` | `47` | `0` | `126` | `811` | `1518` | `+0.000188` |

## Interpretation

This is a post-resegmentation source frontier. A positive result updates
only the mechanical compression bound; it does not derive row0, change
segmentation, change copy lengths, or add semantics.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- Recipe segmentation and copy lengths remain fixed.
- Triple and higher-order source substitutions are outside this gate.
