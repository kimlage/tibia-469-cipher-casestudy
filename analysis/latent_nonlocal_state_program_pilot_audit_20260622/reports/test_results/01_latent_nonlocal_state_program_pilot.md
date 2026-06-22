# Latent Nonlocal State Program Pilot

Classification: `LATENT_NONLOCAL_STATE_PILOT_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test a small hidden-state program over multistream operation tokens. This is the first pilot of the `latent_nonlocal_state_program_pilot` route.

## Summary

- Total HMM bits: `3204.220`.
- Total factorized stream bits: `5342.667`.
- Delta vs factorized: `-2138.447` bits.
- Cells beating factorized: `5/5`.
- Cells beating shuffled p05: `0/5`.

## Prefix Holdouts

| Cutoff | K | Init | Test ops | HMM bits | Factorized bits | Delta | Beats shuffle p05 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| `20` | `6` | `book_phase` | `182` | `1108.131` | `1967.359` | `-859.228` | `False` |
| `30` | `6` | `position` | `140` | `918.782` | `1523.485` | `-604.703` | `False` |
| `40` | `6` | `position` | `95` | `645.193` | `1033.825` | `-388.632` | `False` |
| `50` | `6` | `position` | `56` | `387.374` | `600.874` | `-213.501` | `False` |
| `60` | `6` | `position` | `20` | `144.740` | `217.123` | `-72.383` | `False` |

## Decision

The small latent-state program is promoted only if it beats the factorized stream model and same-multiset order controls under holdout. Otherwise the route remains open but requires richer state than this HMM pilot.
