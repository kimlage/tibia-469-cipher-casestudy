#!/usr/bin/env python3
"""Promote C86 operator frame conservatively when refined contig probe supports it."""

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
        CREATE TABLE IF NOT EXISTS c86_policy_override_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_c86_refined_run_id INTEGER NOT NULL,
            old_policy_status TEXT NOT NULL,
            new_policy_status TEXT NOT NULL,
            old_policy_confidence REAL NOT NULL,
            new_policy_confidence REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
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

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    c86_run_id = latest_id(conn, "c86_contig_refined_probe_runs")
    c86_run = conn.execute(
        "SELECT * FROM c86_contig_refined_probe_runs WHERE run_id=?",
        (c86_run_id,),
    ).fetchone()
    policy = conn.execute(
        """
        SELECT *
        FROM row0_function_policy_items
        WHERE function_id='FRAME_C86_ICE_OPERATOR_OPEN'
        ORDER BY run_id DESC
        LIMIT 1
        """
    ).fetchone()
    if policy is None:
        raise SystemExit("missing FRAME_C86_ICE_OPERATOR_OPEN policy item")

    if c86_run["decision"] != "C86_OPERATOR_PAYLOAD_BRANCHES_READY_NO_GLOSS":
        decision = "C86_POLICY_NOT_PROMOTED"
        new_status = policy["policy_status"]
        new_confidence = float(policy["policy_confidence"])
    else:
        decision = "C86_PROMOTED_TO_FUNCTION_READY_NO_GLOSS"
        new_status = "FUNCTION_READY"
        new_confidence = 0.82

    evidence = {
        "source_c86_refined_run_id": c86_run_id,
        "c86_decision": c86_run["decision"],
        "refined_score": float(c86_run["refined_score"]),
        "c86_occurrence_count": int(c86_run["c86_occurrence_count"]),
        "c86_book_count": int(c86_run["c86_book_count"]),
        "edge_supported_occurrence_count": int(c86_run["edge_supported_occurrence_count"]),
        "edge_supported_class_count": int(c86_run["edge_supported_class_count"]),
        "gloss_allowed": False,
    }
    cur = conn.execute(
        """
        INSERT INTO c86_policy_override_runs
            (created_at, source_c86_refined_run_id, old_policy_status,
             new_policy_status, old_policy_confidence, new_policy_confidence,
             decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            c86_run_id,
            policy["policy_status"],
            new_status,
            float(policy["policy_confidence"]),
            new_confidence,
            decision,
            jdump(evidence),
        ),
    )
    override_run_id = int(cur.lastrowid)
    if decision == "C86_PROMOTED_TO_FUNCTION_READY_NO_GLOSS":
        conn.execute(
            """
            UPDATE row0_function_policy_items
            SET policy_status='FUNCTION_READY',
                policy_confidence=?,
                policy_decision='promote_c86_operator_payload_frame_no_gloss',
                policy_reason='refined contig-token probe found two edge-supported C86 payload branches',
                gloss_allowed=0,
                hard_decode_action='preserve_as_operator_payload_frame_no_global_C_gloss',
                next_action='track_c86_payload_branches_no_plaintext',
                evidence_json=?,
                payload_json=?
            WHERE run_id=? AND function_id='FRAME_C86_ICE_OPERATOR_OPEN'
            """,
            (
                new_confidence,
                jdump(evidence),
                jdump({"override_run_id": override_run_id, "evidence": evidence}),
                policy["run_id"],
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": override_run_id,
                "decision": decision,
                "old_policy_status": policy["policy_status"],
                "new_policy_status": new_status,
                "old_policy_confidence": float(policy["policy_confidence"]),
                "new_policy_confidence": new_confidence,
                "gloss_allowed": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
