# Boundary Candidate Trigger Gate

Classification: `boundary_candidate_trigger_clue_promoted`
Translation delta: `NONE`

## Purpose

Test whether known operation starts can be replaced by the promoted
`right_ge:4` boundary candidate set, with a three-way label policy for
`nonstart`, `literal`, and `copy`.

## Summary

- Candidate policy: `right_ge:4`.
- Candidate positions: `995`.
- Candidate nonstarts/literal/copy: `841` / `29` / `125`.
- Canonical op starts/literal/copy: `261` / `53` / `208`.
- Best overall feature: `book_start_x_copy_available`.
- Best overall cutoff: `20`.
- Best overall exact candidates: `745/819`.
- Best overall start hits: `46/120`.
- Best overall saving vs three-way lookup: `116.856` bits.
- Best global exact candidates: `140/153`.
- Best global start hits: `0`.
- Best global saving vs three-way lookup: `-6.715` bits.
- Best feature over global: `book_start_x_copy_available`.
- Best feature cutoff: `20`.
- Best feature exact candidates: `745/819`.
- Best feature start hits: `46/120`.
- Best feature literal/copy hits: `4` / `42`.
- Best feature predicted starts: `50`.
- Best feature errors: `74`.
- Best feature saving vs lookup: `116.856` bits.
- Same-cutoff global exact/start hits: `699` / `0`.
- Same-cutoff global saving vs lookup: `-52.636` bits.
- Best feature delta vs global: `169.492` bits.
- Best feature start-hit delta vs global: `46`.
- Random delta bits p95: `-6.870`.
- Random start-hit delta p95: `0.000`.
- Promotes boundary candidate trigger: `True`.
- Weak boundary candidate trigger: `False`.

This gate replaces granted operation starts with the previously promoted right_ge:4 boundary candidate set, then asks whether target-conditioned copy availability and boundary features can separate nonstarts, literal starts, and copy starts under prefix holdout.

## Best Rows

| Cutoff | Feature | Exact | Start hits | Lit/Copy hits | Pred starts | Errors | Saving | Delta bits | Delta starts | Contexts |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `book_start_x_copy_available` | `745/819` | `46/120` | `4/42` | `50` | `74` | `116.856` | `169.492` | `46` | `4` |
| `30` | `book_start_x_copy_available` | `638/695` | `37/94` | `3/34` | `40` | `57` | `96.951` | `139.531` | `37` | `4` |
| `30` | `book_start` | `635/695` | `34/94` | `0/34` | `40` | `60` | `86.823` | `129.403` | `34` | `2` |
| `30` | `target_start_bucket` | `635/695` | `34/94` | `0/34` | `40` | `60` | `80.483` | `123.064` | `34` | `6` |
| `40` | `book_start_x_copy_available` | `507/547` | `27/67` | `2/25` | `30` | `40` | `79.039` | `103.592` | `27` | `4` |
| `40` | `book_start` | `505/547` | `25/67` | `0/25` | `30` | `42` | `72.990` | `97.543` | `25` | `2` |
| `40` | `target_start_bucket` | `505/547` | `25/67` | `0/25` | `30` | `42` | `66.650` | `91.203` | `25` | `6` |
| `20` | `surprisal_x_copy_available` | `724/819` | `38/120` | `3/35` | `55` | `95` | `20.914` | `73.550` | `38` | `10` |
| `50` | `book_start_x_copy_available` | `334/355` | `18/39` | `1/17` | `20` | `21` | `49.961` | `69.826` | `18` | `4` |
| `20` | `surprisal_bucket` | `721/819` | `35/120` | `0/35` | `55` | `98` | `17.145` | `69.781` | `35` | `5` |
| `50` | `book_start` | `333/355` | `17/39` | `0/17` | `20` | `22` | `48.207` | `68.072` | `17` | `2` |
| `50` | `target_start_bucket` | `333/355` | `17/39` | `0/17` | `20` | `22` | `41.867` | `61.732` | `17` | `6` |

## Decision

- A boundary-candidate trigger policy is promoted only if a non-global feature beats the nonstart-majority baseline and shuffled-label controls after table/correction cost.
- This gate removes the exact op-start grant only partially: it still grants a target-derived candidate set and target-conditioned copy availability.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
