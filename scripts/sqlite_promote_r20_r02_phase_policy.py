#!/usr/bin/env python3
"""Promote selected R20/R02 local phase frames, blocking global R gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
PROMOTE = {
    "R20_VAETRFEVAST_BLOCK": ("FRAME_R20_VAETRFEVAST_BLOCK", 0.80),
    "R02_TRVEIIVNTBB_BRIDGE": ("FRAME_R02_TRVEIIVNTBB_BRIDGE", 0.78),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS r20_r02_policy_override_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_r20_r02_run_id INTEGER NOT NULL,
            promoted_count INTEGER NOT NULL,
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

    conn = sqlite3.connect(args.db, timeout=30)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    source_run_id = latest_id(conn, "r20_r02_phase_frame_probe_runs")
    items = conn.execute(
        """
        SELECT *
        FROM r20_r02_phase_frame_items
        WHERE run_id=?
        """,
        (source_run_id,),
    ).fetchall()
    by_frame = {row["frame_key"]: row for row in items}

    promoted: list[dict[str, Any]] = []
    for frame_key, (function_id, confidence) in PROMOTE.items():
        item = by_frame.get(frame_key)
        if not item or item["phase_status"] != "PHASE_FRAME_READY":
            continue
        evidence = {
            "source_r20_r02_run_id": source_run_id,
            "frame_key": frame_key,
            "phase_score": float(item["phase_score"]),
            "occurrence_count": int(item["occurrence_count"]),
            "book_count": int(item["book_count"]),
            "canonical_context_count": int(item["canonical_context_count"]),
            "edge_supported_count": int(item["edge_supported_count"]),
            "scope": "local_phase_frame_not_global_R",
            "gloss_allowed": False,
        }
        policy = conn.execute(
            """
            SELECT *
            FROM row0_function_policy_items
            WHERE function_id=?
            ORDER BY run_id DESC
            LIMIT 1
            """,
            (function_id,),
        ).fetchone()
        if policy is None:
            continue
        conn.execute(
            """
            UPDATE row0_function_policy_items
            SET policy_status='FUNCTION_READY',
                policy_confidence=?,
                policy_decision='promote_local_r_phase_frame_no_gloss',
                policy_reason='R20/R02 frame has stable local context and validated contig support; R remains non-global',
                gloss_allowed=0,
                hard_decode_action='preserve_local_phase_frame_no_global_r_gloss',
                next_action='use_as_phase_boundary_or_bridge_no_plaintext',
                evidence_json=?,
                payload_json=?
            WHERE run_id=? AND function_id=?
            """,
            (
                confidence,
                jdump(evidence),
                jdump({"evidence": evidence}),
                policy["run_id"],
                function_id,
            ),
        )
        promoted.append({"function_id": function_id, "confidence": confidence, "evidence": evidence})

    decision = "R20_R02_PHASE_POLICY_APPLIED" if promoted else "R20_R02_PHASE_POLICY_NO_PROMOTION"
    cur = conn.execute(
        """
        INSERT INTO r20_r02_policy_override_runs
            (created_at, source_r20_r02_run_id, promoted_count, decision, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (utc_now(), source_run_id, len(promoted), decision, jdump({"promoted": promoted, "gloss_allowed": False})),
    )
    conn.commit()
    print(json.dumps({"run_id": int(cur.lastrowid), "decision": decision, "promoted_count": len(promoted), "promoted": [{"function_id": row["function_id"], "confidence": row["confidence"]} for row in promoted], "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
