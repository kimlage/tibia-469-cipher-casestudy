# Source Candidate Preflight

Classification: `source_candidate_preflight_no_current_candidate_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This preflight classifies candidate source surfaces before the clean topology v9 protocol.
It does not acquire, download, parse, quote, or integrate leaked proprietary material.
Current candidates promotable into the v9 protocol now: `0`.
Net v9 reduction: `0.0` bits.

## Required Pass Fields

- `rights_clean`
- `primary_or_authorized`
- `object_layer_present`
- `matches_469_books`
- `has_container_or_bookcase_id`
- `has_slot_or_read_order`
- `has_version_or_date`

## Candidate Decisions

| Candidate | Classification | Can enter v9 now | Blocks |
| --- | --- | --- | --- |
| `leaked_cipsoft_source_or_map_route` | `REJECTED_SOURCE_ROUTE` | `False` | proprietary_leak, not_rights_clean, do_not_obtain_or_parse |
| `alt_server_or_otbm_derived_from_leak` | `REJECTED_PROVENANCE_CONTROL` | `False` | unknown_rights, likely_leak_lineage, not_primary_authorized |
| `tibiawiki_hellgate_library_text` | `REJECTED_FOR_TOPOLOGY_CONTROL` | `False` | no_object_layer, no_slot_or_read_order, not_primary_authoring_surface |
| `tibiawiki_hellgate_library_map_image` | `REJECTED_FOR_TOPOLOGY_CONTROL` | `False` | no_book_text_match_rows, no_object_layer, no_slot_or_read_order |
| `s2ward_469_repository` | `REJECTED_FOR_TOPOLOGY_CONTROL` | `False` | no_object_layer, no_slot_or_read_order, not_primary_authoring_surface |
| `arturo_bookcase_mapping_repository` | `REJECTED_PROVENANCE_CONTROL` | `False` | posthoc_community_mapping, no_fine_slot_layer, v9_control_probe_rejected |
| `official_or_in_game_user_capture` | `BLOCKED_NEEDS_PRIMARY_SOURCE` | `False` | not_yet_supplied |
| `user_authorized_metadata_csv_json` | `BLOCKED_NEEDS_PRIMARY_SOURCE` | `False` | not_yet_supplied |
| `public_licensed_object_layer_export` | `BLOCKED_NEEDS_PRIMARY_SOURCE` | `False` | not_yet_found |

## Decision

`source_candidate_preflight_no_current_candidate_promoted`.

A source can move forward only if it is rights-clean or user-authorized, exposes object/container/slot/order or versioned authoring fields, matches the 469 books, and then reduces v9 residual fields under holdout/permutation controls.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
