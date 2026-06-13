#!/usr/bin/env python3
"""Resolve i lo eye frontier as microtoken display drift, no gloss."""

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
        return 0
    return int(row[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    conn = sqlite3.connect(args.db, timeout=30)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS semantic_frontier_resolution_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_actionable_frontier_run_id INTEGER NOT NULL,
            source_probe_run_id INTEGER NOT NULL,
            resolved_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS semantic_frontier_resolution_items (
            run_id INTEGER NOT NULL,
            phrase TEXT NOT NULL,
            old_action_class TEXT NOT NULL,
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
    frontier_run = latest_id(conn, "semantic_actionable_frontier_items")
    probe_run = latest_id(conn, "iloeye_segmentation_probe_runs")
    rows = conn.execute(
        """
        SELECT phrase, action_class, recommendation, reason
        FROM semantic_actionable_frontier_items
        WHERE run_id=? AND phrase IN ('i lo eye','lo eye')
        """,
        (frontier_run,),
    ).fetchall()
    cur = conn.execute(
        """
        INSERT INTO semantic_frontier_resolution_runs
            (created_at, source_actionable_frontier_run_id, source_probe_run_id,
             resolved_count, decision, payload_json)
        VALUES (?, ?, ?, 0, ?, ?)
        """,
        (utc_now(), frontier_run, probe_run, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    resolved = 0
    for phrase, action_class, recommendation, reason in rows:
        evidence = {
            "source_actionable_frontier_run_id": frontier_run,
            "source_probe_run_id": probe_run,
            "old_action_class": action_class,
            "old_recommendation": recommendation,
            "old_reason": reason,
            "blocked_by": "semantic_blocked_phrases + iloeye_segmentation_probe",
            "gloss_allowed": False,
        }
        conn.execute(
            """
            INSERT INTO semantic_frontier_resolution_items
                (run_id, phrase, old_action_class, resolution_status, gloss_allowed,
                 reason, next_action, evidence_json, payload_json)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            (
                run_id,
                phrase,
                action_class,
                "RESOLVED_AS_MICROTOKEN_DISPLAY_DRIFT_NO_GLOSS",
                "mechanical probe shows recurrent ILEEI/EILEEIEFF display drift and blocked phrases already forbid global mutation",
                "remove_from_actionable_gloss_frontier_keep_microtoken_audit",
                jdump(evidence),
                jdump({"evidence": evidence, "gloss_allowed": False}),
            ),
        )
        resolved += 1
    decision = "ILO_EYE_FRONTIER_RESOLVED_NO_GLOSS" if resolved else "ILO_EYE_FRONTIER_ALREADY_ABSENT"
    conn.execute(
        """
        UPDATE semantic_frontier_resolution_runs
        SET resolved_count=?, decision=?, payload_json=?
        WHERE run_id=?
        """,
        (resolved, decision, jdump({"gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "resolved_count": resolved, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
