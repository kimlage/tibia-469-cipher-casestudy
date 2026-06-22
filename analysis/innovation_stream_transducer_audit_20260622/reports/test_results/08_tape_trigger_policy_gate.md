# Tape Trigger Policy Gate

Classification: `conditional_tape_trigger_clue_promoted`
Translation delta: `NONE`

## Purpose

Test whether literal-vs-copy trigger decisions can be predicted at
known operation starts using true-prefix, target-conditioned copy
availability features. This is explicitly not a closed-loop generator.

## Summary

- Operation starts: `261`.
- Literal ops: `53`.
- Copy ops: `208`.
- Literal ops with no copy available: `36`.
- Literal ops despite copy availability: `17`.
- Best overall feature: `copy_available`.
- Best overall cutoff: `20`.
- Best overall exact ops: `172/182`.
- Best overall saving vs literal-site lookup: `48.262` bits.
- Best global exact ops: `155/182`.
- Best global saving vs literal-site lookup: `0.000` bits.
- Best feature over global: `copy_available`.
- Best feature cutoff: `20`.
- Best feature exact ops: `172/182`.
- Best feature literal hits: `17/27`.
- Best feature errors: `10`.
- Best feature saving vs lookup: `48.262` bits.
- Best feature delta vs global: `48.262` bits.
- Best feature exact delta vs global: `17`.
- Random delta bits p95: `-5.459`.
- Random delta exact p95: `0.000`.
- Random exact p95: `150.000`.
- Promotes conditional trigger clue: `True`.
- Weak conditional trigger clue: `False`.

This gate asks whether the literal/copy trigger can be predicted at known operation starts under true-prefix, target-conditioned copy availability. It is a dependency-reduction test for op type, not a closed-loop generator or skeleton derivation.

## Best Rows

| Cutoff | Feature | Exact | Literals hit | Errors | Lookup bits | Total bits | Saving | Delta bits | Delta exact | Contexts |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `copy_available` | `172/182` | `17/27` | `10` | `106.645` | `58.383` | `48.262` | `48.262` | `17` | `2` |
| `20` | `maxcopy_bucket` | `172/182` | `17/27` | `10` | `106.645` | `63.383` | `43.262` | `43.262` | `17` | `7` |
| `20` | `start_x_copy_available` | `172/182` | `17/27` | `10` | `106.645` | `67.383` | `39.262` | `39.262` | `17` | `11` |
| `30` | `copy_available` | `132/140` | `13/21` | `8` | `81.967` | `46.901` | `35.066` | `35.066` | `13` | `2` |
| `30` | `maxcopy_bucket` | `132/140` | `13/21` | `8` | `81.967` | `51.901` | `30.066` | `30.066` | `13` | `7` |
| `20` | `copy_available_x_age` | `169/182` | `14/27` | `13` | `106.645` | `76.892` | `29.754` | `29.754` | `14` | `9` |
| `20` | `next_tape_match` | `166/182` | `27/27` | `16` | `106.645` | `80.355` | `26.291` | `26.291` | `11` | `2` |
| `30` | `start_x_copy_available` | `132/140` | `13/21` | `8` | `81.967` | `55.901` | `26.066` | `26.066` | `13` | `11` |
| `40` | `copy_available` | `90/95` | `10/15` | `5` | `56.615` | `31.248` | `25.368` | `25.368` | `10` | `2` |
| `20` | `copy_available_x_tape_match` | `166/182` | `27/27` | `16` | `106.645` | `81.355` | `25.291` | `25.291` | `11` | `3` |
| `40` | `copy_available_x_tape_match` | `90/95` | `10/15` | `5` | `56.615` | `32.248` | `24.368` | `24.368` | `10` | `3` |
| `40` | `maxcopy_bucket` | `90/95` | `10/15` | `5` | `56.615` | `36.248` | `20.368` | `20.368` | `10` | `7` |

## Decision

- A trigger policy is promoted only if a non-global feature beats the global copy-majority baseline and shuffled-label controls after table/correction cost.
- The promoted clue is conditional on known operation starts and target-conditioned copy availability.
- It reduces the declared literal/copy trigger dependency under those grants, but does not derive the skeleton, source, length, or closed-loop digit stream.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
