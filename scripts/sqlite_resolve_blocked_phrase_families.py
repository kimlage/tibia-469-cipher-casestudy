#!/usr/bin/env python3
"""Resolve anomaly phrases covered by existing blocked phrase families."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
FAMILIES = [
    ("FAST_FINE_INTO_STALE_MACRO", ["fast fine into", "fine into a", "into a a", "a a the", "you've i fast", "i fast fine", "set you've i"]),
    ("FATCT_DISPLAY_SEAM", ["fact with with", "with with set", "fact with with set", "set you've i"]),
    ("BELITTLE_MEN_DISPLAY_ONLY", ["if belittle men", "belittle men"]),
    ("INFINITE_FORMULA_SHADOW", ["infinite fasten infinity", "fasten infinity last", "i infinite fasten"]),
]


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
        CREATE TABLE IF NOT EXISTS blocked_phrase_family_resolution_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_anomaly_run_id INTEGER NOT NULL,
            family_count INTEGER NOT NULL,
            resolved_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS blocked_phrase_family_resolution_items (
            run_id INTEGER NOT NULL,
            family_id TEXT NOT NULL,
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
    cur = conn.execute(
        """
        INSERT INTO blocked_phrase_family_resolution_runs
            (created_at, source_anomaly_run_id, family_count, resolved_count, decision, payload_json)
        VALUES (?, ?, ?, 0, ?, ?)
        """,
        (utc_now(), anomaly_run, len(FAMILIES), "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    resolved = 0
    seen = set()
    for family_id, anchors in FAMILIES:
        clauses = " OR ".join(["phrase LIKE ?" for _ in anchors])
        params = [f"%{anchor}%" for anchor in anchors]
        rows = conn.execute(
            f"""
            SELECT rank, phrase, score, recommendation, hit_count, book_count
            FROM semantic_anomaly_audit_items
            WHERE run_id=? AND ({clauses})
            ORDER BY rank
            """,
            (anomaly_run, *params),
        ).fetchall()
        for rank, phrase, score, recommendation, hit_count, book_count in rows:
            if phrase in seen:
                continue
            seen.add(phrase)
            evidence = {
                "family_id": family_id,
                "source_anomaly_run_id": anomaly_run,
                "recommendation": recommendation,
                "hit_count": hit_count,
                "book_count": book_count,
                "covered_by_existing_blocked_phrase_family": True,
                "gloss_allowed": False,
            }
            conn.execute(
                """
                INSERT INTO blocked_phrase_family_resolution_items
                    (run_id, family_id, phrase, source_rank, source_score,
                     resolution_status, gloss_allowed, reason, next_action,
                     evidence_json, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    family_id,
                    phrase,
                    rank,
                    score,
                    "RESOLVED_BY_EXISTING_BLOCKED_FAMILY_NO_GLOSS",
                    "phrase is covered by stale macro/display/formula family already blocked from hard decode",
                    "keep_as_formula_shadow_display_or_microtoken_audit_do_not_queue_for_gloss",
                    jdump(evidence),
                    jdump({"evidence": evidence, "gloss_allowed": False}),
                ),
            )
            resolved += 1
    decision = "BLOCKED_PHRASE_FAMILIES_RESOLVED_NO_GLOSS"
    conn.execute(
        "UPDATE blocked_phrase_family_resolution_runs SET resolved_count=?, decision=?, payload_json=? WHERE run_id=?",
        (resolved, decision, jdump({"gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "resolved_count": resolved, "family_count": len(FAMILIES), "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
