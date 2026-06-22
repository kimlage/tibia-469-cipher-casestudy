# Internal Start Beam Capacity Gate

Classification: `PROMOTED_INTERNAL_START_CAPACITY_LEDGER_REDUCTION_CANDIDATE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Did the target-free internal-start program fail because the book-level controller beam was too narrow, or because the controller still lacks the right generative ranking/state?

## Summary

- Best controller pair: `book_length__op_count`.
- Best width by hits: `x64`.
- Best width by paid cost: `x64`.
- Max sequence hits: `109`.
- Max generated internal starts before correction: `98`.
- Coverage improved over baseline: `True`.
- Paid reduction vs explicit opcount+cutpoint+type: `True`.

## Capacity Curve

| Width | Seq beam | Book beam | Sequence hits | Generated starts | Program bits | Correction bits | Saving vs start+type |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `baseline` | `12` | `30` | `56/150` | `13/343` | `3149.385` | `1896.024` | `-337.712` |
| `x2` | `24` | `60` | `64/150` | `21/343` | `3092.766` | `1806.665` | `-281.093` |
| `x4` | `48` | `120` | `82/150` | `42/343` | `2956.469` | `1594.851` | `-144.796` |
| `x8` | `96` | `240` | `86/150` | `48/343` | `2931.223` | `1543.002` | `-119.550` |
| `x16` | `192` | `480` | `92/150` | `60/343` | `2883.017` | `1454.472` | `-71.345` |
| `x32` | `384` | `960` | `101/150` | `78/343` | `2815.905` | `1321.678` | `-4.232` |
| `x64` | `768` | `1920` | `109/150` | `98/343` | `2750.345` | `1189.299` | `61.328` |

## Decision

A wider beam reduces the paid ledger and should be promoted only as a capacity-ledger candidate unless it also reaches exact coverage. The remaining misses still require explicit corrections.

Boundary: larger beams test capacity only; paid ledger reduction promotes a candidate, while exact generator status still requires exact coverage without residual sequence corrections.

`row0`, plaintext, translation, and `compression_bound` remain unchanged.
