# Innovation Tape Schedule Gate

Classification: `innovation_tape_schedule_sparsity_weak_clue`
Translation delta: `NONE`

## Purpose

Test whether per-book consumption counts for the innovation tape can be
predicted from online mechanical features rather than declared as an
external schedule.

## Summary

- Literal tape digits: `266`.
- Books with literal digits: `25`.
- Best feature: `global_majority`.
- Best cutoff: `20`.
- Best exact books: `33/50`.
- Best absolute error: `126`.
- Best baseline bits: `360.527`.
- Best total bits: `138.683`.
- Best saving vs baseline: `221.844`.
- Best global-majority exact books: `33/50`.
- Best global-majority saving: `221.844`.
- Best feature over global: `book_decade`.
- Best feature delta bits: `-5.585`.
- Best feature delta exact: `0`.
- Random exact p95: `31.000`.
- Promotes schedule model: `False`.
- Weak schedule clue: `True`.

This gate asks whether the per-book innovation tape consumption schedule can be predicted from online mechanical features beyond a global zero-consumption/sparsity baseline.

## Best Rows

| Cutoff | Feature | Exact | Baseline bits | Total bits | Saving | Abs error | Contexts |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `global_majority` | `33/50` | `360.527` | `138.683` | `221.844` | `126` | `0` |
| `20` | `book_decade` | `33/50` | `360.527` | `144.268` | `216.259` | `126` | `1` |
| `20` | `greedy_residual_bucket` | `33/50` | `360.527` | `166.608` | `193.919` | `85` | `5` |
| `30` | `global_majority` | `26/40` | `291.567` | `115.620` | `175.948` | `97` | `0` |
| `30` | `book_decade` | `26/40` | `291.567` | `126.790` | `164.778` | `97` | `2` |
| `30` | `greedy_residual_bucket` | `26/40` | `291.567` | `143.544` | `148.023` | `69` | `5` |
| `40` | `global_majority` | `20/30` | `219.641` | `84.573` | `135.068` | `82` | `0` |
| `40` | `book_decade` | `20/30` | `219.641` | `101.328` | `118.313` | `82` | `3` |
| `20` | `length_x_greedy` | `27/50` | `360.527` | `243.313` | `117.214` | `155` | `9` |
| `50` | `global_majority` | `14/20` | `146.976` | `51.771` | `95.205` | `45` | `0` |

## Decision

- A schedule feature is promoted only if it improves over global-majority sparsity and beats random exact controls.
- Global sparsity may be retained as a weak clue but does not generate the transducer by itself.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
