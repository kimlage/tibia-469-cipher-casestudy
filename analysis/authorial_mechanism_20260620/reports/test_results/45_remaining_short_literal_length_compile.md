# Remaining-Short Literal-Length Compile

Verdict: `controlled_remaining_short_literal_length_improvement`. Translation delta: `NONE`.

This audit keeps the current remaining-force item-type sequential LZ
recipe fixed and retells only literal-run length costs. When fewer than
`min_len` digits remain in a declared book, the item type is already
forced to literal; that literal must consume the remaining book suffix.
The audit charges an explicit one-bit rule for that deterministic
literal length.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8953.9` |
| Forced-length formula bits | `8922.9` |
| Delta vs current | `-31.0` |
| Current literal length bits | `398.0` |
| New literal length bits | `366.0` |
| Forced suffix literals | `8` |
| Saved length bits before rule | `32.0` |
| Rule bits | `1` |

## Forced Literal Lengths

| Book | Op | Remaining | Length | Saved bits |
|---:|---:|---:|---:|---:|
| `7` | `6` | `2` | `2` | `4` |
| `14` | `7` | `3` | `3` | `4` |
| `16` | `10` | `2` | `2` | `4` |
| `17` | `11` | `4` | `4` | `4` |
| `42` | `6` | `2` | `2` | `4` |
| `55` | `3` | `4` | `4` | `4` |
| `57` | `7` | `4` | `4` | `4` |
| `65` | `2` | `3` | `3` | `4` |

## Interpretation

The rule is decodable because book lengths and `min_len` are already
declared. A shorter-than-`min_len` remaining suffix cannot be encoded
as a copy, and the existing type rules leave only one legal literal
length: the full remaining suffix.

## Boundary

This is a mechanical length-ledger improvement only. It does not alter
row0, introduce plaintext, or make an authorial-intent claim.
