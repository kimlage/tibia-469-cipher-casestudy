#!/usr/bin/env python3
"""Materialize book30 split-frame local context, no gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS book30_split_context_policy_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_book30_split_run_id INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS book30_split_context_policy_items (
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


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db, timeout=30)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    source_run_id = latest_id(conn, "book30_split_frame_probe_runs")
    source = conn.execute("SELECT * FROM book30_split_frame_probe_runs WHERE run_id=?", (source_run_id,)).fetchone()
    if source["decision"] == "BOOK30_SPLIT_CORE_CONTEXT_READY_NO_GLOSS":
        decision = "BOOK30_SPLIT_CONTEXT_POLICY_READY"
        status = "LOCAL_CONTEXT_READY"
        confidence = 0.79
    else:
        decision = "BOOK30_SPLIT_CONTEXT_POLICY_AUDIT_ONLY"
        status = "AUDIT_ONLY"
        confidence = 0.35
    evidence = {
        "source_book30_split_run_id": source_run_id,
        "split_decision": source["decision"],
        "split_score": float(source["split_score"]),
        "core_positive_count": int(source["core_positive_count"]),
        "core_negative_count": int(source["core_negative_count"]),
        "suffix_book30_only": int(source["suffix_book30_only"]),
        "scope": "book30_local_split_context_not_plaintext",
        "gloss_allowed": False,
    }
    cur = conn.execute(
        """
        INSERT INTO book30_split_context_policy_runs
            (created_at, source_book30_split_run_id, decision, payload_json)
        VALUES (?, ?, ?, ?)
        """,
        (utc_now(), source_run_id, decision, jdump({"evidence": evidence, "gloss_allowed": False})),
    )
    run_id = int(cur.lastrowid)
    conn.execute(
        """
        INSERT INTO book30_split_context_policy_items
            (run_id, context_id, policy_status, policy_confidence,
             books_json, evidence_json, next_action, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "LOCAL_BOOK30_SPLIT_CORE_CONTEXT",
            status,
            confidence,
            jdump(["30", "12", "21", "26"]),
            jdump(evidence),
            "use_book30_core_as_local_alignment_context_no_gloss",
            jdump({"evidence": evidence, "gloss_allowed": False}),
        ),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "context_id": "LOCAL_BOOK30_SPLIT_CORE_CONTEXT", "policy_status": status, "policy_confidence": confidence, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
