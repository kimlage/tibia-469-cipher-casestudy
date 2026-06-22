# Internal Start Beam Capacity Gate

Classification: `WEAK_BEAM_CAPACITY_ROUTE_RETAINED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Did the target-free internal-start program fail because the book-level controller beam was too narrow, or because the controller still lacks the right generative ranking/state?

## Summary

- Best controller pair: `book_length__op_count`.
- Best width by hits: `x32`.
- Best width by paid cost: `x32`.
- Max sequence hits: `101`.
- Max generated internal starts before correction: `78`.
- Coverage improved over baseline: `True`.
- Paid reduction vs explicit opcount+cutpoint+type: `False`.

## Capacity Curve

| Width | Seq beam | Book beam | Sequence hits | Generated starts | Program bits | Correction bits | Saving vs start+type |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `baseline` | `12` | `30` | `56/150` | `13/343` | `3149.163` | `1896.024` | `-337.490` |
| `x2` | `24` | `60` | `64/150` | `21/343` | `3092.543` | `1806.665` | `-280.871` |
| `x4` | `48` | `120` | `82/150` | `42/343` | `2956.246` | `1594.851` | `-144.573` |
| `x8` | `96` | `240` | `86/150` | `48/343` | `2931.000` | `1543.002` | `-119.327` |
| `x16` | `192` | `480` | `92/150` | `60/343` | `2882.795` | `1454.472` | `-71.122` |
| `x32` | `384` | `960` | `101/150` | `78/343` | `2815.682` | `1321.678` | `-4.010` |

## Decision

Wider beams increase coverage, but not enough to reduce the paid ledger. This keeps the route alive only as a weak capacity clue; the missing piece is ranking/state, not just beam width.

Boundary: larger beams test capacity only; promotion still requires paid ledger reduction, not more covered examples.

`row0`, plaintext, translation, and `compression_bound` remain unchanged.
