# Active Formula Dependency Refresh Gate

Classification: `active_formula_dependency_refresh_no_structural_dependency_reduction`
Translation delta: `NONE`

## Purpose

Gate 48 mapped dependencies on the source-substitution fourth-pass
formula. This refresh repeats the dependency count on the active
post-target-max formula frozen by the stop audit. It does not search
for another compression improvement.

## Formula Comparison

| Formula | Total bits | Literal ops | Copy ops | Literal digits | Copied digits | Declared recipe dependency fields | Roundtrip |
|---|---:|---:|---:|---:|---:|---:|---:|
| previous source-substitution fourth pass | `8160.825608` | `87` | `261` | `857` | `10406` | `609` | `70/70` |
| active post-target-max second-pass formula | `8156.049986` | `87` | `261` | `856` | `10407` | `609` | `70/70` |

## Dependency Rows

| Dependency | Previous units | Active units | Delta | Status |
|---|---:|---:|---:|---|
| `literal_payload` | `87` | `87` | `+0` | `unchanged_declared_dependency` |
| `copy_source` | `261` | `261` | `+0` | `unchanged_declared_dependency` |
| `copy_length` | `261` | `261` | `+0` | `unchanged_declared_dependency` |

## Result

- Bound gain versus the gate-48 formula: `4.775621` bits.
- Declared recipe dependency delta: `+0` fields.
- Literal digit delta: `-1`.
- Copied digit delta: `+1`.
- Interpretation: Target-max resegmentation and post-target-max source substitutions move one digit from literal payload into copied payload, but they do not reduce the number of declared literal, source, or length fields.
- Mainline implication: The active bound improves, but the structural explanation gap is unchanged at the dependency-count level. A future improvement must derive source/length fields or row0 rather than only reprice them.

## Decision

- Current compression bound remains `8156.049986` bits.
- The target-max/source-substitution path improves the bound but does not reduce declared recipe dependency fields.
- The next mainline test remains structural source/length derivation or row0-origin evidence.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- No new book-generation formula is emitted.
- No additional source-substitution pass is searched.
