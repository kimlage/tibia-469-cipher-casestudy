#!/usr/bin/env python3
"""Classify 3478 as distributed formula digit-window, no gloss/beholder."""

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
        CREATE TABLE IF NOT EXISTS anchor3478_formula_policy_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_anchor3478_run_id INTEGER NOT NULL,
            dominant_window TEXT NOT NULL,
            dominant_count INTEGER NOT NULL,
            total_hit_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS anchor3478_formula_policy_items (
            run_id INTEGER NOT NULL,
            anchor TEXT NOT NULL,
            policy_status TEXT NOT NULL,
            policy_confidence REAL NOT NULL,
            evidence_tier TEXT NOT NULL,
            reason TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, anchor)
        );
        """
    )
    source_run = latest_id(conn, "anchor3478_context_probe_runs")
    row = conn.execute(
        """
        SELECT window_digits, COUNT(*) AS n
        FROM anchor3478_context_items
        WHERE run_id=?
        GROUP BY window_digits
        ORDER BY n DESC, window_digits
        LIMIT 1
        """,
        (source_run,),
    ).fetchone()
    total = conn.execute("SELECT COUNT(*) FROM anchor3478_context_items WHERE run_id=?", (source_run,)).fetchone()[0]
    dominant_window = row[0] if row else ""
    dominant_count = int(row[1]) if row else 0
    confidence = round(dominant_count / max(1, total), 4)
    evidence = {
        "source_anchor3478_run_id": source_run,
        "dominant_window": dominant_window,
        "dominant_count": dominant_count,
        "total_hit_count": total,
        "mechanical_interpretation": "digit window aligns with LEITEL/BENNA/FIININS/BASTFN formula region",
        "blocks": ["3478_as_beholder_gloss", "3478_as_plaintext"],
        "gloss_allowed": False,
    }
    decision = "ANCHOR3478_CLASSIFIED_AS_DISTRIBUTED_FORMULA_WINDOW_NO_GLOSS"
    cur = conn.execute(
        """
        INSERT INTO anchor3478_formula_policy_runs
            (created_at, source_anchor3478_run_id, dominant_window,
             dominant_count, total_hit_count, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (utc_now(), source_run, dominant_window, dominant_count, total, decision, jdump({"evidence": evidence, "gloss_allowed": False})),
    )
    run_id = int(cur.lastrowid)
    conn.execute(
        """
        INSERT INTO anchor3478_formula_policy_items
            (run_id, anchor, policy_status, policy_confidence, evidence_tier,
             reason, next_action, evidence_json, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "3478",
            "AUDIT_FORMULA_WINDOW_NO_GLOSS",
            confidence,
            "WEAK_EXTERNAL_HYPOTHESIS_RECLASSIFIED_BY_ROW0",
            "3478 has repeated digit-window hits but maps to distributed formula region, not a standalone lexical anchor",
            "use_as_formula_boundary_audit_only_do_not_promote_beholder",
            jdump(evidence),
            jdump({"evidence": evidence, "gloss_allowed": False}),
        ),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "dominant_window": dominant_window, "dominant_count": dominant_count, "total_hit_count": total, "policy_confidence": confidence, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
