# Markov Chunk-Content Prior Gate

Classification: `MARKOV_CHUNK_CONTENT_PRIOR_REJECTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether the promoted `prev2` target-digit clue helps rank same-length copy chunk candidates as target continuations under prefix holdout.

## Summary

- Copy ops: `208`.
- Content-first Markov beats frequency/recency cells: `0/5`.
- Content-first Markov beats random p05 cells: `3/5`.
- Markov as frequency/recency tie-breaker beats baseline cells: `0/5`.
- Aggregate frequency/recency bits: `3998.858`.
- Aggregate best content-first Markov bits: `4244.687`.
- Aggregate content-first delta: `245.829` bits.
- Aggregate Markov-tie-breaker delta: `0.000` bits.

## Prefix Holdouts

| Cutoff | Copy ops | Best content-first policy | Content bits | Freq/recency bits | Delta | Beats random p05 |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| `20` | `155` | `markov_likely` | `1492.593` | `1434.174` | `58.419` | `True` |
| `30` | `119` | `markov_likely_freq_recent` | `1195.553` | `1114.375` | `81.178` | `True` |
| `40` | `80` | `markov_likely` | `840.297` | `774.952` | `65.345` | `False` |
| `50` | `49` | `markov_likely` | `513.392` | `491.769` | `21.624` | `True` |
| `60` | `18` | `markov_likely` | `202.852` | `183.590` | `19.263` | `False` |

## Decision

The `prev2` digit-content clue remains useful for digit and boundary statistics, but it does not improve same-length copy-chunk selection over frequency/recency. It is not promoted as a chunk-origin program.
