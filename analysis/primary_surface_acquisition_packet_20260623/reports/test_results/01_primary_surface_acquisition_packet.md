# Primary Surface Acquisition Packet

Classification: `primary_surface_acquisition_packet_ready_no_source_integrated`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

This is the operational handoff for the only remaining main route: a clean primary or rights-cleared object-layer surface.
The worksheet pre-fills all 70 canonical books with matching prefixes and leaves only provenance/topology fields for an authorized capture.

## Required Real Fields

- `source_id`
- `source_rights`
- `source_version_or_date`
- `book_text_or_exact_prefix`
- `x`
- `y`
- `z`
- `container_or_bookcase_id`
- `slot_or_read_order`
- `capture_method`

## Accepted Source Classes

- `official_cipsoft_public_or_in_game_capture`
- `user_provided_authorized_metadata_csv_json`
- `public_licensed_object_layer_data`
- `versioned_authoring_artifact_with_rights`

Rejected source classes:

- `leaked_proprietary_source_or_map`
- `unknown_rights_export`
- `fan_solution_without_object_layer`

## Validation Command

After filling the worksheet with real authorized object-layer data, run:

```bash
python3 analysis/external_authoring_surface_acquisition_audit_20260622/scripts/06_clean_topology_v9_control_protocol.py --input analysis/primary_surface_acquisition_packet_20260623/reports/test_results/01_primary_surface_acquisition_worksheet.csv --output-dir analysis/primary_surface_acquisition_packet_20260623/reports/test_results/protocol_dry_run
```

The current worksheet intentionally has blank required fields, so it is not a valid source yet and integrates `0.0` v9 bits.
The command above writes into `protocol_dry_run/` so acquisition checks cannot overwrite the canonical external-authoring protocol outputs.
The expected dry run result for the blank worksheet is `clean_topology_v9_controls_preregistered_not_run_coverage_insufficient`.

Companion acquisition gates:

- `02_source_candidate_preflight` classifies proposed sources before any v9 integration attempt.
- `03_minimal_capture_design` prioritizes a protocol-useful first capture batch when full 70-book object-layer coverage is not yet available.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
