# Sequential LZ Book Formula Compile

Verdict: `controlled_sequential_lz_book_formula`. Translation delta: `NONE`.

This compiler materializes the earlier LZ-style upper-bound idea as a
self-contained book generator: each book is emitted in numeric order as
literal digit runs plus references to already emitted prior-book or
current-prefix digits. The real corpus and every control choose the best
`min_len` from the same search set.

## Best Real Encoding

| Metric | Value |
|---|---:|
| Min match | `6` |
| Sequential LZ bits | `10190.0` |
| Hierarchical reference bits | `13858.5` |
| Gain vs hierarchical | `3668.5` |
| Raw digit baseline bits | `37414.9` |
| Literal digits | `812` |
| Copy items | `279` |
| Copied digits | `10451` |
| Book roundtrip | `70/70` |

## Negative Controls

| Control | Runs | Mean bits | Min bits | p(bits <= observed) |
|---|---:|---:|---:|---:|
| `within_book_digit_shuffle_bits` | `160` | `48790.2` | `48572.5` | `0.0062` |
| `random_same_lengths_bits` | `160` | `49125.0` | `48892.1` | `0.0062` |
| `book_order_shuffle_bits` | `160` | `10429.2` | `10115.7` | `0.0311` |

## Boundary

This is a mechanical copy/reference generator and a tighter upper bound
on book fabrication cost. It does not explain the row0 pair table and
does not introduce plaintext.
