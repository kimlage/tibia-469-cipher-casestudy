#!/usr/bin/env python3
"""Promote VINVIN_VTLR after suffix branch contrast passes."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
FUNCTION_ID = "VINVIN_VTLR"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS vinvin_suffix_policy_override_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_policy_run_id INTEGER NOT NULL,
            source_vinvin_suffix_run_id INTEGER NOT NULL,
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
    suffix_run_id = latest_id(conn, "vinvin_suffix_contrast_probe_runs")
    suffix = conn.execute("SELECT * FROM vinvin_suffix_contrast_probe_runs WHERE run_id=?", (suffix_run_id,)).fetchone()
    item = conn.execute(
        "SELECT * FROM row0_function_policy_items WHERE run_id=? AND function_id=?",
        (policy_run_id, FUNCTION_ID),
    ).fetchone()
    if item is None:
        raise SystemExit(f"missing policy item {FUNCTION_ID}")
    if suffix["decision"] == "VINVIN_SUFFIX_BRANCHES_FUNCTION_READY" and float(suffix["branch_score"]) >= 0.85:
        new_status = "FUNCTION_READY"
        new_confidence = 0.84
        decision = "VINVIN_VTLR_PROMOTED_TO_FUNCTION_READY_NO_GLOSS"
    else:
        new_status = item["policy_status"]
        new_confidence = float(item["policy_confidence"])
        decision = "VINVIN_VTLR_NOT_PROMOTED"
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
                "promote_after_suffix_branch_contrast",
                "VINVIN/VTLR suffix branches survived contig support and negative same-operator controls",
                "test_branch_payloads_no_gloss",
                "must preserve branch classes and avoid formula/plaintext collapse",
                "downgrade if branch score depends on formula masks or O23 singleton",
                jdump({"source_vinvin_suffix_run_id": suffix_run_id, "gloss_allowed": False}),
                policy_run_id,
                FUNCTION_ID,
            ),
        )
    conn.execute(
        """
        INSERT INTO vinvin_suffix_policy_override_runs
            (created_at, source_policy_run_id, source_vinvin_suffix_run_id,
             function_id, old_policy_status, new_policy_status,
             old_policy_confidence, new_policy_confidence, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            policy_run_id,
            suffix_run_id,
            FUNCTION_ID,
            item["policy_status"],
            new_status,
            item["policy_confidence"],
            new_confidence,
            decision,
            jdump(dict(suffix)),
        ),
    )
    conn.commit()
    print(
        json.dumps(
            {
                "decision": decision,
                "function_id": FUNCTION_ID,
                "policy_run_id": policy_run_id,
                "source_vinvin_suffix_run_id": suffix_run_id,
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
