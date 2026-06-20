# Topology Mechanical Signal Audit

Verdict: `no_promoted_topology_signal`. Translation delta: `NONE`.

This audit tests whether the partial public Hellgate order or bookcase
grouping predicts simple row0 mechanical similarity better than
deterministic shuffles. It is not a translation test.

## Public Order

| Metric | Value |
|---|---:|
| Resolved entries used | `65` |
| Unique resolved books | `64` |
| Public adjacent score | `0.420618` |
| Shuffle mean | `0.407042` |
| p(control >= observed) | `0.1460` |

## Bookcase Grouping

| Metric | Value |
|---|---:|
| Bookcase group score | `0.389400` |
| Shuffle mean | `0.400969` |
| p(control >= observed) | `0.7215` |

## External Anchors

- Isle shelf 39 prefix `6512889672` maps to local candidates `['22']`.
- Under the Fandom overview seed, the same prefix is Hellgate public entry `31`, not public entry `35`; the TibiaSecrets `Book 35` statement remains an indexing/numbering mismatch to audit, not an accepted rejection.
- Kharos/Ferumbras remains blocked until exact text or an independent indexed source is available.

## H-TOP Status

| Hypothesis | Status |
|---|---|
| `H-TOP1` | `accepted_process_guard` |
| `H-TOP2` | `open_requires_coordinates` |
| `H-TOP3` | `weak_context_clue` |
| `H-TOP4` | `watchlist_only` |
| `H-TOP5` | `tested_no_promotion` |

## Conclusion

The public topology seed is useful for future graph/holdout work, but this
simple signal test does not promote a physical-order mechanism or any
semantic reading.
