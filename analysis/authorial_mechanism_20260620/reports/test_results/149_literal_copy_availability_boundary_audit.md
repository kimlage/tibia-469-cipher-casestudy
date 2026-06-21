# 149. Literal Copy Availability Boundary Audit

Classification: `literal_items_mostly_forced_with_residual_parser_choices`
Translation delta: `NONE`

## Purpose

The active online formula still declares literal payload text. This audit
separates literal operations that are mechanically forced by no legal
`min_len` copy candidate from residual parser choices where a copy was
available but the deterministic cost parser chose literal text.

## Summary

- Literal items: `87`
- Copy items: `261`
- Literal digits: `857`
- Forced literal items with no copy candidate at start: `73`
- Optional literal items with copy candidate at start: `14`
- Forced literal digits with no copy candidate at digit position: `760`
- Optional literal digits with copy candidate at digit position: `97`
- Short-suffix literal digits: `43`
- Optional literal items shorter than `min_len`: `9`
- Optional literal items where an available copy covers the literal length: `11`

## Optional Literal Starts

| Book | Op | Pos | Literal len | Candidates | Max copy len | Preview |
|---:|---:|---:|---:|---:|---:|---|
| `8` | `4` | `103` | `19` | `4` | `5` | `4519121128883046467` |
| `12` | `0` | `0` | `2` | `12` | `6` | `56` |
| `12` | `8` | `82` | `4` | `7` | `11` | `1972` |
| `16` | `6` | `144` | `7` | `9` | `6` | `6512887` |
| `17` | `3` | `149` | `4` | `7` | `7` | `0364` |
| `25` | `0` | `0` | `3` | `16` | `7` | `219` |
| `30` | `1` | `17` | `6` | `17` | `6` | `800364` |
| `32` | `1` | `11` | `2` | `1` | `9` | `40` |
| `38` | `1` | `112` | `2` | `10` | `5` | `51` |
| `39` | `0` | `0` | `7` | `1` | `5` | `5765219` |
| `42` | `3` | `89` | `2` | `10` | `5` | `19` |
| `44` | `0` | `0` | `5` | `27` | `18` | `21972` |
| `52` | `0` | `0` | `3` | `59` | `21` | `895` |
| `58` | `1` | `24` | `3` | `6` | `23` | `464` |

## Interpretation

Most literal runs are not arbitrary parser choices: `73/87` literal
items start where no legal copy candidate exists, covering `788/857`
literal payload digits at the item level. At digit granularity,
`760/857` literal digits are emitted at positions with no legal
copy candidate. The residual externality is therefore localized to
`14` literal starts and `97` literal digit positions where copy
availability exists but the cost parser still chooses literal text.

The residual optional set is not promoted as a source of semantics.
It is a mechanical parser/cost frontier: replacing these literals
requires a charged recipe repair that preserves roundtrip and beats
the active ledger.

## Decision

- Literal recipe externality is reduced but not removed.
- Compression bound unchanged.
- Row0 origin, plaintext, and semantic status unchanged.
