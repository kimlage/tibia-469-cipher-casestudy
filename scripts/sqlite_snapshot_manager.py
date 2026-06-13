#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from sqlite_snapshot_ref import (
    DEFAULT_SNAPSHOT_NAME,
    ensure_snapshot_refs_schema,
    fetch_export_row,
    lookup_export_id_by_artifact,
    mark_snapshot,
)


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage named operational snapshots in SQLite")
    sub = parser.add_subparsers(dest="cmd", required=True)

    show_p = sub.add_parser("show", help="Show named snapshots")
    show_p.add_argument("--db", default=DEFAULT_DB)

    mark_p = sub.add_parser("mark", help="Mark a named snapshot")
    mark_p.add_argument("--db", default=DEFAULT_DB)
    mark_p.add_argument("--name", default=DEFAULT_SNAPSHOT_NAME)
    mark_p.add_argument("--export-id", type=int, default=None)
    mark_p.add_argument("--artifact", default=None)
    mark_p.add_argument("--note", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        ensure_snapshot_refs_schema(conn)
        if args.cmd == "show":
            rows = conn.execute(
                """
                SELECT
                    s.name,
                    s.export_id,
                    s.artifact_path,
                    s.note,
                    s.updated_at,
                    e.exported_at
                FROM snapshot_refs s
                LEFT JOIN exports e ON e.export_id = s.export_id
                ORDER BY s.name
                """
            ).fetchall()
            print(json.dumps([dict(row) for row in rows], ensure_ascii=True, indent=2))
            return 0

        if args.cmd == "mark":
            export_id = args.export_id
            if export_id is None:
                if not args.artifact:
                    raise SystemExit("Provide --export-id or --artifact")
                export_id = lookup_export_id_by_artifact(conn, Path(args.artifact).resolve())
                if export_id is None:
                    raise SystemExit(f"Artifact not found in exports: {args.artifact}")
            mark_snapshot(conn, export_id, snapshot_name=args.name, note=args.note)
            export = fetch_export_row(conn, export_id)
            artifact_path = export["artifact_path"] if "artifact_path" in export.keys() and export["artifact_path"] else export["workbook_path"]
            print(
                json.dumps(
                    {
                        "snapshot_name": args.name,
                        "export_id": export_id,
                        "artifact_path": artifact_path,
                        "note": args.note,
                    },
                    ensure_ascii=True,
                    indent=2,
                )
            )
            return 0

        raise SystemExit(f"Unknown command: {args.cmd}")
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
