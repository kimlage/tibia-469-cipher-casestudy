# `scripts/` — analysis & reproducibility scripts

This directory holds the Python from the **structural-search era** of the 469
project: one canonical data-ingest tool, a handful of workbook-runner utilities,
and a large archive of one-off cryptanalysis probes.

> **Looking for the final report's evidence?** It is **not** here. Every number
> in the [final report](../docs/469_final_report.md) is reproduced by the
> committed pipeline in [`analysis/audit_20260609/`](../analysis/audit_20260609/)
> (scripts + raw outputs). This `scripts/` directory is the older exploratory
> layer, preserved for provenance.

## The operational database

Almost everything here reads a local SQLite database,
`data/bonelord_operational.sqlite`, which is **not committed**. It is
regenerated from the committed `.xlsx` workbooks (e.g.
`bonelord_469_iter129.xlsx`) via the canonical exporter:

```bash
python scripts/export_workbook_to_sqlite.py \
    bonelord_469_iter129.xlsx \
    --db data/bonelord_operational.sqlite \
    --replace-db
```

`export_workbook_to_sqlite.py` does a lossless-ish ingest of the workbook
(per-cell dump, JSON row payloads, and one convenience `sheet__<name>` table per
sheet). All downstream scripts open the DB **read-only**
(`sqlite3.connect("file:...?mode=ro", uri=True)`).

> Note: the exporter's `--db` flag defaults to `bonelord_workbook.sqlite`, but
> the probes and the audit pipeline expect `bonelord_operational.sqlite` — pass
> `--db data/bonelord_operational.sqlite` explicitly, as shown above.

## Canonical / load-bearing scripts

These are the scripts a reproducer actually needs:

| Script | Role |
| --- | --- |
| `export_workbook_to_sqlite.py` | **Canonical.** Regenerates the operational SQLite DB from a committed `.xlsx` workbook. The entry point for everything else. |
| `sqlite_snapshot_ref.py` | Shared helper for resolving a workbook export/snapshot inside the DB. Imported by ~22 probes; not run directly. |
| `bonelord_flow_next_iteration.py` | The original workbook-mutating "next iteration" decode runner (openpyxl only). Historical engine of the iterative loop — large (~950 KB) and **not** needed to reproduce the final report. |
| `bonelord_validate_workbook.py` | Workbook-invariant validator for the iteration loop. |
| `bonelord_run_until_stale.py` | Drives `bonelord_flow_next_iteration.py` until convergence. |
| `bonelord_import_corpus.py` | Imports local plaintext reference lines into the workbook (no network). |

## Historical probe archive (~543 scripts, not curated)

The overwhelming majority of this directory — **543 of the ~553 `.py` files** —
are `sqlite_*` probe/gate/audit scripts from the structural-search era. They are
preserved verbatim for provenance, **not curated for reuse**:

- **No single entry point.** Each script is a self-contained one-off: it opens
  the read-only DB, runs one specific structural test or falsification, prints
  or writes its result, and exits.
- **Heavily versioned and forked.** ~258 carry a `_v<N>` suffix
  (`..._falsification_v1.py`), and names encode the question they probed
  (`sqlite_human_q96_...`, `sqlite_book...`, `sqlite_naese...`, etc.). ~140 are
  `sqlite_human_q<NN>_*` analyst queries.
- **Internal cross-imports.** A few probes are imported by others as data
  modules (e.g. `sqlite_probe_registry`) rather than run standalone.

Treat this archive as a lab notebook, not a library. To understand the project's
conclusions, read [`analysis/audit_20260609/`](../analysis/audit_20260609/) and
the [final report](../docs/469_final_report.md); to see the exploratory path
that preceded them, browse here.

## Reproducing

1. Install dependencies: `pip install -r requirements.txt` (repo root).
2. Regenerate the DB from a committed workbook (command above).
3. Run any individual probe, e.g.
   `python scripts/sqlite_human_q96_q80_packet_source_as_packet_audit_v1.py`.
   Probes resolve the repo root relative to their own location and open the DB
   read-only, so no further configuration is needed.
