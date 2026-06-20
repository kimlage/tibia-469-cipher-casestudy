# Public Topology Manifest Audit

Verdict: `partial_public_topology_ready_fine_topology_blocked`. Translation delta: `NONE`.

This audit builds a partial public Hellgate bookcase manifest and maps it
to the local 70-book corpus by numeric prefix. It intentionally does not
claim exact tile, slot, orientation, map-version, or authorial read order.

## Coverage

| Metric | Value |
|---|---:|
| Public seed entries | `71` |
| Local DB books | `70` |
| Resolved unique entries | `65` |
| Ambiguous entries | `6` |
| Unmatched entries | `0` |
| Local books covered by any candidate | `70` |

## Ambiguity

The public table is usable as a partial bookcase/order seed, but several
short public title prefixes are ambiguous against the local corpus. The
seed also has 71 public entries while the local canonical corpus has 70
books. This preserves the blocker against treating public entry order as
a clean authorial sequence.

Ambiguous public entries: `['2', '19', '24', '34', '56', '66']`

## Source Checks

| Source | URL | Verified date | Community/non-GT | Blocked use |
|---|---:|---|---:|---:|
| `hellgate_library_fandom` | `True` | `2026-06-20` | `True` | `True` |
| `tibiawiki_br_469` | `True` | `2026-06-20` | `True` | `True` |
| `isle_library_fandom` | `True` | `2026-06-20` | `True` | `True` |
| `tibiasecrets_article166` | `True` | `2026-06-20` | `True` | `True` |
| `kharos_fandom` | `True` | `2026-06-20` | `True` | `True` |

## Fine Topology Blocker

Still missing for promotion:

- `book_id`
- `source_location`
- `room_or_library`
- `shelf_or_container`
- `tile_or_position`
- `read_order`
- `capture_source_url_or_commit`
- `verification_date`

## Conclusion

Macro/bookcase topology is ready for bounded mechanical tests. Fine-grained
topology remains blocked, and semantic translation remains unchanged.
