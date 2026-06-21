# Online Prefix Book Frontier Audit

Classification: `online_prefix_book_frontier_bootstrap_only_failure`
Translation delta: `NONE`

## Purpose

Audit 129 compiles a deterministic online reparse formula using only
previous numeric-order books before committing each next book. This audit
decomposes that result by target book and adds a book-bounded source
variant, so the sequential frontier is visible instead of only the
full-corpus total.

## Summary

- Books checked: `70`.
- Online roundtrip books: `70/70`.
- Book-bounded online roundtrip books: `70/70`.
- Online beats raw: `69/70`.
- Book-bounded online beats raw: `69/70`.
- Online after bootstrap beats raw: `69/69`.
- Book-bounded after bootstrap beats raw: `69/69`.
- Online failure books: `[0]`.
- Book-bounded online failure books: `[0]`.
- Mean online gain vs raw: `424.050` bits.
- Mean book-bounded online gain vs raw: `419.761` bits.
- Min book-bounded online gain vs raw: `-10.499` bits.
- Total book-bounded online gain vs raw: `29383.262` bits.
- Book-bounded cumulative break-even book: `2`.

## Weakest Book-Bounded Online Books

| Book | Prior books | Length | Literal digits | Copied digits | Gain vs raw |
|---:|---:|---:|---:|---:|---:|
| `0` | `0` | `144` | `128` | `16` | `-10.499` |
| `1` | `1` | `92` | `69` | `23` | `9.752` |
| `2` | `2` | `177` | `146` | `31` | `43.038` |
| `3` | `3` | `140` | `92` | `48` | `68.705` |
| `25` | `25` | `35` | `3` | `32` | `85.075` |
| `20` | `20` | `63` | `0` | `63` | `96.767` |
| `49` | `49` | `115` | `25` | `90` | `129.348` |
| `54` | `54` | `57` | `0` | `57` | `155.526` |
| `39` | `39` | `59` | `7` | `52` | `155.927` |
| `7` | `7` | `106` | `24` | `82` | `191.693` |

## Highest Book-Boundary Penalties

| Book | Penalty vs unbounded online | Book-bounded gain vs raw |
|---:|---:|---:|
| `10` | `36.626` | `861.066` |
| `31` | `30.366` | `635.828` |
| `59` | `21.101` | `823.114` |
| `67` | `20.776` | `283.636` |
| `42` | `20.373` | `482.471` |
| `27` | `18.887` | `372.481` |
| `53` | `18.156` | `860.325` |
| `58` | `17.951` | `827.097` |
| `34` | `16.960` | `237.581` |
| `43` | `16.701` | `431.207` |

## Decision

- The online numeric-prefix parser has a single local raw-coding failure: book `0`, before any prior book inventory exists.
- After the bootstrap book, both unbounded and book-bounded online variants beat raw digit coding in `69/69` books.
- This strengthens sequential mechanical generation evidence, but it does not derive row0 or introduce plaintext.
