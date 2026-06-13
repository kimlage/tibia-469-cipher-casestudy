#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, fetch_export_row, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read translation snapshots from SQLite")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path")
    parser.add_argument("--export-id", type=int, default=None, help="Specific export_id")
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME, help="Named snapshot ref to use")
    parser.add_argument("--sheet", default=None, help="Convenience sheet table name, e.g. Books or FlowState")
    parser.add_argument("--limit", type=int, default=20, help="Row limit")
    parser.add_argument("--key", default=None, help="Key lookup for key/value style sheets")
    parser.add_argument("--summary", action="store_true", help="Print a quick operational summary")
    parser.add_argument("--latest-snapshot", action="store_true", help="Print latest snapshot metadata")
    parser.add_argument("--list-snapshots", type=int, default=0, help="List recent snapshots")
    return parser.parse_args()


def normalize_identifier(text: str, fallback: str) -> str:
    value = (text or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    value = value or fallback
    if value[0].isdigit():
        value = f"c_{value}"
    return value


def query_rows(conn: sqlite3.Connection, table_name: str, export_id: int, limit: int) -> List[Dict[str, Any]]:
    cur = conn.execute(
        f'SELECT * FROM "{table_name}" WHERE __export_id = ? ORDER BY __row_index LIMIT ?',
        (export_id, limit),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def row_value(row: sqlite3.Row, *names: str, default: Any = None) -> Any:
    keys = set(row.keys())
    for name in names:
        if name in keys and row[name] is not None:
            return row[name]
    return default


def count_table(conn: sqlite3.Connection, table_name: str, export_id: int | None = None) -> int:
    try:
        if export_id is None:
            return int(conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0])
        return int(conn.execute(f'SELECT COUNT(*) FROM "{table_name}" WHERE export_id = ?', (export_id,)).fetchone()[0])
    except sqlite3.OperationalError:
        return 0


def fetch_export_metadata(conn: sqlite3.Connection, export_id: int) -> Dict[str, Any]:
    export = fetch_export_row(conn, export_id)
    sheet_count = count_table(conn, "sheets", export_id)
    cell_count = count_table(conn, "cells", export_id)
    row_count = count_table(conn, "row_json", export_id)
    return {
        "snapshot_id": export_id,
        "export_id": export_id,
        "artifact_path": row_value(export, "artifact_path", "workbook_path"),
        "artifact_name": row_value(export, "artifact_name", "workbook_name"),
        "artifact_sha256": row_value(export, "artifact_sha256", "workbook_sha256"),
        "artifact_size": row_value(export, "artifact_size", "workbook_size", default=0),
        "artifact_mtime": row_value(export, "artifact_mtime", "workbook_mtime", default=0),
        "artifact_kind": row_value(export, "artifact_kind", default="legacy_xlsx"),
        "exported_at": export["exported_at"],
        "sheet_count": sheet_count,
        "cell_count": cell_count,
        "row_json_count": row_count,
    }


def list_snapshots(conn: sqlite3.Connection, limit: int) -> List[Dict[str, Any]]:
    cur = conn.execute("SELECT * FROM exports ORDER BY export_id DESC LIMIT ?", (limit,))
    out = []
    for row in cur.fetchall():
        out.append(
            {
                "snapshot_id": int(row["export_id"]),
                "artifact_path": row_value(row, "artifact_path", "workbook_path"),
                "artifact_name": row_value(row, "artifact_name", "workbook_name"),
                "artifact_kind": row_value(row, "artifact_kind", default="legacy_xlsx"),
                "exported_at": row["exported_at"],
            }
        )
    return out


def maybe_key_lookup(conn: sqlite3.Connection, sheet: str, export_id: int, key: str) -> Dict[str, Any] | None:
    table_name = f"sheet__{normalize_identifier(sheet, 'sheet')}"
    candidates = [
        ("key", "value"),
        ("setting", "value"),
        ("name", "value"),
        ("metric", "value"),
    ]
    for key_col, value_col in candidates:
        row = conn.execute(
            f'SELECT * FROM "{table_name}" WHERE __export_id = ? AND "{key_col}" = ? LIMIT 1',
            (export_id, key),
        ).fetchone()
        if row is not None:
            out = dict(row)
            out["_lookup"] = {"key_column": key_col, "value_column": value_col}
            return out
    return None


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        latest = fetch_export_metadata(conn, export_id)

        if args.latest_snapshot:
            print(json.dumps(latest, ensure_ascii=True, indent=2))
            return 0

        if args.list_snapshots > 0:
            print(json.dumps(list_snapshots(conn, args.list_snapshots), ensure_ascii=True, indent=2))
            return 0

        if args.summary or not args.sheet:
            out = {
                "latest_snapshot": latest,
                "operational_sheets": {},
            }
            for sheet in ("FlowState", "FlowSettings", "Books", "Glossary", "ExternalRefs_v115"):
                table = f"sheet__{normalize_identifier(sheet, 'sheet')}"
                rows = query_rows(conn, table, export_id, 20)
                out["operational_sheets"][sheet] = rows
            print(json.dumps(out, ensure_ascii=True, indent=2))
            return 0

        table_name = f"sheet__{normalize_identifier(args.sheet, 'sheet')}"
        if args.key:
            row = maybe_key_lookup(conn, args.sheet, export_id, args.key)
            print(json.dumps(dict(row) if row else None, ensure_ascii=True, indent=2))
            return 0

        print(json.dumps(query_rows(conn, table_name, export_id, args.limit), ensure_ascii=True, indent=2))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
