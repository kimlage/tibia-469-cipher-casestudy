#!/usr/bin/env python3
"""Test Book12/21 shadow readings as shared spine/base plus Book21 tail."""

from __future__ import annotations

import datetime as dt
import difflib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
LEFT = "12"
RIGHT = "21"
ENDPOINT_CONTROLS = ["13", "38"]
O23_MARKERS = ["ONAF", "FNAAST", "VEINLETFNAAST"]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_book12_21_tail_shadow_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            left_bookid TEXT NOT NULL,
            right_bookid TEXT NOT NULL,
            shared_block TEXT NOT NULL,
            shared_block_len INTEGER NOT NULL,
            shared_ratio_left REAL NOT NULL,
            shared_ratio_right REAL NOT NULL,
            direct_o23_marker_count INTEGER NOT NULL,
            accepted_human_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_book12_21_tail_shadow_probe_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            symbol_text TEXT NOT NULL,
            prefix_before_shared TEXT NOT NULL,
            shared_block TEXT NOT NULL,
            suffix_after_shared TEXT NOT NULL,
            o23_markers_json TEXT NOT NULL,
            classification TEXT NOT NULL,
            shadow_implication TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def best_block(a: str, b: str) -> tuple[int, int, int]:
    matcher = difflib.SequenceMatcher(a=list(a), b=list(b), autojunk=False)
    blocks = [block for block in matcher.get_matching_blocks() if block.size]
    if not blocks:
        return 0, 0, 0
    block = max(blocks, key=lambda item: item.size)
    return int(block.a), int(block.b), int(block.size)


def markers(text: str) -> list[str]:
    return [marker for marker in O23_MARKERS if marker in text]


def classify(bookid: str, suffix: str, hit_markers: list[str]) -> tuple[str, str, str]:
    if bookid == LEFT:
        return (
            "SHARED_BASE_TERMINAL_WITNESS_NO_DIRECT_O23",
            "Book 12 is a compact shared-base witness; endpoint wording must remain terminal/structural, not O23 lexical.",
            "Use Book 12 as the short positive base; test whether its terminal marker recurs outside O23 contexts.",
        )
    if bookid == RIGHT:
        return (
            "SHARED_BASE_WITH_EXTRA_TAIL_EXTENSION",
            "Book 21 preserves the Book12 shared base and adds TIVNSENI*LAELBEV as an extension.",
            "Test the Book21 tail against R02/bridge families before drafting stronger prose.",
        )
    if hit_markers:
        return (
            "O23_ENDPOINT_CONTROL",
            "Endpoint control with direct O23/ONAF/FNAAST markers; not the same evidence class as Books 12/21.",
            "Keep as endpoint control; do not import O23 meaning into Books 12/21.",
        )
    return (
        "NON_O23_CONTROL",
        "No direct O23 marker; background control.",
        "Keep as context only.",
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    books = [LEFT, RIGHT, *ENDPOINT_CONTROLS]
    placeholders = ",".join("?" for _ in books)
    rows = conn.execute(
        f"""
        SELECT bookid, symbol_text
        FROM row0_variant_book_tokens
        WHERE run_id=(SELECT max(run_id) FROM row0_variant_book_tokens)
          AND bookid IN ({placeholders})
        """,
        tuple(books),
    ).fetchall()
    by_book = {str(row["bookid"]): str(row["symbol_text"]) for row in rows}
    left = by_book[LEFT]
    right = by_book[RIGHT]
    left_pos, right_pos, size = best_block(left, right)
    shared = left[left_pos : left_pos + size]
    left_parts = (left[:left_pos], shared, left[left_pos + size :])
    right_parts = (right[:right_pos], shared, right[right_pos + size :])
    direct_markers = {bookid: markers(text) for bookid, text in by_book.items()}
    direct_o23_in_targets = len(direct_markers[LEFT]) + len(direct_markers[RIGHT])
    ratio_left = round(size / max(1, len(left)), 4)
    ratio_right = round(size / max(1, len(right)), 4)

    if size >= 50 and right_parts[2] and direct_o23_in_targets == 0:
        decision = "BOOK12_21_TAIL_SHADOW_SHARED_BASE_PLUS_EXTENSION_NO_O23_GLOSS"
    elif size >= 50:
        decision = "BOOK12_21_TAIL_SHADOW_SHARED_BASE_WITH_O23_RISK"
    else:
        decision = "BOOK12_21_TAIL_SHADOW_WEAK_SHARED_BASE_NEEDS_REVISION"
    payload = {
        "left_parts": {"prefix": left_parts[0], "shared": left_parts[1], "suffix": left_parts[2]},
        "right_parts": {"prefix": right_parts[0], "shared": right_parts[1], "suffix": right_parts[2]},
        "endpoint_controls": {bookid: {"symbol_text": by_book[bookid], "markers": direct_markers[bookid]} for bookid in ENDPOINT_CONTROLS},
        "principle": "terminal/tail support only; direct O23 endpoint markers must not be imported into Book12/21",
    }
    cur = conn.execute(
        """
        INSERT INTO human_book12_21_tail_shadow_probe_v1_runs
        (created_at, decision, left_bookid, right_bookid, shared_block,
         shared_block_len, shared_ratio_left, shared_ratio_right,
         direct_o23_marker_count, accepted_human_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            LEFT,
            RIGHT,
            shared,
            size,
            ratio_left,
            ratio_right,
            direct_o23_in_targets,
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)

    for bookid in books:
        text = by_book[bookid]
        if bookid == LEFT:
            parts = left_parts
        elif bookid == RIGHT:
            parts = right_parts
        else:
            parts = ("", "", "")
        hit_markers = direct_markers[bookid]
        classification, implication, next_action = classify(bookid, parts[2], hit_markers)
        conn.execute(
            """
            INSERT INTO human_book12_21_tail_shadow_probe_v1_items
            (run_id, bookid, symbol_text, prefix_before_shared, shared_block,
             suffix_after_shared, o23_markers_json, classification,
             shadow_implication, next_action, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bookid,
                text,
                parts[0],
                parts[1],
                parts[2],
                json.dumps(hit_markers, ensure_ascii=False, sort_keys=True),
                classification,
                implication,
                next_action,
                json.dumps(
                    {
                        "shared_block_len": size,
                        "shared_ratio_left": ratio_left,
                        "shared_ratio_right": ratio_right,
                        "direct_o23_marker_count_in_targets": direct_o23_in_targets,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "shared_block_len": size,
                "shared_ratio_left": ratio_left,
                "shared_ratio_right": ratio_right,
                "direct_o23_marker_count": direct_o23_in_targets,
                "accepted_human_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
