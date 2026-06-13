#!/usr/bin/env python3
"""Materialize local pair contexts from zero-coverage alignment probes."""

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
        CREATE TABLE IF NOT EXISTS zero_pair_context_policy_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_zero_pair_run_id INTEGER NOT NULL,
            context_count INTEGER NOT NULL,
            audit_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS zero_pair_context_policy_items (
            run_id INTEGER NOT NULL,
            context_id TEXT NOT NULL,
            source_pair_id TEXT NOT NULL,
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
    source_run_id = latest_id(conn, "zero_pair_alignment_probe_runs")
    rows = conn.execute(
        """
        SELECT *
        FROM zero_pair_alignment_items
        WHERE run_id=?
        ORDER BY pair_id
        """,
        (source_run_id,),
    ).fetchall()
    cur = conn.execute(
        """
        INSERT INTO zero_pair_context_policy_runs
            (created_at, source_zero_pair_run_id, context_count, audit_count, decision, payload_json)
        VALUES (?, ?, 0, 0, ?, ?)
        """,
        (utc_now(), source_run_id, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    context_count = 0
    audit_count = 0
    summaries: list[dict[str, Any]] = []
    for row in rows:
        status = row["alignment_status"]
        if status == "PAIR_TRUNCATION_ALIGNMENT_READY":
            context_id = "LOCAL_PAIR_20_54_TRUNCATION_ALIGNMENT"
            policy_status = "LOCAL_CONTEXT_READY"
            confidence = 0.74
            next_action = "use_for_local_boundary_alignment_no_gloss"
        elif status == "PAIR_MICROTEMPLATE_READY":
            context_id = "LOCAL_PAIR_25_39_FAST_BEIE_MICROTEMPLATE"
            policy_status = "LOCAL_CONTEXT_READY"
            confidence = 0.72
            next_action = "use_as_short_microtemplate_no_gloss"
        elif status == "PAIR_CONTEXT_ALIGNMENT":
            context_id = "LOCAL_PAIR_8_23_C68_CONTEXT_ALIGNMENT"
            policy_status = "AUDIT_CONTEXT"
            confidence = 0.45
            next_action = "keep_as_c68_context_alignment_no_global_c"
        else:
            context_id = f'LOCAL_{row["pair_id"]}_AUDIT'
            policy_status = "AUDIT_ONLY"
            confidence = 0.30
            next_action = "keep_as_pair_similarity_control"
        if policy_status == "LOCAL_CONTEXT_READY":
            context_count += 1
        else:
            audit_count += 1
        evidence = {
            "source_zero_pair_run_id": source_run_id,
            "pair_id": row["pair_id"],
            "left_bookid": row["left_bookid"],
            "right_bookid": row["right_bookid"],
            "lcs_len": int(row["lcs_len"]),
            "lcs_ratio_shorter": float(row["lcs_ratio_shorter"]),
            "lcs_ratio_longer": float(row["lcs_ratio_longer"]),
            "gloss_allowed": False,
        }
        summaries.append({"context_id": context_id, "policy_status": policy_status, "confidence": confidence})
        conn.execute(
            """
            INSERT INTO zero_pair_context_policy_items
                (run_id, context_id, source_pair_id, policy_status, policy_confidence,
                 books_json, evidence_json, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                context_id,
                row["pair_id"],
                policy_status,
                confidence,
                jdump([row["left_bookid"], row["right_bookid"]]),
                jdump(evidence),
                next_action,
                jdump({"evidence": evidence, "gloss_allowed": False}),
            ),
        )
    decision = "ZERO_PAIR_CONTEXT_POLICY_READY" if context_count else "ZERO_PAIR_CONTEXT_POLICY_AUDIT_ONLY"
    conn.execute(
        """
        UPDATE zero_pair_context_policy_runs
        SET context_count=?, audit_count=?, decision=?, payload_json=?
        WHERE run_id=?
        """,
        (context_count, audit_count, decision, jdump({"items": summaries, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "context_count": context_count, "audit_count": audit_count, "items": summaries, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
