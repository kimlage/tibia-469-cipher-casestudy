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
  - analysis/physical_topology_control_signal_audit_20260622
  - analysis/external_authoring_surface_acquisition_audit_20260622
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

The follow-up control-signal audit tests the remaining topology-progress
condition directly: whether partial public bookcase/order metadata predicts
residual executable-decoder streams. It does not. Over resolved unique topology
coverage (`54` derived books, `237` operations), topology features are worse
than global coding for coarse control (`-107.149` bits), copy-hint rank bucket
(`-102.873` bits), and op type (`-46.439` bits), with `0/20` positive splits
for each target and no permutation-p95 wins. Public topology therefore remains
a bounded manifest/context clue, not a generation-control program.

The external authoring-surface acquisition audit checks the next plausible
topology source class. `tibiamaps/tibia-historical-map-data` is now tracked as a
weak map-geometry candidate because it exposes historical `7.3/7.4/7.5/7.7`
floor maps, but the API probe sees PNG floor imagery, not book object,
container, slot, or insertion-order metadata. Current TibiaMaps data is also
map/marker surface, not historical book object provenance. This narrows the
future topology requirement: a promotable source must provide
`book_id/text -> x/y/z -> container/bookcase object -> slot/read/order ->
version/provenance`. Map images alone do not satisfy the contract and do not
reduce v9.

A GitHub exact-book source hunt then checks the easy public-code route. Five
representative 469 book-prefix searches produce `60` exact text hits across
`5` repositories, but all are corpus mirrors or community analysis repositories
(`s2ward/469`, `elkolorado/*`, `caiocrm/469`). No hit exposes book object,
container, slot, or order provenance. This preserves the acquisition target:
object-layer data or versioned authoring traces, not another text mirror.

The leaked-source boundary gate rejects the old Tibia source-code/map leak as
an evidence route for this repository. Community reuse in alt servers is not
enough to establish permission or clean provenance. A usable topology input
must instead be official/in-game, public licensed, user-authorized, or otherwise
rights-cleared metadata with the required object/container/slot/order fields.

The clean topology contract validator makes that route executable. It writes a
CSV template with required fields (`source_id`, `source_rights`,
`source_version_or_date`, exact book text/prefix, `x/y/z`,
`container_or_bookcase_id`, `slot_or_read_order`, and `capture_method`) and
tests current public data as negative controls. The existing Hellgate public
bookcase manifest fails the contract because it lacks rights/provenance,
coordinates, object identity, and slot/read order. TibiaMaps public markers are
clean POI-level data (`4861` markers) but contain no Hellgate/Library/Bonelord/
Beholder hits and no book object layer. No topology source is integrated into
v9.

## Reports

- [Public topology synthesis report](../../analysis/physical_topology_20260620/reports/public_topology_synthesis_report.md)
- [Final physical topology report](../../analysis/physical_topology_20260620/reports/final_physical_topology_report.md)
- [Public topology manifest audit](../../analysis/physical_topology_20260620/reports/test_results/01_public_topology_manifest_audit.md)
- [Topology mechanical signal audit](../../analysis/physical_topology_20260620/reports/test_results/02_topology_mechanical_signal_audit.md)
- [Structured physical order LZ test](../../analysis/authorial_mechanism_20260620/reports/test_results/16_structured_physical_order_lz_test.md)
- [Physical topology control signal audit](../../analysis/physical_topology_control_signal_audit_20260622/reports/final_physical_topology_control_signal_audit.md)
- [External authoring surface acquisition audit](../../analysis/external_authoring_surface_acquisition_audit_20260622/reports/final_external_authoring_surface_acquisition_audit.md)
- [Clean topology contract template](../../analysis/external_authoring_surface_acquisition_audit_20260622/reports/test_results/04_clean_topology_contract_template.csv)

## What Counts As Future Progress

Future topology work must either provide an authoritative fine-grained manifest
or show that a physical graph predicts held-out module/copy structure better
than shuffles and at lower description length. A route that merely creates a
nice story or suggests a translation is not progress.
