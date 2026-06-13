#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Maintain probe registry inside SQLite")
    sub = parser.add_subparsers(dest="cmd", required=True)

    init_p = sub.add_parser("init", help="Create probe registry tables")
    init_p.add_argument("--db", default=DEFAULT_DB)

    add_p = sub.add_parser("add", help="Add a probe run record")
    add_p.add_argument("--db", default=DEFAULT_DB)
    add_p.add_argument("--family", required=True)
    add_p.add_argument("--probe-name", required=True)
    add_p.add_argument("--artifact", required=True)
    add_p.add_argument("--status", required=True)
    add_p.add_argument("--outcome", required=True)
    add_p.add_argument("--skip-top", default=None)
    add_p.add_argument("--notes", default=None)
    add_p.add_argument("--expected-failure-mode", default=None)
    add_p.add_argument("--reason-selected", default=None)

    list_p = sub.add_parser("list", help="List recent probe runs")
    list_p.add_argument("--db", default=DEFAULT_DB)
    list_p.add_argument("--family", default=None)
    list_p.add_argument("--limit", type=int, default=20)

    dead_p = sub.add_parser("dead", help="Summarize likely dead families")
    dead_p.add_argument("--db", default=DEFAULT_DB)
    dead_p.add_argument("--limit", type=int, default=50)
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS probe_runs (
            probe_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            family TEXT NOT NULL,
            probe_name TEXT NOT NULL,
            workbook_path TEXT NOT NULL,
            artifact_path TEXT,
            status TEXT NOT NULL,
            outcome TEXT NOT NULL,
            skip_top TEXT,
            expected_failure_mode TEXT,
            reason_selected TEXT,
            notes TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_probe_runs_family ON probe_runs (family, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_probe_runs_outcome ON probe_runs (outcome, created_at DESC);
        """
    )
    cols = {row[1] for row in conn.execute("PRAGMA table_info(probe_runs)").fetchall()}
    if "artifact_path" not in cols:
        conn.execute('ALTER TABLE probe_runs ADD COLUMN artifact_path TEXT')
        conn.execute("UPDATE probe_runs SET artifact_path = workbook_path WHERE artifact_path IS NULL")
    conn.commit()


def add_probe(
    conn: sqlite3.Connection,
    family: str,
    probe_name: str,
    artifact: str,
    status: str,
    outcome: str,
    skip_top: Optional[str],
    notes: Optional[str],
    expected_failure_mode: Optional[str],
    reason_selected: Optional[str],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO probe_runs (
            created_at, family, probe_name, workbook_path, artifact_path, status, outcome, skip_top,
            expected_failure_mode, reason_selected, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            family,
            probe_name,
            artifact,
            artifact,
            status,
            outcome,
            skip_top,
            expected_failure_mode,
            reason_selected,
            notes,
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_runs(conn: sqlite3.Connection, family: Optional[str], limit: int) -> List[sqlite3.Row]:
    if family:
        return conn.execute(
            """
            SELECT * FROM probe_runs
            WHERE family = ?
            ORDER BY probe_id DESC
            LIMIT ?
            """,
            (family, limit),
        ).fetchall()
    return conn.execute(
        """
        SELECT * FROM probe_runs
        ORDER BY probe_id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def dead_summary(conn: sqlite3.Connection, limit: int) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            family,
            COUNT(*) AS runs,
            SUM(CASE WHEN outcome = 'DP_UNUSED' THEN 1 ELSE 0 END) AS dp_unused,
            SUM(CASE WHEN outcome = 'GT_HARD_FAIL' THEN 1 ELSE 0 END) AS gt_hard_fail,
            SUM(CASE WHEN outcome = 'NO_OP' THEN 1 ELSE 0 END) AS no_op,
            MAX(created_at) AS last_seen
        FROM probe_runs
        GROUP BY family
        HAVING
            SUM(CASE WHEN outcome = 'DP_UNUSED' THEN 1 ELSE 0 END) >= 2
            OR SUM(CASE WHEN outcome = 'GT_HARD_FAIL' THEN 1 ELSE 0 END) >= 2
            OR SUM(CASE WHEN outcome = 'NO_OP' THEN 1 ELSE 0 END) >= 2
        ORDER BY last_seen DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        if args.cmd == "init":
            init_schema(conn)
            print(json.dumps({"ok": True, "db": args.db}, ensure_ascii=True))
            return 0
        if args.cmd == "add":
            init_schema(conn)
            probe_id = add_probe(
                conn,
                family=args.family,
                probe_name=args.probe_name,
                artifact=args.artifact,
                status=args.status,
                outcome=args.outcome,
                skip_top=args.skip_top,
                notes=args.notes,
                expected_failure_mode=args.expected_failure_mode,
                reason_selected=args.reason_selected,
            )
            print(json.dumps({"probe_id": probe_id}, ensure_ascii=True))
            return 0
        if args.cmd == "list":
            init_schema(conn)
            rows = [dict(r) for r in list_runs(conn, args.family, args.limit)]
            print(json.dumps(rows, ensure_ascii=True, indent=2))
            return 0
        if args.cmd == "dead":
            init_schema(conn)
            rows = [dict(r) for r in dead_summary(conn, args.limit)]
            print(json.dumps(rows, ensure_ascii=True, indent=2))
            return 0
        raise SystemExit(f"Unknown command: {args.cmd}")
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
