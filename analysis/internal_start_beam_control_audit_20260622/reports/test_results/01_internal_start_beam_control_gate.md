# Internal Start Beam Control Gate

Classification: `PROMOTED_X64_INTERNAL_START_CAPACITY_CONTROLLED_CANDIDATE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Does the x64 internal-start capacity candidate beat same-multiset shuffled coarse-sequence controls under the same decoded beams?

## Summary

- Real sequence hits: `109`.
- Control sequence-hit p95: `63.000`.
- Real generated internal starts: `98`.
- Control generated-start p95: `56.000`.
- x64 capacity saving: `61.328` bits.
- Beats same-multiset controls: `True`.

## Cutoff Rows

| Cutoff | Real hits | Control p95 hits | Real starts | Control p95 starts |
| ---: | ---: | ---: | ---: | ---: |
| `20` | `31` | `19.000` | `27` | `17.000` |
| `30` | `28` | `18.000` | `27` | `18.000` |
| `40` | `24` | `16.000` | `24` | `16.000` |
| `50` | `17` | `12.000` | `15` | `10.000` |
| `60` | `9` | `7.000` | `5` | `5.000` |

## Decision

The x64 capacity candidate survives same-multiset controls. It remains a capacity-ledger candidate, not an exact generator, because misses and residual corrections are still paid.

`row0`, plaintext, translation, and `compression_bound` remain unchanged.
