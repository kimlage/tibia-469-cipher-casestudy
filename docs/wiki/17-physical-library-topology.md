---
page_id: physical-library-topology
page_type: finding
context: bonelord-469
visibility: public_candidate
status: frozen
updated_at: 2026-06-20
moc_parent: README.md
source_refs:
  - analysis/physical_topology_20260620
---

# 17. Physical Library Topology

[<- Language Comparanda](16-language-comparanda.md) . [Wiki home](README.md)

---

## Verdict

The public topology pass adds a partial physical manifest and bounded
mechanical tests. It does not create a topology decoder and does not change the
semantic verdict.

Translation delta: `NONE`.

Round result: `PARTIAL TOPOLOGY READY / fine topology blocked`.

## What Was Verified

Public sources support:

- Hellgate Library as the central public corpus, with books listed in overview
  and bookcase order.
- Isle of the Kings Library shelf 21 as *Beware of the Bonelords* context.
- Isle of the Kings Library shelf 39 as the external `6512889672 (Book)` 469
  anchor.
- Kharos/Ferumbras Tower as a community-reported external watchlist item, not a
  fine-grained indexed holdout.

The still-missing layer is:

```text
book_id -> exact tile -> shelf side -> slot -> orientation -> map version
```

Without that layer, topology can inspire tests but cannot promote a route,
graph, or read-order mechanism.

## H-TOP Classification

| ID | Hypothesis | Classification |
|---|---|---|
| H-TOP1 | public collection order may be editorial, not authorial | `accepted_process_guard` |
| H-TOP2 | the library should be modeled as a graph, not a single list | `open_requires_coordinates` |
| H-TOP3 | Isle shelf 21/39 may be metatext-to-cipher context | `weak_context_clue` |
| H-TOP4 | Kharos/Ferumbras may be dispersal/watchlist, not a key | `watchlist_only` |
| H-TOP5 | topology may predict modules, not words | `tested_no_promotion` |

## Test Results

The public Hellgate seed has 71 public table entries against the local
canonical 70-book corpus. Several short public title prefixes are ambiguous
against local books. This is why the manifest is useful as a partial topology
seed, not as a clean authorial sequence.

The mechanical-signal audit tested public order adjacency and bookcase grouping
against deterministic shuffles over row0 similarity. It did not promote a
physical-order mechanism.

The later DP LZ order test used the same public manifest as a possible
zero-search-cost book order for the strongest current generator. Numeric order
still wins at `9823.3` bits. The best public/bookcase order costs `9993.1`
bits (`+169.8`), and candidate-filled ambiguous orders cost more. This further
supports the blocker: the public overview/bookcase seed is not an accepted
authorial read order.

## Reports

- [Public topology synthesis report](../../analysis/physical_topology_20260620/reports/public_topology_synthesis_report.md)
- [Final physical topology report](../../analysis/physical_topology_20260620/reports/final_physical_topology_report.md)
- [Public topology manifest audit](../../analysis/physical_topology_20260620/reports/test_results/01_public_topology_manifest_audit.md)
- [Topology mechanical signal audit](../../analysis/physical_topology_20260620/reports/test_results/02_topology_mechanical_signal_audit.md)
- [Structured physical order LZ test](../../analysis/authorial_mechanism_20260620/reports/test_results/16_structured_physical_order_lz_test.md)

## What Counts As Future Progress

Future topology work must either provide an authoritative fine-grained manifest
or show that a physical graph predicts held-out module/copy structure better
than shuffles and at lower description length. A route that merely creates a
nice story or suggests a translation is not progress.
