# Schedule-State Multistream Pilot

Classification: `SCHEDULE_STATE_MULTISTREAM_CLUE_NOT_GENERATOR`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether the HMM multistream clue can be attached to visible schedule states rather than hidden order-sensitive state. Decoder-visible families are selected by prefix training only; diagnostic-conditioned families are reported separately and are not promotable as generators.

## Summary

- Selected decoder-visible schedule bits: `3559.712`.
- Factorized external stream bits: `5212.286`.
- Delta vs factorized: `-1652.574` bits.
- Delta vs joint unigram: `-57.222` bits.
- Cells beating factorized: `5/5`.
- Cells beating joint unigram: `2/5`.
- Cells beating same-book shuffled p05: `0/5`.

## Prefix Holdouts

| Cutoff | Selected family | Test ops | Schedule bits | Factorized bits | Delta | Beats shuffle p05 | Diagnostic best |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `20` | `book_phase` | `182` | `1315.878` | `1915.785` | `-599.907` | `False` | `remaining_bucket:1196.617` |
| `30` | `book_phase` | `140` | `1032.134` | `1490.818` | `-458.684` | `False` | `remaining_bucket:936.880` |
| `40` | `book_phase` | `95` | `653.528` | `1002.445` | `-348.917` | `False` | `booklen_remaining:622.107` |
| `50` | `phase_op_pos` | `56` | `410.363` | `592.033` | `-181.670` | `False` | `booklen_remaining:359.765` |
| `60` | `phase_op_pos` | `20` | `147.810` | `211.206` | `-63.396` | `False` | `booklen_remaining:132.290` |

## Decision

This gate promotes only if decoder-visible schedule states reduce the external ledger under holdout and beat same-book shuffled controls. Diagnostic-conditioned wins are useful localization clues only, because they grant exact remaining/target-position structure.
