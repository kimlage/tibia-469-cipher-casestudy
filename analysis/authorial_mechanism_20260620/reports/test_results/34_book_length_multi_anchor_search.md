# Book Length Multi-Anchor Search

Verdict: `multi_anchor_book_length_ledger_not_promoted`. Translation delta: `NONE`.

This audit tests whether the promoted single-anchor book-length ledger
can be improved by a decodable multi-anchor signed-Rice mixture. The
search uses optimal dynamic programming over sorted unique lengths and
charges cluster anchors, `k`, and explicit per-book mode bits.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `9073.3` |
| Current book-length bits | `566.0` |
| Best multi-anchor book-length bits | `581.0` |
| Best multi-anchor total bits | `9088.3` |
| Delta vs current | `15.0` |
| Best cluster count | `2` |
| Best k | `4` |

## Top Models

| Rank | Clusters | k | Book-length bits | Total bits | Delta |
|---:|---:|---:|---:|---:|---:|
| `1` | `2` | `4` | `581.0` | `9088.3` | `15.0` |
| `2` | `2` | `3` | `597.0` | `9104.3` | `31.0` |
| `3` | `4` | `3` | `607.0` | `9114.3` | `41.0` |
| `4` | `2` | `5` | `613.0` | `9120.3` | `47.0` |
| `5` | `4` | `2` | `623.0` | `9130.3` | `57.0` |
| `6` | `4` | `4` | `635.0` | `9142.3` | `69.0` |
| `7` | `3` | `3` | `637.0` | `9144.3` | `71.0` |
| `8` | `3` | `4` | `644.0` | `9151.3` | `78.0` |
| `9` | `6` | `2` | `653.0` | `9160.3` | `87.0` |
| `10` | `2` | `6` | `664.0` | `9171.3` | `98.0` |

## Interpretation

The best multi-anchor ledger is worse than the promoted single-anchor
ledger once per-book mode bits and extra anchor declarations are paid.
The current `anchor=151`, `k=5` length ledger remains the active bound.

## Boundary

This is a mechanical cost-ledger audit only. It does not alter the
book text, row0, or semantic verdict.
