# Internal Boundary Candidate Trigger Decomposition Gate

Classification: `internal_boundary_candidate_trigger_rejected`
Translation delta: `NONE`

## Purpose

Test whether the promoted boundary-candidate trigger clue explains
internal operation starts after removing book-start candidates.
Target-conditioned copy availability is still allowed in this gate.

## Summary

- Candidate policy: `right_ge:4`.
- Internal candidate positions: `935`.
- Internal starts/literal/copy: `94` / `16` / `78`.
- Best overall feature: `global_majority`.
- Best overall cutoff: `60`.
- Best overall exact candidates: `140/143`.
- Best overall start hits: `0/3`.
- Best overall saving vs three-way lookup: `-3.000` bits.
- Best global exact/start hits: `140/143` / `0`.
- Best global saving vs three-way lookup: `-3.000` bits.
- Best feature over global: `book_start`.
- Best feature cutoff: `20`.
- Best feature exact candidates: `699/769`.
- Best feature start hits: `0/70`.
- Best feature literal/copy hits: `0` / `0`.
- Best feature predicted starts: `0`.
- Best feature errors: `70`.
- Best feature saving vs lookup: `-39.365` bits.
- Best feature delta vs global: `-5.285` bits.
- Best feature start-hit delta vs global: `0`.
- Random delta bits p95: `-5.285`.
- Random start-hit delta p95: `0.000`.
- All-candidate trigger delta bits: `169.492`.
- Book-start dominance delta bits: `169.492`.
- Promotes internal boundary candidate trigger: `False`.
- Weak internal boundary candidate trigger: `False`.

This gate removes book-start candidates from the promoted boundary-candidate trigger test while retaining target-conditioned copy availability. It asks whether the composed clue actually explains internal operation starts.

## Best Rows

| Cutoff | Feature | Exact | Start hits | Lit/Copy hits | Pred starts | Errors | Saving | Delta bits | Delta starts | Contexts |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `global_majority` | `699/769` | `0/70` | `0/0` | `0` | `70` | `-34.080` | `0.000` | `0` | `0` |
| `30` | `global_majority` | `601/655` | `0/54` | `0/0` | `0` | `54` | `-26.600` | `0.000` | `0` | `0` |
| `40` | `global_majority` | `480/517` | `0/37` | `0/0` | `0` | `37` | `-13.704` | `0.000` | `0` | `0` |
| `50` | `global_majority` | `316/335` | `0/19` | `0/0` | `0` | `19` | `-11.582` | `0.000` | `0` | `0` |
| `60` | `global_majority` | `140/143` | `0/3` | `0/0` | `0` | `3` | `-3.000` | `0.000` | `0` | `0` |
| `20` | `book_start` | `699/769` | `0/70` | `0/0` | `0` | `70` | `-39.365` | `-5.285` | `0` | `1` |
| `30` | `book_start` | `601/655` | `0/54` | `0/0` | `0` | `54` | `-31.885` | `-5.285` | `0` | `1` |
| `60` | `book_start` | `140/143` | `0/3` | `0/0` | `0` | `3` | `-8.285` | `-5.285` | `0` | `1` |
| `40` | `book_start` | `480/517` | `0/37` | `0/0` | `0` | `37` | `-18.990` | `-5.285` | `0` | `1` |
| `50` | `book_start` | `316/335` | `0/19` | `0/0` | `0` | `19` | `-16.868` | `-5.285` | `0` | `1` |
| `20` | `copy_available` | `699/769` | `0/70` | `0/0` | `0` | `70` | `-40.950` | `-6.870` | `0` | `2` |
| `20` | `book_start_x_copy_available` | `699/769` | `0/70` | `0/0` | `0` | `70` | `-40.950` | `-6.870` | `0` | `2` |

## Decision

- Internal boundary-candidate trigger is not promoted unless a non-global feature beats the internal nonstart-majority baseline and shuffled-label controls after table/correction cost.
- Under current features, even target-conditioned copy availability does not recover internal operation starts once book-start candidates are removed.
- The previously promoted boundary-candidate trigger clue is therefore book-start dominated.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
