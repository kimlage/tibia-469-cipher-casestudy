#!/usr/bin/env python3
"""Promote O23_ONAF to controlled FUNCTION_READY after Hellgate holdout."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
FUNCTION_ID = "FRAME_O23_ONAF_FAMILY"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS row0_function_policy_override_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_policy_run_id INTEGER NOT NULL,
            source_o23_run_id INTEGER NOT NULL,
            function_id TEXT NOT NULL,
            old_policy_status TEXT,
            new_policy_status TEXT NOT NULL,
            old_policy_confidence REAL,
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

    policy_run_id = latest_id(conn, "row0_function_policy_runs")
    o23_run_id = latest_id(conn, "o23_onaf_hellgate_holdout_probe_runs")
    o23 = conn.execute(
        """
        SELECT *
        FROM o23_onaf_hellgate_holdout_probe_runs
        WHERE run_id=?
        """,
        (o23_run_id,),
    ).fetchone()
    item = conn.execute(
        """
        SELECT *
        FROM row0_function_policy_items
        WHERE run_id=? AND function_id=?
        """,
        (policy_run_id, FUNCTION_ID),
    ).fetchone()
    if item is None:
        raise SystemExit(f"missing policy item {FUNCTION_ID}")
    if o23["decision"] == "O23_ONAF_ENDPOINT_FRAME_ALIVE" and float(o23["specificity_score"]) >= 0.85:
        new_status = "FUNCTION_READY"
        new_confidence = 0.86
        decision = "O23_ONAF_PROMOTED_TO_FUNCTION_READY_NO_GLOSS"
    else:
        new_status = item["policy_status"]
        new_confidence = float(item["policy_confidence"])
        decision = "O23_ONAF_NOT_PROMOTED"

    if new_status != item["policy_status"] or abs(new_confidence - float(item["policy_confidence"])) > 1e-9:
        conn.execute(
            """
            UPDATE row0_function_policy_items
            SET policy_status=?,
                policy_confidence=?,
                policy_decision=?,
                policy_reason=?,
                next_action=?,
                promotion_gate=?,
                abandon_gate=?,
                payload_json=?
            WHERE run_id=? AND function_id=?
            """,
            (
                new_status,
                new_confidence,
                "promote_after_hellgate_o23_holdout",
                "O23_ONAF survived external Hellgate38 holdout, contig alive edge, independent support, and negative controls",
                "test_boundary_continuation_payload_no_gloss",
                "must remain O23_ONAF frame with external/contig support and no NAFIE_without_O23 drift",
                "downgrade if O23_ONAF collapses into formula or endpoint-only singleton",
                jdump({"source_o23_run_id": o23_run_id, "gloss_allowed": False}),
                policy_run_id,
                FUNCTION_ID,
            ),
        )
    conn.execute(
        """
        INSERT INTO row0_function_policy_override_runs
            (created_at, source_policy_run_id, source_o23_run_id, function_id,
             old_policy_status, new_policy_status, old_policy_confidence,
             new_policy_confidence, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            policy_run_id,
            o23_run_id,
            FUNCTION_ID,
            item["policy_status"],
            new_status,
            item["policy_confidence"],
            new_confidence,
            decision,
            jdump(dict(o23)),
        ),
    )
    conn.commit()
    print(
        json.dumps(
            {
                "decision": decision,
                "function_id": FUNCTION_ID,
                "policy_run_id": policy_run_id,
                "source_o23_run_id": o23_run_id,
                "old_policy_status": item["policy_status"],
                "new_policy_status": new_status,
                "new_policy_confidence": new_confidence,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
