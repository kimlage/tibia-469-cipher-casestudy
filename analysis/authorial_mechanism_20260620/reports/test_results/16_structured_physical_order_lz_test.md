# Structured Physical Order LZ Test

Verdict: `structured_physical_order_not_better_than_numeric`. Translation delta: `NONE`.

This audit tests whether the partial public Hellgate bookcase/order seed
can be used as a zero-search-cost book order for the DP sequential LZ
generator. The source is explicitly public overview/bookcase order, not
exact tile, slot, orientation, or authorial read order.

## Manifest Coverage

| Metric | Value |
|---|---:|
| `manifest_rows` | `71` |
| `resolved_unique_rows` | `65` |
| `resolved_unique_books` | `64` |
| `ambiguous_rows` | `6` |
| `duplicate_resolved_book_rows` | `1` |

## Candidate Orders

| Order | Bits | Delta vs numeric | Copied digits | Literal digits | Roundtrip |
|---|---:|---:|---:|---:|---:|
| `numeric_order` | `9823.3` | `0.0` | `10468` | `795` | `70/70` |
| `hellgate_public_resolved_then_numeric_missing` | `9993.1` | `169.8` | `10530` | `733` | `70/70` |
| `hellgate_bookcase_public_entry_then_numeric_missing` | `9993.1` | `169.8` | `10530` | `733` | `70/70` |
| `hellgate_bookcase_numeric_within_then_missing` | `9993.1` | `169.8` | `10530` | `733` | `70/70` |
| `hellgate_public_resolved_reverse_then_numeric_missing` | `10028.0` | `204.7` | `10440` | `823` | `70/70` |
| `hellgate_public_candidates_first_then_numeric_missing` | `10094.4` | `271.1` | `10524` | `739` | `70/70` |
| `hellgate_public_candidates_last_then_numeric_missing` | `10118.7` | `295.4` | `10518` | `745` | `70/70` |

## Random Order Control

| Runs | Mean bits | Min bits | Max bits | p(bits <= best structured) |
|---:|---:|---:|---:|---:|
| `100` | `10049.1` | `9741.1` | `10263.2` | `0.0198` |

## Interpretation

Structured public orders are useful diagnostics, but the committed public
manifest still has ambiguous entries, duplicate resolved rows, and no fine
tile/slot/orientation/read-order layer. Therefore a better structured
order, if any, is not promoted as authorial order in this cycle.

## Boundary

This is a mechanical order-cost audit only. It does not introduce plaintext,
semantic claims, or a row0 pair-table formula.
