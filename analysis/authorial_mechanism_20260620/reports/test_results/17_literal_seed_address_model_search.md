# Literal Seed Address Model Search

Verdict: `literal_seed_address_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit tests whether copy operations in the DP LZ formula can source
from prior literal seed runs using `literal_run_id + offset`, rather than
the current absolute `source_pos` in the emitted stream.

## Address Models

| Model | Copy bits | Total bits | Delta vs current | Decodable mixed ledger |
|---|---:|---:|---:|---:|
| `literal_seed_address_optimistic_no_mode` | `5520.9` | `9752.8` | `-70.5` | `False` |
| `absolute_flat_source_pos` | `5591.4` | `9823.3` | `-0.0` | `True` |
| `literal_seed_address_conservative_mode_per_copy` | `5801.9` | `10033.8` | `210.5` | `True` |

## Seed Opportunity

| Metric | Value |
|---|---:|
| Copy items | `281` |
| Literal runs | `84` |
| Copy items addressable from a prior literal seed | `82` |
| Optimistic seed-address uses | `28` |
| Conservative seed-address uses | `28` |
| Exact whole literal-run copies | `3` |
| Optimistic address savings | `70.5` bits |

## Interpretation

A literal-seed address looks cheaper only in the optimistic ledger that
does not pay to distinguish absolute stream addresses from literal-seed
addresses. Once a source-mode bit is charged for a decodable mixed
ledger, the model is worse than the current absolute `source_pos`
formula. Therefore this seed-address model is not promoted.

## Boundary

This is a mechanical address-cost audit only. It does not alter the book
strings, explain row0, or introduce plaintext.
