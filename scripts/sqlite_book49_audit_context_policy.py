#!/usr/bin/env python3
"""Materialize book49 residual audit context, no promotion/gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    conn = sqlite3.connect(args.db, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS book49_audit_context_policy_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_book49_residual_run_id INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS book49_audit_context_policy_items (
            run_id INTEGER NOT NULL,
            context_id TEXT NOT NULL,
            policy_status TEXT NOT NULL,
            policy_confidence REAL NOT NULL,
            books_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, context_id)
        );
        """
    )
    source_run_id = latest_id(conn, "book49_residual_negative_probe_runs")
    source = conn.execute("SELECT * FROM book49_residual_negative_probe_runs WHERE run_id=?", (source_run_id,)).fetchone()
    evidence = {
        "source_book49_residual_run_id": source_run_id,
        "decision": source["decision"],
        "book49_hit_count": int(source["book49_hit_count"]),
        "control_hit_book_count": int(source["control_hit_book_count"]),
        "singleton_o32_count": int(source["singleton_o32_count"]),
        "residual_score": float(source["residual_score"]),
        "scope": "book49_residual_audit_only",
        "gloss_allowed": False,
    }
    cur = conn.execute(
        "INSERT INTO book49_audit_context_policy_runs (created_at, source_book49_residual_run_id, decision, payload_json) VALUES (?, ?, ?, ?)",
        (utc_now(), source_run_id, "BOOK49_AUDIT_CONTEXT_READY", jdump({"evidence": evidence, "gloss_allowed": False})),
    )
    run_id = int(cur.lastrowid)
    conn.execute(
        """
        INSERT INTO book49_audit_context_policy_items
            (run_id, context_id, policy_status, policy_confidence, books_json,
             evidence_json, next_action, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "AUDIT_BOOK49_O32_NEEI_RESIDUAL_CONTEXT",
            "AUDIT_CONTEXT",
            0.38,
            jdump(["49"]),
            jdump(evidence),
            "retain_as_residual_negative_control_do_not_promote_o32_or_neei",
            jdump({"evidence": evidence, "gloss_allowed": False}),
        ),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "BOOK49_AUDIT_CONTEXT_READY", "context_id": "AUDIT_BOOK49_O32_NEEI_RESIDUAL_CONTEXT", "policy_status": "AUDIT_CONTEXT", "policy_confidence": 0.38, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
