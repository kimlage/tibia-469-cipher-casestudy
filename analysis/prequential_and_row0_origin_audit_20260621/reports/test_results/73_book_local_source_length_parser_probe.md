# Book-Local Source/Length Parser Probe

Classification: `book_local_source_length_parser_probe_roundtrips_subset`
Translation delta: `NONE`

## Purpose

Gate 72 showed that the final source/length parser is feasible by
state proxy but transition-heavy. This probe runs the existing active
source/length DP on two cutoff-60 books to prove executable parser
behavior before attacking the hard case.

## Summary

- Target books: `[67, 60]`.
- Roundtrip books: `2/2`.
- Books beating raw digit uniform: `2/2`.
- Total parser bits: `125.866`.
- Total same-policy reprice bits: `125.866`.
- Parser minus same-policy reprice: `+0.000` bits.
- Total gain versus raw digit uniform: `701.294` bits.
- Total state evaluations: `127899`.
- Total transition evaluations: `8423281`.
- Total elapsed: `9.699` seconds.

## Book Rows

| Book | Digits | Parser bits | Same-policy reprice | Delta | Raw gain | Ops | States | Transitions | Seconds |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `67` | `98` | `21.126` | `21.126` | `+0.000` | `304.423` | `1` | `33222` | `2523629` | `3.241` |
| `60` | `151` | `104.741` | `104.741` | `+0.000` | `396.871` | `6` | `94677` | `5899652` | `6.458` |

## Hard Case Held Back

- Book: `66`.
- Digits: `210`.
- End-state proxy: `258264`.
- Copy-transition proxy: `26096904`.
- Copy candidate edges: `21321`.
- Distinct candidate end states: `408`.
- Reason: book 66 is the cutoff-60 hard case by transition proxy; it needs pruning/caching before exact execution is a useful gate.

## Decision

- The existing active source/length DP is already executable on small and medium cutoff-60 books, proving the parser path beyond a proxy audit. It is not yet promotable: the subset is narrow, the same-policy reparse comparator is still competitive, and the hard book remains transition-heavy.
- No compression-bound change is introduced.
- No parser or recipe-discovery promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
