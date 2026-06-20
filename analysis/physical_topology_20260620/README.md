---
title: "469 physical library topology"
date: 2026-06-20
status: partial_public_topology_and_tests
translation_delta: NONE
---

# 469 Physical Library Topology

This directory incorporates the 2026-06-20 research note on the public physical
topology of 469 books: Hellgate Library, Isle of the Kings Library, and the
Kharos/Ferumbras Tower watchlist.

It does not promote a physical-position decoder. The current public evidence is
strong enough for macro-location, shelf/bookcase anchors, and an initial
bookcase/order manifest, but still too weak for exact tile, shelf side, slot,
orientation, map-version, or authorial read-order claims.

## Gates

- Public bookcase/order data may be used for mechanical tests only.
- Do not treat public collection order as authorial order.
- Do not mix `HG_public_book_index`, `HG_bookcase_public`, and local `bookid`.
- Do not promote a topology hypothesis unless it predicts a mechanical property
  on holdout better than shuffles and lowers MDL.
- Semantic progress still requires CipSoft/in-game number-to-text,
  book-to-text, or symbol-to-meaning ground truth.

## Contents

- `source_research_summary.md` - distilled incorporation of the provided
  physical-topology research note.
- `public_topology_sources.yaml` - source registry and confidence labels.
- `tables/hellgate_public_bookcase_seed.csv` - public Hellgate bookcase/order
  seed extracted from the source page.
- `scripts/01_public_topology_manifest_audit.py` - maps the public seed to the
  local 70-book DB and records ambiguity.
- `scripts/02_topology_mechanical_signal_audit.py` - tests whether public order
  or bookcase grouping predicts simple row0 mechanical similarity better than
  deterministic shuffles.
- `reports/` - generated and human-readable reports.

Translation delta: `NONE`.
