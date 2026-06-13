#!/usr/bin/env python3
"""Promote C68 FATCT as a local NAESE slot subfunction, no global C68 gloss."""

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
        CREATE TABLE IF NOT EXISTS c68_fatct_policy_override_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_c68_fatct_run_id INTEGER NOT NULL,
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

    source_run_id = latest_id(conn, "c68_fatct_slot_probe_runs")
    source = conn.execute("SELECT * FROM c68_fatct_slot_probe_runs WHERE run_id=?", (source_run_id,)).fetchone()
    policy = conn.execute(
        """
        SELECT *
        FROM row0_function_policy_items
        WHERE function_id='FRAME_C68_FATCT_SLOT'
        ORDER BY run_id DESC
        LIMIT 1
        """
    ).fetchone()
    if policy is None:
        raise SystemExit("missing FRAME_C68_FATCT_SLOT policy item")

    if source["decision"] == "C68_FATCT_NAESE_SLOT_SUBFUNCTION_READY_NO_GLOSS":
        decision = "C68_FATCT_PROMOTED_TO_SLOT_CLASSIFIER_NO_GLOSS"
        new_status = "SLOT_CLASSIFIER"
        new_conf = 0.81
    else:
        decision = "C68_FATCT_NOT_PROMOTED"
        new_status = policy["policy_status"]
        new_conf = float(policy["policy_confidence"])

    evidence = {
        "source_c68_fatct_run_id": source_run_id,
        "decision": source["decision"],
        "slot_score": float(source["slot_score"]),
        "occurrence_count": int(source["occurrence_count"]),
        "book_count": int(source["book_count"]),
        "canonical_context_count": int(source["canonical_context_count"]),
        "edge_supported_count": int(source["edge_supported_count"]),
        "gloss_allowed": False,
        "scope": "local_naese_fatct_slot_not_global_c68",
    }
    cur = conn.execute(
        """
        INSERT INTO c68_fatct_policy_override_runs
            (created_at, source_c68_fatct_run_id, old_policy_status,
             new_policy_status, old_policy_confidence, new_policy_confidence,
             decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (utc_now(), source_run_id, policy["policy_status"], new_status, float(policy["policy_confidence"]), new_conf, decision, jdump(evidence)),
    )
    run_id = int(cur.lastrowid)
    if decision == "C68_FATCT_PROMOTED_TO_SLOT_CLASSIFIER_NO_GLOSS":
        conn.execute(
            """
            UPDATE row0_function_policy_items
            SET policy_status='SLOT_CLASSIFIER',
                policy_confidence=?,
                policy_decision='promote_c68_fatct_as_local_naese_slot_no_gloss',
                policy_reason='FATCT has stable NAESE slot context and validated contig support, but C68 remains non-global',
                gloss_allowed=0,
                hard_decode_action='classify_local_naese_fatct_slot_no_global_c68_gloss',
                next_action='use_as_slot_boundary_inside_naese_ivifast_no_plaintext',
                evidence_json=?,
                payload_json=?
            WHERE run_id=? AND function_id='FRAME_C68_FATCT_SLOT'
            """,
            (new_conf, jdump(evidence), jdump({"override_run_id": run_id, "evidence": evidence}), policy["run_id"]),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "old_policy_status": policy["policy_status"], "new_policy_status": new_status, "old_policy_confidence": float(policy["policy_confidence"]), "new_policy_confidence": new_conf, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
