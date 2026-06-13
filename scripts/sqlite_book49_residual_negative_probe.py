#!/usr/bin/env python3
"""Probe book 49 residual/O32 patterns against repetition controls, no gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
PATTERNS = {
    "O32_SINGLETON_CONTEXT": ["O32"],
    "NEEI_RESIDUAL": ["N", "E", "E", "I"],
    "EEILEE_RESIDUAL": ["E", "E", "I", "L", "E", "E"],
    "LEII_SEAM": ["L", "E", "I", "I"],
}
CONTROLS = {"24", "31", "32", "37", "56", "57", "58", "59"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def find_positions(tokens: list[str], pattern: list[str]) -> list[int]:
    size = len(pattern)
    return [idx for idx in range(0, len(tokens) - size + 1) if tokens[idx : idx + size] == pattern]


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    conn = sqlite3.connect(args.db, timeout=30)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS book49_residual_negative_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_row0_variant_run_id INTEGER NOT NULL,
            book49_hit_count INTEGER NOT NULL,
            control_hit_book_count INTEGER NOT NULL,
            singleton_o32_count INTEGER NOT NULL,
            residual_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS book49_residual_negative_items (
            run_id INTEGER NOT NULL,
            pattern_id TEXT NOT NULL,
            bookid TEXT NOT NULL,
            positions_json TEXT NOT NULL,
            residual_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, pattern_id, bookid)
        );
        """
    )
    row0_run_id = latest_id(conn, "row0_variant_frontier_runs")
    rows = conn.execute("SELECT bookid, tokens_json FROM row0_variant_book_tokens WHERE run_id=?", (row0_run_id,)).fetchall()
    tokens_by_book = {str(bookid): json.loads(tokens_json or "[]") for bookid, tokens_json in rows}
    cur = conn.execute(
        """
        INSERT INTO book49_residual_negative_probe_runs
            (created_at, source_row0_variant_run_id, book49_hit_count,
             control_hit_book_count, singleton_o32_count, residual_score, decision, payload_json)
        VALUES (?, ?, 0, 0, 0, 0, ?, ?)
        """,
        (utc_now(), row0_run_id, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    book49_hits = 0
    control_books = set()
    singleton_o32 = 0
    items = []
    for pattern_id, pattern in PATTERNS.items():
        for bookid, tokens in tokens_by_book.items():
            positions = find_positions(tokens, pattern)
            if not positions:
                continue
            if bookid == "49":
                book49_hits += len(positions)
                status = "BOOK49_RESIDUAL_HIT"
                next_action = "retain_as_book49_residual_audit"
                if pattern_id == "O32_SINGLETON_CONTEXT":
                    singleton_o32 += len(positions)
            elif bookid in CONTROLS:
                control_books.add(bookid)
                status = "CONTROL_REPETITION_HIT"
                next_action = "blocks_function_promotion"
            else:
                status = "OUTSIDE_HIT"
                next_action = "background_or_unscored"
            payload = {"pattern_id": pattern_id, "bookid": bookid, "positions": positions, "gloss_allowed": False}
            items.append(payload)
            conn.execute(
                """
                INSERT INTO book49_residual_negative_items
                    (run_id, pattern_id, bookid, positions_json, residual_status, next_action, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, pattern_id, bookid, jdump(positions), status, next_action, jdump(payload)),
            )
    score = round(min(0.40, book49_hits * 0.04) + min(0.30, len(control_books) * 0.05) + (0.20 if singleton_o32 else 0.0), 4)
    decision = "BOOK49_RESIDUAL_AUDIT_ONLY_NO_GLOSS"
    conn.execute(
        """
        UPDATE book49_residual_negative_probe_runs
        SET book49_hit_count=?, control_hit_book_count=?, singleton_o32_count=?,
            residual_score=?, decision=?, payload_json=?
        WHERE run_id=?
        """,
        (book49_hits, len(control_books), singleton_o32, score, decision, jdump({"items": items, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "book49_hit_count": book49_hits, "control_hit_book_count": len(control_books), "singleton_o32_count": singleton_o32, "residual_score": score, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
