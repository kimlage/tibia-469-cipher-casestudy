# Sequential LZ Dynamic-Parse Compile

Verdict: `controlled_sequential_lz_dp_parse_formula`. Translation delta: `NONE`.

The previous sequential LZ run-literal formula kept the original greedy
parse. This pass keeps the same copy/reference vocabulary and cost
model, fixes `min_len=6` from that prior best formula, and chooses
each book parse by dynamic programming under the literal-run cost. The
emitted books and copy sources remain mechanical digit operations only.

## Best Real Encoding

| Metric | Value |
|---|---:|
| Min match | `6` |
| DP-parse LZ bits | `9823.3` |
| Run-literal greedy bits | `9944.0` |
| Gain vs run-literal greedy | `120.7` |
| Raw digit baseline bits | `37414.9` |
| Literal digits | `795` |
| Literal runs | `84` |
| Copy items | `281` |
| Copied digits | `10468` |
| Book roundtrip | `70/70` |

## Negative Controls

| Control | Runs | Mean bits | Min bits | p(bits <= observed) |
|---|---:|---:|---:|---:|
| `within_book_digit_shuffle_bits` | `100` | `39542.3` | `39520.2` | `0.0099` |
| `random_same_lengths_bits` | `100` | `39549.8` | `39535.6` | `0.0099` |
| `book_order_shuffle_bits` | `100` | `10063.8` | `9776.9` | `0.0396` |

## Boundary

This is a parser optimization inside the existing mechanical
copy/reference generator. It tightens the book fabrication upper
bound but does not explain row0 or introduce plaintext.
