#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional


DEFAULT_SNAPSHOT_NAME = "canonical"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_snapshot_refs_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS snapshot_refs (
            name TEXT PRIMARY KEY,
            export_id INTEGER NOT NULL,
            artifact_path TEXT,
            artifact_sha256 TEXT,
            note TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_snapshot_refs_export_id ON snapshot_refs (export_id);
        """
    )
    conn.commit()


def fetch_export_row(conn: sqlite3.Connection, export_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM exports WHERE export_id = ?", (export_id,)).fetchone()
    if row is None:
        raise SystemExit(f"Export not found: {export_id}")
    return row


def table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()}


def lookup_export_id_by_artifact(conn: sqlite3.Connection, artifact_path: Path) -> Optional[int]:
    ensure_snapshot_refs_schema(conn)
    cols = table_columns(conn, "exports")
    for path_col in ("artifact_path", "workbook_path"):
        if path_col not in cols:
            continue
        row = conn.execute(
            f"""
            SELECT export_id
            FROM exports
            WHERE "{path_col}" = ?
            ORDER BY export_id DESC
            LIMIT 1
            """,
            (str(artifact_path),),
        ).fetchone()
        if row is not None:
            return int(row[0])
    if artifact_path.exists():
        digest = sha256_file(artifact_path)
        for sha_col in ("artifact_sha256", "workbook_sha256"):
            if sha_col not in cols:
                continue
            row = conn.execute(
                f"""
                SELECT export_id
                FROM exports
                WHERE "{sha_col}" = ?
                ORDER BY export_id DESC
                LIMIT 1
                """,
                (digest,),
            ).fetchone()
            if row is not None:
                return int(row[0])
    return None


def resolve_export_id(
    conn: sqlite3.Connection,
    export_id: Optional[int] = None,
    snapshot_name: str = DEFAULT_SNAPSHOT_NAME,
) -> int:
    ensure_snapshot_refs_schema(conn)
    if export_id is not None:
        fetch_export_row(conn, int(export_id))
        return int(export_id)
    row = conn.execute(
        "SELECT export_id FROM snapshot_refs WHERE name = ?",
        (snapshot_name,),
    ).fetchone()
    if row is None:
        raise SystemExit(
            f"Snapshot ref not found: {snapshot_name}. Create it first with sqlite_snapshot_manager.py."
        )
    return int(row[0])


def mark_snapshot(
    conn: sqlite3.Connection,
    export_id: int,
    snapshot_name: str = DEFAULT_SNAPSHOT_NAME,
    note: Optional[str] = None,
) -> None:
    ensure_snapshot_refs_schema(conn)
    export = fetch_export_row(conn, export_id)
    artifact_path = export["artifact_path"] if "artifact_path" in export.keys() and export["artifact_path"] else export["workbook_path"]
    artifact_sha256 = export["artifact_sha256"] if "artifact_sha256" in export.keys() and export["artifact_sha256"] else export["workbook_sha256"]
    updated_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    conn.execute(
        """
        INSERT INTO snapshot_refs (name, export_id, artifact_path, artifact_sha256, note, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            export_id = excluded.export_id,
            artifact_path = excluded.artifact_path,
            artifact_sha256 = excluded.artifact_sha256,
            note = excluded.note,
            updated_at = excluded.updated_at
        """,
        (snapshot_name, export_id, artifact_path, artifact_sha256, note, updated_at),
    )
    conn.commit()
