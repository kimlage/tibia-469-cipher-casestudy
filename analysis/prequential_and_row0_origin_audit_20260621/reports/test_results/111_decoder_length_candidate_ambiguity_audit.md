# Decoder Length Candidate Ambiguity Audit

Classification: `decoder_length_candidates_ambiguous_dependency_retained`
Translation delta: `NONE`

## Purpose

Gate 110 showed that the length atlas remains the blocker. This audit
tests a generous decoder-side question: if operation type is granted, and
copy source is also granted for copy rows, are the operation lengths
forced by syntax and remaining capacity?

## Assumptions

- Copy rows: op type and declared source are granted; candidate lengths are `min_len..decoder_max`.
- Literal rows: op type is granted and payload is unknown; candidate lengths are `1..remaining`.
- This is an ambiguity ledger, not a compression model or new formula.

## Candidate Counts

| Scope | Rows | Forced | Ambiguous | Min | Median | Mean | Max | log2 candidate space |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Copy | `208` | `4` | `204` | `1` | `86.000` | `94.413` | `278` | `1246.314` |
| Literal | `53` | `1` | `52` | `1` | `94.000` | `93.113` | `281` | `309.234` |
| All | `261` | `5` | `256` | `1` | `89.000` | `94.149` | `281` | `1555.548` |

## Declared-Length Diagnostics

- Copy declared length equals decoder max: `58/208`.
- Literal declared length equals remaining book suffix: `5/53`.
- Forced length count under generous assumptions: `5/261`.
- Ambiguous length count under generous assumptions: `256/261`.

## Decision

- Promotes length generator: `False`.
- Even under generous decoder assumptions, operation lengths are not forced. For copy operations this audit grants the declared source and op type, then counts every syntactically possible length from min_len to decoder_max. For literal operations it grants op type but not payload, so every positive remaining length is possible. The resulting candidate sets remain widely ambiguous, so the length atlas cannot be replaced by a forced decoder-side rule at this frontier.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
