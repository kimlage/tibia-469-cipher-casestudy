# Clean Topology Contract Validator

Classification: `clean_topology_contract_ready_public_sources_still_insufficient`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

A rights-clean topology input now has an executable CSV contract and template.

The current public Hellgate bookcase manifest is a negative control: it does not satisfy the contract because it lacks rights/provenance, coordinates, container object identity, and slot/read-order fields.

TibiaMaps public markers were probed as licensed map/POI data: `4861` markers, but no Hellgate/Library/Bonelord/Beholder hits and no book object layer.

## Contract Fields

| Field | Required |
| --- | --- |
| `source_id` | `True` |
| `source_rights` | `True` |
| `source_version_or_date` | `True` |
| `book_text_or_exact_prefix` | `True` |
| `x` | `True` |
| `y` | `True` |
| `z` | `True` |
| `container_or_bookcase_id` | `True` |
| `slot_or_read_order` | `True` |
| `capture_method` | `True` |
| `orientation_or_side` | `False` |
| `notes` | `False` |

## Negative Controls

| Source | Contract Valid | Can Test v9 | Missing/Reason |
| --- | --- | --- | --- |
| `hellgate_public_bookcase_manifest.csv` | `False` | `False` | missing: source_id, source_rights, source_version_or_date, book_text_or_exact_prefix, x, y, z, container_or_bookcase_id, slot_or_read_order, capture_method |
| `tibiamaps markers.json` | `False` | `False` | POI markers only; term hits {'hellgate': 0, 'library': 0, 'bonelord': 0, 'beholder': 0, '469': 0} |

## Decision

No external source is acquired or integrated into v9. Net v9 reduction: `0.0` bits.

Progress from here requires filling the template with rights-cleared object/container/slot/order metadata.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
