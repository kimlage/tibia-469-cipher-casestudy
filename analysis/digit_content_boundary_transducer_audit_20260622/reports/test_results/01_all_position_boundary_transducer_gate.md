# All-Position Digit Boundary Transducer Gate

Classification: `WEAK_DIGIT_BOUNDARY_CLUE_NOT_GENERATOR`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test the selected digit-level content/boundary route without granting the operation-token sequence, exact internal starts, or target-conditioned copy availability. Every internal digit position is labeled as `nonstart`, `literal`, or `copy`.

## Summary

- Model bits: `3075.566`.
- Global label bits: `3106.596`.
- Composition baseline bits: `2160.605`.
- Delta vs global: `-31.030` bits.
- Delta vs composition: `914.961` bits.
- Cells beating composition: `0/5`.
- Cells beating shuffled-label p05: `4/5`.
- Actual start labels: `343`.
- Predicted start labels: `0`.

## Prefix Holdouts

| Cutoff | Family | Positions | Model bits | Composition bits | Delta | Shuffle p05 | Predicted starts |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| `20` | `suffix4_seen` | `7875` | `1173.142` | `813.457` | `359.684` | `True` | `0` |
| `30` | `suffix4_seen` | `6587` | `874.112` | `627.816` | `246.296` | `True` | `0` |
| `40` | `suffix4_seen` | `5029` | `584.021` | `416.799` | `167.222` | `True` | `0` |
| `50` | `suffix4_seen` | `3469` | `339.748` | `238.253` | `101.495` | `True` | `0` |
| `60` | `suffix4_seen` | `1449` | `104.543` | `64.281` | `40.263` | `False` | `0` |

## Decision

Promotion requires reducing the true-count composition baseline and beating shuffled-label controls. Beating only global/nonstart-heavy coding is not enough to reduce the internal-start dependency.
