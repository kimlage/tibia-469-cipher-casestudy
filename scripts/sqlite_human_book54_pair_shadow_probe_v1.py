#!/usr/bin/env python3
"""Test Book54's human shadow reading against the Book20/54 pair."""

from __future__ import annotations

import datetime as dt
import difflib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
LEFT = "20"
RIGHT = "54"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_book54_pair_shadow_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            left_bookid TEXT NOT NULL,
            right_bookid TEXT NOT NULL,
            lcs_len INTEGER NOT NULL,
            lcs_ratio_shorter REAL NOT NULL,
            lcs_ratio_longer REAL NOT NULL,
            shared_block TEXT NOT NULL,
            shared_block_left_pos INTEGER NOT NULL,
            shared_block_right_pos INTEGER NOT NULL,
            accepted_human_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_book54_pair_shadow_probe_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            symbol_text TEXT NOT NULL,
            prefix_before_shared TEXT NOT NULL,
            shared_block TEXT NOT NULL,
            suffix_after_shared TEXT NOT NULL,
            classification TEXT NOT NULL,
            shadow_implication TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def best_block(left: str, right: str) -> tuple[int, int, int]:
    matcher = difflib.SequenceMatcher(a=list(left), b=list(right), autojunk=False)
    blocks = [block for block in matcher.get_matching_blocks() if block.size]
    if not blocks:
        return 0, 0, 0
    block = max(blocks, key=lambda item: item.size)
    return int(block.a), int(block.b), int(block.size)


def classify(bookid: str, prefix: str, shared: str, suffix: str) -> tuple[str, str, str]:
    if bookid == LEFT:
        return (
            "LONGER_PAIR_MEMBER_WITH_LEFT_PREFIX",
            "Book 20 supplies the longer left-context wrapper before the shared local-pair block.",
            "Use as the longer control for Book54; do not translate the prefix.",
        )
    return (
        "SHORTER_PAIR_MEMBER_WITH_MINIMAL_PREFIX_AND_EXTRA_TAIL",
        "Book 54 preserves the shared local-pair block with a shorter prefix and its own small tail, so 'ending fragment' is too narrow.",
        "Revise shadow wording to shared-core/truncation alignment rather than preserved ending only.",
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    rows = conn.execute(
        """
        SELECT bookid, symbol_text
        FROM row0_variant_book_tokens
        WHERE run_id=(SELECT max(run_id) FROM row0_variant_book_tokens)
          AND bookid IN (?, ?)
        """,
        (LEFT, RIGHT),
    ).fetchall()
    by_book = {str(row["bookid"]): str(row["symbol_text"]) for row in rows}
    left = by_book[LEFT]
    right = by_book[RIGHT]
    left_pos, right_pos, size = best_block(left, right)
    shared = left[left_pos : left_pos + size]
    shorter = min(len(left), len(right))
    longer = max(len(left), len(right))
    ratio_short = round(size / max(1, shorter), 4)
    ratio_long = round(size / max(1, longer), 4)

    left_parts = (left[:left_pos], shared, left[left_pos + size :])
    right_parts = (right[:right_pos], shared, right[right_pos + size :])
    if size >= 20 and ratio_short >= 0.75 and right_parts[2]:
        decision = "BOOK54_PAIR_SHADOW_SHARED_CORE_WITH_OWN_TAIL_NO_GLOSS"
    elif size >= 20 and ratio_short >= 0.75:
        decision = "BOOK54_PAIR_SHADOW_TRUNCATED_SHARED_BLOCK_NO_GLOSS"
    else:
        decision = "BOOK54_PAIR_SHADOW_WEAK_ALIGNMENT_NEEDS_REVISION"
    payload = {
        "left_symbol_text": left,
        "right_symbol_text": right,
        "left_parts": {"prefix": left_parts[0], "shared": left_parts[1], "suffix": left_parts[2]},
        "right_parts": {"prefix": right_parts[0], "shared": right_parts[1], "suffix": right_parts[2]},
        "principle": "pair alignment supports local relation only, not lexical translation",
    }
    cur = conn.execute(
        """
        INSERT INTO human_book54_pair_shadow_probe_v1_runs
        (created_at, decision, left_bookid, right_bookid, lcs_len,
         lcs_ratio_shorter, lcs_ratio_longer, shared_block,
         shared_block_left_pos, shared_block_right_pos,
         accepted_human_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            LEFT,
            RIGHT,
            size,
            ratio_short,
            ratio_long,
            shared,
            left_pos,
            right_pos,
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for bookid, text, parts in [(LEFT, left, left_parts), (RIGHT, right, right_parts)]:
        classification, implication, next_action = classify(bookid, parts[0], parts[1], parts[2])
        conn.execute(
            """
            INSERT INTO human_book54_pair_shadow_probe_v1_items
            (run_id, bookid, symbol_text, prefix_before_shared, shared_block,
             suffix_after_shared, classification, shadow_implication,
             next_action, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bookid,
                text,
                parts[0],
                parts[1],
                parts[2],
                classification,
                implication,
                next_action,
                json.dumps(
                    {
                        "lcs_len": size,
                        "lcs_ratio_shorter": ratio_short,
                        "lcs_ratio_longer": ratio_long,
                        "shared_block_left_pos": left_pos,
                        "shared_block_right_pos": right_pos,
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
                "lcs_len": size,
                "lcs_ratio_shorter": ratio_short,
                "lcs_ratio_longer": ratio_long,
                "shared_block": shared,
                "accepted_human_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
