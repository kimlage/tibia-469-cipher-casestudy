# Leaked Source Boundary and Clean Topology Contract

Classification: `leaked_source_route_rejected_clean_topology_contract_ready`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Decision

The project should not obtain, download, parse, quote, or integrate leaked proprietary Tibia source/map data.

Community reuse in alt servers is not sufficient provenance or permission for this repository.

A clean route remains available: authorized object/container/slot/order metadata, official/in-game capture, or public licensed object-layer data.

Net v9 reduction from this gate: `0.0` bits.

## Required Clean Fields

| Field | Required | Purpose |
| --- | --- | --- |
| `source_id` | `True` | Stable identifier for the provided dataset or capture. |
| `source_rights` | `True` | License/permission statement or proof that the data is user-owned/authorized/publicly licensed. |
| `source_version_or_date` | `True` | Client/game/map version or capture date. |
| `book_text_or_exact_prefix` | `True` | Exact numeric text or prefix sufficient to match a canonical 469 book. |
| `x` | `True` | World X coordinate or equivalent local coordinate. |
| `y` | `True` | World Y coordinate or equivalent local coordinate. |
| `z` | `True` | Floor/depth coordinate. |
| `container_or_bookcase_id` | `True` | Bookcase/container object identity, not just a public ordinal. |
| `slot_or_read_order` | `True` | Slot inside the container, item stack position, or observed read order. |
| `orientation_or_side` | `False` | Shelf side/orientation when available. |
| `capture_method` | `True` | Official/in-game capture, user-generated observation, licensed map export, or other allowed route. |

## Source Policy

| Source Class | Status | Can Use | Allowed Action |
| --- | --- | --- | --- |
| `leaked_proprietary_source_or_map` | `REJECTED_SOURCE_ROUTE` | `False` | do not obtain, download, parse, quote, or integrate |
| `official_cipsoft_public_or_in_game_capture` | `PROMOTABLE_IF_FIELDS_AND_CONTROLS_PASS` | `True` | parse into the clean topology contract and test against v9 fields with controls |
| `user_provided_authorized_metadata_csv_json` | `PROMOTABLE_IF_RIGHTS_FIELDS_AND_CONTROLS_PASS` | `True` | validate schema, match canonical books, then run holdout/permutation controls |
| `public_licensed_community_map_or_marker_data` | `AUDIT_ONLY_UNLESS_OBJECT_LAYER_PRESENT` | `True` | record provenance and test only fields present in the clean contract |
| `public_text_mirror_or_fan_solution` | `REJECTED_FOR_TOPOLOGY_CONTROL` | `True` | use as corpus provenance only; do not promote as generator evidence |

## Test Protocol

1. validate rights/provenance and required fields
2. match each row to canonical 469 book by exact text/prefix
3. separate unique, ambiguous, and unmatched book rows
4. derive coordinate/order variables without looking at v9 residual targets
5. test prediction of v9 fields: book_order_topology, event_schedule/coarse_control, copy_literal_decision_policy
6. compare against shuffled coordinates, permuted book order, same-bookcase controls, and public-bookcase baseline
7. promote only if the clean source reduces declared external fields after model/correction costs

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
