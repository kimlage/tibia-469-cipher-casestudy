# Start Candidate Ranking Gate

Classification: `START_CANDIDATE_RANKING_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether decoder-visible prefix/content scores can produce a candidate set that reduces the cost of declaring internal starts.

## Summary

- Candidate bits: `1941.433`.
- Exact start composition baseline bits: `2063.661`.
- Delta vs baseline: `-122.227` bits.
- Cells beating random top-K p05: `2/5`.
- Candidate positions selected: `1954`.
- Start hits: `37/343`.
- Misses requiring correction: `306`.
- Recall: `0.108`.

## Prefix Holdouts

| Cutoff | Family | Rate | K | Hits | Misses | Candidate bits | Baseline bits | Delta | Random p05 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `20` | `suffix4_seen` | `0.080` | `632` | `14` | `118` | `728.812` | `775.501` | `-46.689` | `True` |
| `30` | `suffix4_seen` | `0.080` | `528` | `11` | `89` | `563.836` | `598.810` | `-34.975` | `True` |
| `40` | `global` | `0.080` | `401` | `5` | `60` | `374.125` | `395.378` | `-21.253` | `False` |
| `50` | `suffix4_seen` | `0.080` | `277` | `5` | `31` | `215.315` | `229.691` | `-14.376` | `False` |
| `60` | `suffix4_seen` | `0.080` | `116` | `2` | `8` | `59.346` | `64.281` | `-4.935` | `False` |

## Decision

Promotion requires candidate+miss-correction bits below the exact composition baseline and random top-K controls. Candidate enrichment without net cost reduction remains a diagnostic clue only.
