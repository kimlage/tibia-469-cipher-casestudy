# Book Length Ledger Search

Verdict: `controlled_book_length_ledger_improvement`. Translation delta: `NONE`.

This audit keeps the repaired sequential LZ recipe fixed and retests only
the ledger used to describe the 70 book lengths. The current formula
charges each book length with `gamma(length+1)`. Candidate ledgers are
decodable and charge their declared parameters.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `9537.3` |
| Current book-length bits | `1030.0` |
| Best book-length bits | `566.0` |
| Best total bits | `9073.3` |
| Delta vs current | `-464.0` |
| Book count | `70` |
| Length range | `35..294` |
| Unique lengths | `51` |

## Top Models

| Rank | Model | Parameters | Book-length bits | Total bits | Delta |
|---:|---|---|---:|---:|---:|
| `1` | `signed_rice_residual_from_anchor` | `{"anchor": 151, "k": 5}` | `566.0` | `9073.3` | `-464.0` |
| `2` | `signed_rice_residual_from_anchor` | `{"anchor": 146, "k": 5}` | `567.0` | `9074.3` | `-463.0` |
| `3` | `signed_rice_residual_from_anchor` | `{"anchor": 147, "k": 5}` | `567.0` | `9074.3` | `-463.0` |
| `4` | `signed_rice_residual_from_anchor` | `{"anchor": 149, "k": 5}` | `567.0` | `9074.3` | `-463.0` |
| `5` | `signed_rice_residual_from_anchor` | `{"anchor": 150, "k": 5}` | `567.0` | `9074.3` | `-463.0` |
| `6` | `signed_rice_residual_from_anchor` | `{"anchor": 148, "k": 5}` | `568.0` | `9075.3` | `-462.0` |
| `7` | `signed_rice_residual_from_anchor` | `{"anchor": 154, "k": 5}` | `568.0` | `9075.3` | `-462.0` |
| `8` | `signed_rice_residual_from_anchor` | `{"anchor": 152, "k": 5}` | `569.0` | `9076.3` | `-461.0` |
| `9` | `signed_rice_residual_from_anchor` | `{"anchor": 153, "k": 5}` | `569.0` | `9076.3` | `-461.0` |
| `10` | `signed_rice_residual_from_anchor` | `{"anchor": 155, "k": 5}` | `569.0` | `9076.3` | `-461.0` |

## Interpretation

The book lengths are clustered enough that a signed Rice residual ledger
around a declared anchor is much cheaper than independent gamma-coded
lengths. This is a cost-ledger improvement, not evidence of plaintext
or a row0 pair-table origin.

## Boundary

This changes only the mechanical generation cost accounting and the
declared book-length ledger. It does not alter the emitted books, row0,
or the semantic verdict.
