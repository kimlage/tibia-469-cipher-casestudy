#!/usr/bin/env python3
"""Register TTNVVN semantic anomalies as resolved formula-slot unknowns."""

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
    return int(row[0]) if row else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    conn = sqlite3.connect(args.db, timeout=30)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS semantic_anomaly_resolution_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_anomaly_run_id INTEGER NOT NULL,
            source_probe_run_id INTEGER NOT NULL,
            family TEXT NOT NULL,
            resolved_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS semantic_anomaly_resolution_items (
            run_id INTEGER NOT NULL,
            phrase TEXT NOT NULL,
            source_rank INTEGER NOT NULL,
            source_score INTEGER NOT NULL,
            resolution_status TEXT NOT NULL,
            gloss_allowed INTEGER NOT NULL,
            reason TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, phrase)
        );
        """
    )
    anomaly_run = latest_id(conn, "semantic_anomaly_audit_items")
    probe_run = latest_id(conn, "ttnvvn_formula_slot_probe_runs")
    rows = conn.execute(
        """
        SELECT rank, phrase, score, recommendation, hit_count, book_count
        FROM semantic_anomaly_audit_items
        WHERE run_id=? AND phrase LIKE '%TTNVVN%'
        ORDER BY rank
        """,
        (anomaly_run,),
    ).fetchall()
    cur = conn.execute(
        """
        INSERT INTO semantic_anomaly_resolution_runs
            (created_at, source_anomaly_run_id, source_probe_run_id,
             family, resolved_count, decision, payload_json)
        VALUES (?, ?, ?, ?, 0, ?, ?)
        """,
        (utc_now(), anomaly_run, probe_run, "TTNVVN_FORMULA_SLOT", "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    resolved = 0
    for rank, phrase, score, recommendation, hit_count, book_count in rows:
        evidence = {
            "source_anomaly_run_id": anomaly_run,
            "source_probe_run_id": probe_run,
            "recommendation": recommendation,
            "hit_count": hit_count,
            "book_count": book_count,
            "slot_policy": "KNOWN_STRUCTURAL_UNKNOWN_NOT_LEXICAL",
            "gloss_allowed": False,
        }
        conn.execute(
            """
            INSERT INTO semantic_anomaly_resolution_items
                (run_id, phrase, source_rank, source_score, resolution_status,
                 gloss_allowed, reason, next_action, evidence_json, payload_json)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            (
                run_id,
                phrase,
                rank,
                score,
                "RESOLVED_AS_FORMULA_SLOT_UNKNOWN_NO_GLOSS",
                "TTNVVN is a known structural unknown adjacent to formula; old tumtum/gloss is blocked",
                "keep_as_formula_shadow_plus_UNK_TTNVVN_do_not_queue_for_gloss",
                jdump(evidence),
                jdump({"evidence": evidence, "gloss_allowed": False}),
            ),
        )
        resolved += 1
    decision = "TTNVVN_ANOMALIES_RESOLVED_NO_GLOSS"
    conn.execute(
        """
        UPDATE semantic_anomaly_resolution_runs
        SET resolved_count=?, decision=?, payload_json=?
        WHERE run_id=?
        """,
        (resolved, decision, jdump({"family": "TTNVVN_FORMULA_SLOT", "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "resolved_count": resolved, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
