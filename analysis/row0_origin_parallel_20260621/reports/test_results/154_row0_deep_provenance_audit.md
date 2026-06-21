# 154. Row0 Deep Provenance Audit

Classification: `AUDIT_ONLY`
Translation delta: `NONE`

Decision: `project_row0_provenance_partially_traced_but_cipsoft_origin_untraced`.

## Workbook inventory

| Workbook | Sheets | Key row0-adjacent sheets | Classification |
|---|---:|---|---|
| `bonelord_469_iter129.xlsx` | `1926` | `KeyTable, BooksDigitModel_v118, DigitOmissionStats_v118, OmissionCompare_v120, ExternalGroundTruthCheck_v120, GroundTruthSources_v121, GroundTruthSources_v122, GroundTruthSources_v129` | `legacy_workbook_snapshot_or_derived_project_artifact` |
| `bonelord_469_iter129_frontier.xlsx` | `1491` | `KeyTable, BooksDigitModel_v118, DigitOmissionStats_v118, OmissionCompare_v120, ExternalGroundTruthCheck_v120, GroundTruthSources_v121, GroundTruthSources_v122, GroundTruthSources_v129` | `legacy_workbook_snapshot_or_derived_project_artifact` |
| `bonelord_469_iter129_stab.xlsx` | `1491` | `KeyTable, BooksDigitModel_v118, DigitOmissionStats_v118, OmissionCompare_v120, ExternalGroundTruthCheck_v120, GroundTruthSources_v121, GroundTruthSources_v122, GroundTruthSources_v129` | `legacy_workbook_snapshot_or_derived_project_artifact` |
| `archive/bonelord_469_iter141.xlsx` | `173` | `KeyTable, BooksDigitModel_v118, DigitOmissionStats_v118, OmissionCompare_v120, ExternalGroundTruthCheck_v120, GroundTruthSources_v121, GroundTruthSources_v122, GroundTruthSources_v129` | `legacy_workbook_snapshot_or_derived_project_artifact` |

## Script provenance

| Artifact | Classification | Risk |
|---|---|---|
| `export_workbook_to_sqlite` | `preservation_importer_not_row0_generator` | `low_generation_risk_high_source_importance` |
| `row0_code_symbol_probe` | `project_reconstruction_probe_not_cipsoft_origin` | `medium_reconstruction_policy_risk` |
| `q3_tables` | `sqlite_schema_introspection_only` | `low` |
| `external_row0_literal_decode` | `external_phrase_audit_not_origin_source` | `semantic_overreach_risk_if_misused` |

## Interpretation

The repository can explain how row0 is preserved, imported, reconstructed, and audited inside the project. It still does not identify a primary CipSoft source or authorial generator for the pair-label placement.
