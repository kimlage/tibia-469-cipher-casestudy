# 121. Prequential Component Ablation Audit

Classification: `prequential_component_ablation_simplifies_generation_explanation`
Translation delta: `NONE`

## Purpose

This audit asks which learned components of the active book generator
generalize under prefix holdout and which ones are better treated as
compression-bound detail. It compares the active contexts against simpler
variants on the same train cutoffs used by audit 118.

Lower total `vs uniform` values are better because they save more bits
across all five prefix holdouts.

## Component Summary

| Component | Active variant | Best online | Best frozen | Active online total | Best online total | Active frozen total | Best frozen total |
|---|---|---|---|---:|---:|---:|---:|
| `copy_length` | `active_midpoint` | `active_midpoint` | `active_midpoint` | `-42.214` | `-42.214` | `-34.385` | `-34.385` |
| `literal_payload` | `active_order2` | `order1_previous_digit` | `order1_previous_digit` | `-95.467` | `-111.953` | `-75.227` | `-106.042` |
| `item_type` | `active_split6_prev1` | `split6_only` | `split6_only` | `-198.802` | `-203.013` | `-151.482` | `-159.027` |

## Interpretation

The active compression formula remains the `8561.792` bit bound. This
audit does not lower that bound. Its job is to keep the generation
explanation honest: if a simpler context predicts holdouts better than
the active context, the active context should be described as a
compression-bound refinement rather than a robust authorial mechanism.

## Boundary

- No row0/table origin formula is promoted.
- No plaintext, glossary, or authorial-intent claim is introduced.
- `translation_delta`: `NONE`.
