#!/usr/bin/env python3
"""Analyze 3478 digit-anchor contexts and row0 alignment, no gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
ANCHOR = "3478"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS anchor3478_context_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_books_export_id INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            unique_window_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS anchor3478_context_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            digit_pos INTEGER NOT NULL,
            left_digits TEXT NOT NULL,
            anchor TEXT NOT NULL,
            right_digits TEXT NOT NULL,
            window_digits TEXT NOT NULL,
            decodedbase TEXT NOT NULL,
            context_class TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid, digit_pos)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str, col: str = "__export_id") -> int:
    row = conn.execute(f"SELECT {col} FROM {table} ORDER BY {col} DESC LIMIT 1").fetchone()
    return int(row[col]) if row else 0


def classify(window: str) -> str:
    if window.startswith("00") or window.endswith("00") or "00" in window:
        return "ZERO_CROSSING_DIGIT_WINDOW"
    if len(set(window)) <= 4:
        return "LOW_VARIETY_NUMERIC_WINDOW"
    return "MIXED_NUMERIC_WINDOW"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db, timeout=30)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    export_id = latest_id(conn, "sheet__books")
    rows = conn.execute(
        """
        SELECT bookid, digits, decodedbase
        FROM sheet__books
        WHERE __export_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (export_id,),
    ).fetchall()
    cur = conn.execute(
        """
        INSERT INTO anchor3478_context_probe_runs
            (created_at, source_books_export_id, hit_count, book_count,
             unique_window_count, decision, payload_json)
        VALUES (?, ?, 0, 0, 0, ?, ?)
        """,
        (utc_now(), export_id, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    hit_count = 0
    books = set()
    windows = Counter()
    items = []
    for row in rows:
        digits = str(row["digits"] or "")
        start = 0
        while True:
            pos = digits.find(ANCHOR, start)
            if pos < 0:
                break
            left = digits[max(0, pos - 6) : pos]
            right = digits[pos + len(ANCHOR) : pos + len(ANCHOR) + 6]
            window = left + ANCHOR + right
            cls = classify(window)
            books.add(str(row["bookid"]))
            hit_count += 1
            windows[window] += 1
            payload = {"bookid": str(row["bookid"]), "digit_pos": pos, "window": window, "gloss_allowed": False}
            items.append(payload)
            conn.execute(
                """
                INSERT INTO anchor3478_context_items
                    (run_id, bookid, digit_pos, left_digits, anchor, right_digits,
                     window_digits, decodedbase, context_class, next_action, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    str(row["bookid"]),
                    pos,
                    left,
                    ANCHOR,
                    right,
                    window,
                    str(row["decodedbase"] or ""),
                    cls,
                    "audit_digit_boundary_against_row0_no_beholder_gloss",
                    jdump(payload),
                ),
            )
            start = pos + 1
    decision = "ANCHOR3478_DIGIT_CONTEXT_AUDIT_ONLY_NO_GLOSS"
    conn.execute(
        """
        UPDATE anchor3478_context_probe_runs
        SET hit_count=?, book_count=?, unique_window_count=?, decision=?, payload_json=?
        WHERE run_id=?
        """,
        (hit_count, len(books), len(windows), decision, jdump({"top_windows": windows.most_common(20), "items": items, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "hit_count": hit_count, "book_count": len(books), "unique_window_count": len(windows), "top_windows": windows.most_common(10), "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
