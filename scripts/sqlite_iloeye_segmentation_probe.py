#!/usr/bin/env python3
"""Resolve i lo eye as segmentation/display drift, not gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
PATTERN = ["B", "E", "E", "I", "L", "E", "E", "I", "E", "F", "F", "I", "F", "T", "L", "E", "I", "T", "E", "L", "B"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
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
        CREATE TABLE IF NOT EXISTS iloeye_segmentation_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_row0_variant_run_id INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            blocked_phrase_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS iloeye_segmentation_items (
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
    row0_run_id = latest_id(conn, "row0_variant_frontier_runs")
    rows = conn.execute("SELECT bookid, tokens_json FROM row0_variant_book_tokens WHERE run_id=?", (row0_run_id,)).fetchall()
    cur = conn.execute(
        "INSERT INTO iloeye_segmentation_probe_runs (created_at, source_row0_variant_run_id, hit_count, book_count, blocked_phrase_count, decision, payload_json) VALUES (?, ?, 0, 0, 0, ?, ?)",
        (utc_now(), row0_run_id, "PENDING", "{}"),
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
            INSERT INTO iloeye_segmentation_items
                (run_id, bookid, positions_json, status, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bid,
                jdump(positions),
                "DISPLAY_DRIFT_FORMULA_FAMILY",
                "block_i_lo_eye_plaintext_use_formula_or_suspect_marker",
                jdump(payload),
            ),
        )
    blocked = conn.execute("SELECT COUNT(*) FROM semantic_blocked_phrases WHERE phrase IN ('i lo eye','lo eye')").fetchone()[0]
    decision = "ILO_EYE_SEGMENTATION_DISPLAY_DRIFT_BLOCKED_NO_GLOSS"
    conn.execute(
        """
        UPDATE iloeye_segmentation_probe_runs
        SET hit_count=?, book_count=?, blocked_phrase_count=?, decision=?, payload_json=?
        WHERE run_id=?
        """,
        (hit_count, len(books), blocked, decision, jdump({"books": books, "pattern": " ".join(PATTERN), "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "hit_count": hit_count, "book_count": len(books), "blocked_phrase_count": blocked, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
