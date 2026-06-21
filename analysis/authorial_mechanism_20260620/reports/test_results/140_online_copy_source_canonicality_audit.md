# 140. Online Copy Source Canonicality Audit

Classification: `copy_source_canonicality_controls_confirm_earliest_rule`
Translation delta: `NONE`

## Purpose

Audit 135 showed that every declared copy source is the earliest prior
occurrence of the copied substring. This addendum adds negative controls
for that canonicality result: latest occurrence, previous-source rules,
and uniform random choice among candidate occurrences. It does not remove
source fields from the decoder and it does not search for plaintext.

## Result

- Copy ops: `261`
- Unique source-candidate ops: `123`
- Ambiguous source-candidate ops: `138`
- Earliest-occurrence hits: `261/261`
- Latest-occurrence hits: `123/261`
- Previous-source hits: `0/261`
- Previous-source-plus-length hits: `5/261`

| Measure | Value |
|---|---:|
| Candidate source count min/median/mean/max | `1` / `2` / `2.441` / `14` |
| Copy length min/median/mean/max | `5` / `18` / `39.870` / `275` |
| Random candidate expected hits | `169.473` |
| Random candidate expected hit rate | `0.649` |
| Observed earliest hit rate | `1.000` |
| log2 P(all earliest under uniform candidate choice) | `-236.596` |

## Interpretation

Every stored copy source is the earliest previous occurrence of the copied
substring at the declared length. This supports a deterministic parser
tie-break rule and removes one arbitrary-choice concern from the online
recipe.

The limit is important: this does not make the formula source-free. A
decoder still needs the copied substring, copy decision, or source-bearing
recipe information to reconstruct the book. The result is source
canonicality, not a new compression bound.

## Boundary

- No plaintext or translation is introduced.
- Row0/table origin is unchanged.
- Compression bound is unchanged.
