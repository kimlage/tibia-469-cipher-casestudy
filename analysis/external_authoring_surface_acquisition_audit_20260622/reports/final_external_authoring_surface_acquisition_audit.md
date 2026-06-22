# Final External Authoring Surface Acquisition Audit

Classification: `external_authoring_surface_not_acquired_object_layer_required`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

The next useful external route is not another public bookcase list or map image. It must expose an object/container/slot/order layer or versioned authoring trace.

A new candidate source was identified: `tibiamaps/tibia-historical-map-data`. It is useful enough to track because it has historical 7.3/7.4/7.5/7.7 map folders, but the API probe observes PNG floor maps rather than object/book metadata. It is therefore map-geometry only, not a promoted authoring surface.

## Candidate Matrix

| Candidate | Classification | Potential v9 Fields | Blocking Issue |
| --- | --- | --- | --- |
| `tibiamaps_historical_map_data` | `WEAK_EXTERNAL_SURFACE_CANDIDATE_MAP_GEOMETRY_ONLY` | book_order_topology | object layer absent in observed repository shape; leaked-file provenance cannot be treated as official attestation without policy/legal review |
| `tibiamaps_current_map_data` | `AUDIT_ONLY_MAP_AND_MARKER_SURFACE` | book_order_topology | modern/current map surface is not historical authoring order and not an object-content layer |
| `tibiawiki_hellgate_library_bookcase_order` | `REJECTED_ALREADY_TESTED_PUBLIC_BOOKCASE_SURFACE` | none | public overview order is not authorial read order and failed controls |
| `otbm_or_old_client_object_layer` | `BLOCKED_NEEDS_ALLOWED_PRIMARY_OR_NEAR_PRIMARY_OBJECT_SOURCE` | book_order_topology, event_schedule_and_coarse_control, copy_literal_decision_policy | availability, legality/provenance, and exact coverage are unverified |
| `historical_corpus_variants_or_authoring_drafts` | `BLOCKED_NEEDS_VERSIONED_TEXT_OR_SCRIPT_SOURCE` | innovation_replay_event_starts, non_continuation_copy_source_length, literal_innovation_payload_residual | no versioned source located |

## Sufficient Artifact Contract

A promotable source must provide, at minimum:

- version/date and provenance
- coverage for the 70 books or a declared subset with holdout
- `book_id` or exact text match
- `x/y/z` or equivalent physical coordinate
- container/bookcase object identity
- slot/read/order or insertion/order metadata
- enough structure to test against coordinate/order permutation controls

Map PNGs alone fail this contract because they do not identify book objects or slots.

## Decision

No external source is acquired or integrated into v9. Net v9 reduction: `0.0` bits.

`external_authoring_surface_not_acquired_object_layer_required`: the blocker is now concrete. The next external push should seek an allowed object-layer source or historical variants, not more internal residual coding.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Sources

- https://github.com/tibiamaps/tibia-historical-map-data
- https://github.com/tibiamaps/tibia-map-data
- https://tibiamaps.io/guides/map-file-format
- https://tibiamaps.io/guides/minimap-file-format
- https://tibia.fandom.com/wiki/Hellgate_Library

## Reproducible Artifacts

- [01_external_authoring_surface_acquisition_gate.py](../scripts/01_external_authoring_surface_acquisition_gate.py)
- [01_external_authoring_surface_acquisition_gate.json](test_results/01_external_authoring_surface_acquisition_gate.json)
- [01_external_authoring_surface_acquisition_gate.md](test_results/01_external_authoring_surface_acquisition_gate.md)
