#!/usr/bin/env python3
"""Resolve VTLRNEFIE semantic anomaly as suspect display inside VINVIN frame."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
PATTERN = ["V", "T", "L", "R20", "N", "E", "F", "I", "E"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row[0]) if row else 0


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
        CREATE TABLE IF NOT EXISTS vtlrnefie_suspect_resolution_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_row0_variant_run_id INTEGER NOT NULL,
            source_anomaly_run_id INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            resolved_anomaly_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS vtlrnefie_suspect_resolution_items (
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
        INSERT INTO vtlrnefie_suspect_resolution_runs
            (created_at, source_row0_variant_run_id, source_anomaly_run_id,
             hit_count, book_count, resolved_anomaly_count, decision, payload_json)
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
            INSERT INTO vtlrnefie_suspect_resolution_items
                (run_id, bookid, positions_json, status, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bid,
                jdump(positions),
                "SUSPECT_DISPLAY_TOKEN_WITHIN_VINVIN_FRAME",
                "keep_vtlrnefie_as_suspect_no_fervently_no_unfertile",
                jdump(payload),
            ),
        )
    anomaly_rows = conn.execute(
        """
        SELECT rank, phrase, score, recommendation, hit_count, book_count
        FROM semantic_anomaly_audit_items
        WHERE run_id=? AND phrase LIKE '%VTLRNEFIE%'
        """,
        (anomaly_run,),
    ).fetchall()
    decision = "VTLRNEFIE_RESOLVED_AS_SUSPECT_VINVIN_FRAME_NO_GLOSS"
    conn.execute(
        """
        UPDATE vtlrnefie_suspect_resolution_runs
        SET hit_count=?, book_count=?, resolved_anomaly_count=?, decision=?, payload_json=?
        WHERE run_id=?
        """,
        (hit_count, len(books), len(anomaly_rows), decision, jdump({"books": books, "anomalies": anomaly_rows, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "hit_count": hit_count, "book_count": len(books), "resolved_anomaly_count": len(anomaly_rows), "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
