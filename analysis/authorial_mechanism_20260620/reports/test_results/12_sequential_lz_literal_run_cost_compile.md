# Sequential LZ Literal-Run Cost Compile

Verdict: `controlled_sequential_lz_run_literal_formula`. Translation delta: `NONE`.

The previous sequential LZ formula already emits literal runs, but its
rough cost charged a literal flag per digit. This pass keeps the same
copy/reference generator family and charges each literal run as
`flag + gamma(length+1) + digits`, then lets the real corpus and controls
choose the best `min_len` from the same set.

## Best Real Encoding

| Metric | Value |
|---|---:|
| Min match | `6` |
| Run-literal LZ bits | `9944.0` |
| Sequential LZ v1 bits | `10190.0` |
| Gain vs v1 | `246.0` |
| Raw digit baseline bits | `37414.9` |
| Literal digits | `812` |
| Literal runs | `85` |
| Copy items | `279` |
| Copied digits | `10451` |
| Book roundtrip | `70/70` |

## Negative Controls

| Control | Runs | Mean bits | Min bits | p(bits <= observed) |
|---|---:|---:|---:|---:|
| `within_book_digit_shuffle_bits` | `160` | `39555.5` | `39540.7` | `0.0062` |
| `random_same_lengths_bits` | `160` | `39556.8` | `39537.2` | `0.0062` |
| `book_order_shuffle_bits` | `160` | `10233.9` | `9991.2` | `0.0062` |

## Boundary

This is a cost/model refinement of the mechanical copy/reference
generator. It tightens the book fabrication upper bound but does not
explain row0 or introduce plaintext.
