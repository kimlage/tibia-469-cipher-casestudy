# Hierarchical Reference Formula Compile

Verdict: `hierarchical_reference_formula_roundtrips_no_semantics`. Translation delta: `NONE`.

This compiler combines the controlled literal-reference recipe layer with
the tape-inventory self-reference layer. The decoder first reconstructs
the 16 tape components from literal runs and self-references, then renders
all 70 books from the existing component slice/span/reference recipes.

## Rough Cost Ladder

| Model | Rough total bits | Gain vs previous |
|---|---:|---:|
| Base module formula | `24350.7` | `0.0` |
| Tape formula | `17753.5` | `6597.1` |
| Literal-reference formula | `16586.1` | `1167.4` |
| Hierarchical reference formula | `13858.5` | `2727.7` |

## Validation

- Component roundtrip: `16/16`.
- Book roundtrip: `70/70`.

## Boundary

This is the current strongest mechanical book-generation formula in this
front. It remains a generator/compression result only: no plaintext, no
pair-table origin, and no authorial-intent claim are promoted.
