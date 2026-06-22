# Event-Aligned Chunk Library Gate

Classification: `event_aligned_chunk_library_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can copy content be selected from previously emitted operation-boundary chunks, so exact length and source derive from an event-aligned span instead of from arbitrary substring addressing?

## Summary

- Best span limit: `all`.
- Selected policy: `long_recent`.
- Copy hits/misses: `6/202` out of `208`.
- Sources derived/matching raw: `6/208` / `5/208`.
- Candidate count median/mean/max on hits: `119` / `95.500` / `170`.
- V2 residual baseline: `3423.183` bits.
- Event-aligned residual: `3322.129` bits.
- Delta vs v2 residual: `-101.054` bits.
- Delta vs shuffled-boundary control: `-49.693` bits.
- Composition bits after derived lengths: `440.233`.
- Literal length delimiter bits: `153.392`.
- Top-80 copy hits: `4/208`.

## Span Modes

| Max span ops | Copy hits | Residual bits | Delta vs v2 | Top80 |
| ---: | ---: | ---: | ---: | ---: |
| `1` | `1` | `3369.170` | `-54.013` | `1` |
| `2` | `4` | `3341.232` | `-81.951` | `4` |
| `3` | `4` | `3342.632` | `-80.551` | `4` |
| `4` | `5` | `3330.614` | `-92.569` | `4` |
| `8` | `5` | `3331.928` | `-91.255` | `3` |
| `all` | `6` | `3322.129` | `-101.054` | `4` |

## Prefix Holdout

| Cutoff | Policy | Hits | Misses | Event bits | V2 bits | Delta | Top80 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `long_recent` | `6` | `149` | `2209.956` | `2303.166` | `-93.211` | `4` |
| `30` | `long_recent` | `3` | `116` | `1730.285` | `1786.763` | `-56.478` | `1` |
| `40` | `long_recent` | `3` | `77` | `1222.769` | `1274.354` | `-51.585` | `1` |
| `50` | `long_recent` | `1` | `48` | `756.861` | `774.007` | `-17.147` | `0` |
| `60` | `long_recent` | `0` | `18` | `228.190` | `234.951` | `-6.761` | `0` |

## Controls

- Random rank control observed/p05/p50/p95: `24.189` / `23.625` / `29.754` / `33.921`.
- Shuffled completed-book boundaries copy hits: `1/208`.
- Shuffled completed-book boundaries residual delta: `-51.361` bits.
- Boundary-specific delta vs shuffled control: `-49.693` bits.

## Decision

`event_aligned_chunk_library_not_promoted` as a generator. The representation sharply reduces candidate-set size for the few aligned hits, but most copy content is not a prior event span. The residual saving is mostly a length/literal refactor also visible under shuffled-boundary control, so source/length remain mostly external.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
