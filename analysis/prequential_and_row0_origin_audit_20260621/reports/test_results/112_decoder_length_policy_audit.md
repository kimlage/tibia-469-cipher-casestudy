# Decoder Length Policy Audit

Classification: `simple_length_candidate_policies_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 111 showed that operation lengths remain ambiguous even after
granting op type and copy source. This audit tests whether fixed
decoder-side policies over those candidate sets recover the declared
length sequence.

## Policy Scoreboard

| Policy | Hits | Copy hits | Literal hits | Promoted |
|---|---:|---:|---:|---|
| `max_candidate` | `63/261` | `58/208` | `5/53` | `False` |
| `previous_length_else_max` | `51/261` | `40/208` | `11/53` | `False` |
| `previous_length_else_min` | `33/261` | `22/208` | `11/53` | `False` |
| `previous_length_else_median` | `32/261` | `21/208` | `11/53` | `False` |
| `min_candidate` | `15/261` | `7/208` | `8/53` | `False` |
| `median_candidate` | `11/261` | `9/208` | `2/53` | `False` |
| `q75_candidate` | `9/261` | `7/208` | `2/53` | `False` |
| `q25_candidate` | `8/261` | `5/208` | `3/53` | `False` |

## Declared Position Diagnostics

- Forced rows: `5`.
- Declared min hits: `10`.
- Declared max hits: `58`.
- Declared lower-quarter rows: `131`.
- Declared upper-quarter rows: `73`.
- Mean normalized candidate position: `0.389953`.

## Decision

- Best policy: `max_candidate` = `63/261`.
- Promotes length policy: `False`.
- Fixed decoder-side length policies do not explain the length sequence. The best tested policy is only a partial boundary diagnostic, not a generator: declared lengths are spread across candidate sets rather than being consistently min, max, median, quartile, or previous-length choices. Length selection remains a retained parser objective.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
