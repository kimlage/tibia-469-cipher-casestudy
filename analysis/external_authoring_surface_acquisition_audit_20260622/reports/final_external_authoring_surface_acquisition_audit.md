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

## GitHub Exact Book Source Hunt

A follow-up exact-code search checks whether public GitHub hits for representative book strings expose an object layer.
It found `60` exact text hits across `5` repositories, but all promoted-class hits are corpus mirrors or community analysis repositories.
No hit supplies book object/container/slot/order provenance, so no source is integrated into v9.

- [02_github_exact_book_source_hunt.py](../scripts/02_github_exact_book_source_hunt.py)
- [02_github_exact_book_source_hunt.json](test_results/02_github_exact_book_source_hunt.json)
- [02_github_exact_book_source_hunt.md](test_results/02_github_exact_book_source_hunt.md)

## Leaked Source Boundary

A source-boundary gate answers whether the old Tibia source-code/map leak should be used for topology.
It should not: leaked proprietary material is rejected as an evidence route.
Community reuse in alt servers is not sufficient provenance or permission for this repository.
The usable path is an authorized CSV/JSON object-layer contract with book text/prefix, coordinates, container/bookcase identity, slot/read order, version/date, and rights/provenance.
No source is integrated into v9 and net v9 reduction remains `0.0` bits.

- [03_leaked_source_boundary_and_clean_topology_contract.py](../scripts/03_leaked_source_boundary_and_clean_topology_contract.py)
- [03_leaked_source_boundary_and_clean_topology_contract.json](test_results/03_leaked_source_boundary_and_clean_topology_contract.json)
- [03_leaked_source_boundary_and_clean_topology_contract.md](test_results/03_leaked_source_boundary_and_clean_topology_contract.md)

## Clean Topology Contract Validator

A contract validator now defines the executable CSV shape for rights-cleared topology evidence.
The current public Hellgate manifest fails the contract, and TibiaMaps public markers are POI-level data without Hellgate/book object slots.
No source is integrated into v9 and net v9 reduction remains `0.0` bits.

- [04_clean_topology_contract_validator.py](../scripts/04_clean_topology_contract_validator.py)
- [04_clean_topology_contract_validator.json](test_results/04_clean_topology_contract_validator.json)
- [04_clean_topology_contract_validator.md](test_results/04_clean_topology_contract_validator.md)
- [04_clean_topology_contract_template.csv](test_results/04_clean_topology_contract_template.csv)

## Clean Topology v9 Integration Harness

A v9 integration harness now matches rights-clean topology CSV rows to canonical books and prepares topology feature tests against v9 operation streams.
The current template input has `1` unique match and does not meet coverage thresholds, so no source is integrated.
No v9 reduction is claimed.

- [05_clean_topology_v9_integration_harness.py](../scripts/05_clean_topology_v9_integration_harness.py)
- [05_clean_topology_v9_integration_harness.json](test_results/05_clean_topology_v9_integration_harness.json)
- [05_clean_topology_v9_integration_harness.md](test_results/05_clean_topology_v9_integration_harness.md)
