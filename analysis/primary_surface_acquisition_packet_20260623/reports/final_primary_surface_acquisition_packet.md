# Final Primary Surface Acquisition Packet

Status: `analysis_only`
Classification: `primary_surface_acquisition_packet_ready_no_source_integrated`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

The internal route is saturated as the main front. This packet makes the remaining external route executable by providing a fillable worksheet for all 70 canonical books.
The worksheet has `70` rows and pre-fills canonical prefixes, but it intentionally contains blank provenance/topology fields.

No source is integrated. This is an acquisition interface for future official/in-game/user-authorized/public-licensed object-layer data.

## Decision

`primary_surface_acquisition_packet_ready_no_source_integrated`.

Progress now requires filling this worksheet or an equivalent CSV with clean source rights, version/date, coordinates, container identity, and slot/read order, then running the existing v9 control protocol.
The packet's own validation command writes to `reports/test_results/protocol_dry_run/`, so incomplete acquisition worksheets can be checked without changing the canonical external-authoring report outputs.
The blank worksheet is expected to fail coverage and integrate `0.0` v9 bits until real authorized topology fields are supplied.
Run the source-candidate preflight before the v9 protocol when a proposed source is ambiguous, community-derived, leak-adjacent, or missing object-layer fields.
Use the minimal capture design to collect a protocol-useful first batch when a full 70-book object-layer capture is not yet available.

## Reproducible Artifacts

- [01_build_primary_surface_acquisition_packet.py](../scripts/01_build_primary_surface_acquisition_packet.py)
- [02_source_candidate_preflight.py](../scripts/02_source_candidate_preflight.py)
- [03_minimal_capture_design.py](../scripts/03_minimal_capture_design.py)
- [04_minimal_capture_protocol_fixture.py](../scripts/04_minimal_capture_protocol_fixture.py)
- [01_primary_surface_acquisition_worksheet.csv](test_results/01_primary_surface_acquisition_worksheet.csv)
- [01_primary_surface_acquisition_packet.json](test_results/01_primary_surface_acquisition_packet.json)
- [01_primary_surface_acquisition_packet.md](test_results/01_primary_surface_acquisition_packet.md)
- [02_source_candidate_preflight.json](test_results/02_source_candidate_preflight.json)
- [02_source_candidate_preflight.md](test_results/02_source_candidate_preflight.md)
- [03_minimal_capture_design.csv](test_results/03_minimal_capture_design.csv)
- [03_minimal_capture_design.json](test_results/03_minimal_capture_design.json)
- [03_minimal_capture_design.md](test_results/03_minimal_capture_design.md)
- [04_minimal_capture_protocol_fixture.csv](test_results/04_minimal_capture_protocol_fixture.csv)
- [04_minimal_capture_protocol_fixture.json](test_results/04_minimal_capture_protocol_fixture.json)
- [04_minimal_capture_protocol_fixture.md](test_results/04_minimal_capture_protocol_fixture.md)
- [minimal_capture_protocol_fixture/06_clean_topology_v9_control_protocol.json](test_results/minimal_capture_protocol_fixture/06_clean_topology_v9_control_protocol.json)
- [minimal_capture_protocol_fixture/06_clean_topology_v9_control_protocol.md](test_results/minimal_capture_protocol_fixture/06_clean_topology_v9_control_protocol.md)
- [protocol_dry_run/06_clean_topology_v9_control_protocol.json](test_results/protocol_dry_run/06_clean_topology_v9_control_protocol.json)
- [protocol_dry_run/06_clean_topology_v9_control_protocol.md](test_results/protocol_dry_run/06_clean_topology_v9_control_protocol.md)

## Source Candidate Preflight

A candidate-source preflight now separates rejected leak/unknown-rights routes, weak public text or macro-topology clues, and admissible but not-yet-supplied clean object-layer routes before the v9 protocol is run.
The current preflight has `0` candidates that can enter the v9 protocol now and integrates `0.0` bits.

- [02_source_candidate_preflight.py](../scripts/02_source_candidate_preflight.py)
- [02_source_candidate_preflight.json](test_results/02_source_candidate_preflight.json)
- [02_source_candidate_preflight.md](test_results/02_source_candidate_preflight.md)

## Minimal Capture Design

A minimal capture design now prioritizes an incremental clean object-layer acquisition instead of requiring all 70 books up front.
The first recommended batch is `balanced_v9_probe_22_books`: all seed books plus two high-signal derived books per decade bucket, giving `12` derived books and `5` possible prefix splits under the current protocol floor.
This is an acquisition plan only: no source is integrated and v9 reduction remains `0.0` bits.

- [03_minimal_capture_design.py](../scripts/03_minimal_capture_design.py)
- [03_minimal_capture_design.csv](test_results/03_minimal_capture_design.csv)
- [03_minimal_capture_design.json](test_results/03_minimal_capture_design.json)
- [03_minimal_capture_design.md](test_results/03_minimal_capture_design.md)

## Minimal Capture Protocol Fixture

A synthetic protocol fixture now verifies that the `balanced_v9_probe_22_books` capture batch can enter the v9 protocol path with sufficient schema, book matching, coverage, joined rows, and splits.
This fixture is explicitly non-evidential and integrates no source; it only tests that the acquisition design is runnable once real authorized object-layer fields are supplied.

- [04_minimal_capture_protocol_fixture.py](../scripts/04_minimal_capture_protocol_fixture.py)
- [04_minimal_capture_protocol_fixture.csv](test_results/04_minimal_capture_protocol_fixture.csv)
- [04_minimal_capture_protocol_fixture.json](test_results/04_minimal_capture_protocol_fixture.json)
- [04_minimal_capture_protocol_fixture.md](test_results/04_minimal_capture_protocol_fixture.md)
- [minimal_capture_protocol_fixture/06_clean_topology_v9_control_protocol.json](test_results/minimal_capture_protocol_fixture/06_clean_topology_v9_control_protocol.json)
- [minimal_capture_protocol_fixture/06_clean_topology_v9_control_protocol.md](test_results/minimal_capture_protocol_fixture/06_clean_topology_v9_control_protocol.md)
