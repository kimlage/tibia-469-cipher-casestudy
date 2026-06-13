#!/usr/bin/env python3
"""Resolve TTNVVN anomaly family as formula slot unknown, no gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
PATTERN = ["L", "T", "A", "S", "T", "T", "N", "V", "V", "N", "N", "F", "I", "E"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        return 0
    return int(row[0])


def find_positions(tokens: list[str], pattern: list[str]) -> list[int]:
    size = len(pattern)
    return [idx for idx in range(0, len(tokens) - size + 1) if tokens[idx : idx + size] == pattern]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    conn = sqlite3.connect(args.db, timeout=30)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ttnvvn_formula_slot_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_row0_variant_run_id INTEGER NOT NULL,
            source_anomaly_run_id INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            anomaly_phrase_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ttnvvn_formula_slot_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            positions_json TEXT NOT NULL,
            status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )
    row0_run = latest_id(conn, "row0_variant_frontier_runs")
    anomaly_run = latest_id(conn, "semantic_anomaly_audit_items")
    rows = conn.execute("SELECT bookid, tokens_json FROM row0_variant_book_tokens WHERE run_id=?", (row0_run,)).fetchall()
    cur = conn.execute(
        """
        INSERT INTO ttnvvn_formula_slot_probe_runs
            (created_at, source_row0_variant_run_id, source_anomaly_run_id,
             hit_count, book_count, anomaly_phrase_count, decision, payload_json)
        VALUES (?, ?, ?, 0, 0, 0, ?, ?)
        """,
        (utc_now(), row0_run, anomaly_run, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    hit_count = 0
    books = []
    for bookid, tokens_json in rows:
        tokens = json.loads(tokens_json or "[]")
        positions = find_positions(tokens, PATTERN)
        if not positions:
            continue
        bid = str(bookid)
        books.append(bid)
        hit_count += len(positions)
        payload = {"bookid": bid, "positions": positions, "pattern": " ".join(PATTERN), "gloss_allowed": False}
        conn.execute(
            """
            INSERT INTO ttnvvn_formula_slot_items
                (run_id, bookid, positions_json, status, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bid,
                jdump(positions),
                "FORMULA_SLOT_UNKNOWN_TTNVVN",
                "keep_ttnvvn_as_unk_formula_slot_no_tumtum_no_gloss",
                jdump(payload),
            ),
        )
    anomaly_count = conn.execute(
        "SELECT COUNT(*) FROM semantic_anomaly_audit_items WHERE run_id=? AND phrase LIKE '%TTNVVN%'",
        (anomaly_run,),
    ).fetchone()[0]
    decision = "TTNVVN_FORMULA_SLOT_RESOLVED_AS_UNKNOWN_NO_GLOSS"
    conn.execute(
        """
        UPDATE ttnvvn_formula_slot_probe_runs
        SET hit_count=?, book_count=?, anomaly_phrase_count=?, decision=?, payload_json=?
        WHERE run_id=?
        """,
        (hit_count, len(books), anomaly_count, decision, jdump({"books": books, "pattern": " ".join(PATTERN), "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "hit_count": hit_count, "book_count": len(books), "anomaly_phrase_count": anomaly_count, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
