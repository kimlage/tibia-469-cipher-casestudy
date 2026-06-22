# Innovation Tape Structure Gate

Classification: `innovation_tape_structure_promoted`
Translation delta: `NONE`

## Purpose

Test whether the `266`-digit innovation tape has structure of its own:
coverage by seed-book substrings, coverage by prior tape substrings, or
prequential Markov digit predictability beyond shuffled same-multiset
controls.

## Summary

- Literal tape digits: `266`.
- Seed text digits: `1696`.
- Best seed min length: `2`.
- Best seed covered digits: `266`.
- Best seed control p95: `265.000`.
- Best prior-tape min length: `2`.
- Best prior-tape covered digits: `205`.
- Best prior-tape control p95: `206.000`.
- Best Markov order: `2`.
- Best Markov bits: `879.609`.
- Best Markov bpd: `3.306800`.
- Best Markov control p05: `898.869`.
- Promotes tape structure: `True`.

This gate asks whether the innovation tape itself has a mechanical source: seed-derived coverage, self-recurrence, or prequential digit structure beyond shuffled controls.

## Seed Coverage

| Min len | Covered | Literal residual | Copy items | Control p95 | Beats p95 |
| ---: | ---: | ---: | ---: | ---: | --- |
| `2` | `266` | `0` | `86` | `265.000` | `True` |
| `3` | `231` | `35` | `63` | `187.000` | `True` |
| `4` | `153` | `113` | `34` | `71.000` | `True` |
| `5` | `87` | `179` | `16` | `20.000` | `True` |

## Prior Tape Coverage

| Min len | Covered | Literal residual | Copy items | Control p95 | Beats p95 |
| ---: | ---: | ---: | ---: | ---: | --- |
| `2` | `205` | `61` | `85` | `206.000` | `False` |
| `3` | `103` | `163` | `30` | `86.000` | `True` |
| `4` | `52` | `214` | `12` | `24.000` | `True` |
| `5` | `16` | `250` | `3` | `6.000` | `True` |

## Markov Rows

| Order | Bits | Bits/digit | Control p05 | Beats p05 |
| ---: | ---: | ---: | ---: | --- |
| `0` | `904.664` | `3.400991` | `904.664` | `False` |
| `1` | `896.274` | `3.369453` | `936.488` | `True` |
| `2` | `879.609` | `3.306800` | `898.869` | `True` |

## Decision

- Tape structure is promoted only if it beats same-multiset shuffled controls.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
