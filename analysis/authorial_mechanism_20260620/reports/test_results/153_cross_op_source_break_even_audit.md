# 153. Cross-Op Source Break-Even Audit

Classification: `cross_op_source_break_even_blocks_promotion`
Translation delta: `NONE`

## Purpose

Audit 152 showed that the best cross-op literal repair loses by only
`0.027` bits, mostly because of copy-source cost. This audit quantifies
the break-even source cost and checks whether the selected source is an
ordinary candidate or an earliest full-length occurrence.

## Candidate Source Context

- Book/op/pos: `12` / `8` / `82`
- Source/copy length: `102` / `11`
- Candidate sources at position: `7`
- Full-length sources for this copy length: `2`
- Selected source is earliest full-length source: `True`

Full-length sources:

| Source | Max length |
|---:|---:|
| `102` | `11` |
| `1803` | `11` |

## Break-Even Ledger

- Active delta: `0.027434` bits
- Active copy-source delta: `11.236537` bits
- Non-source delta: `-11.209104` bits
- Break-even copy-source delta: `11.209104` bits
- Source margin over break-even: `0.027434` bits
- No-source oracle delta: `-11.209104` bits
- No-source/no-length oracle delta: `-12.847767` bits

## Interpretation

The candidate would improve under a non-decodable source-free oracle,
but the active ledger must still identify the copied source. The
selected source is the earliest full-length occurrence, which is a
useful encoder-side clue, but not a decoder-side derivation of the
copied text. The real active source cost is only `0.027` bits above
break-even, so this is a tight mechanical frontier rather than a
promotable formula.

## Decision

- Compression bound unchanged.
- Source-free oracle not promoted.
- Candidate not promoted.
- Row0 origin, plaintext, and semantic status unchanged.
