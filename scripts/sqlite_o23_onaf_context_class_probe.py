#!/usr/bin/env python3
"""Classify O23_ONAF contexts after promotion: endpoint, suffix branch, independent."""

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
FRAME = ["O23", "N", "A", "F", "I", "E", "I"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS o23_onaf_context_class_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            source_o23_run_id INTEGER NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            context_class_count_json TEXT NOT NULL,
            right_payload_class_count_json TEXT NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS o23_onaf_context_class_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            occurrence_index INTEGER NOT NULL,
            start_pos INTEGER NOT NULL,
            context_class TEXT NOT NULL,
            right_payload_class TEXT NOT NULL,
            left_context TEXT NOT NULL,
            frame_text TEXT NOT NULL,
            right_context TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid, occurrence_index)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def find_frame(tokens: list[str], frame: list[str]) -> list[int]:
    starts = []
    size = len(frame)
    for idx in range(0, len(tokens) - size + 1):
        if tokens[idx : idx + size] == frame:
            starts.append(idx)
    return starts


def classify_context(bookid: str, start: int, left: list[str]) -> str:
    if start == 0 and bookid == "38":
        return "EXTERNAL_HELLGATE_BOOK_START"
    if left[-5:] == ["T", "I", "F", "A", "V"]:
        return "VINVIN_VTLR_TIFAV_SUFFIX_BRANCH"
    if start == 0:
        return "BOOK_START_ONAF"
    return "INTERNAL_ONAF_CONTINUATION"


def classify_right(right: list[str]) -> str:
    if right[:6] == ["V", "E", "I", "N", "L", "E"]:
        return "VEINLETFNAAST_PAYLOAD"
    if right[:4] == ["E", "I", "V", "E"]:
        return "EIVE_PAYLOAD"
    if right[:3] == ["E", "I", "E"]:
        return "EIE_PAYLOAD"
    if right[:1] == ["E"]:
        return "E_PAYLOAD_OTHER"
    if not right:
        return "END_AFTER_ONAF"
    return "OTHER_PAYLOAD"


def next_action(context_class: str, right_payload_class: str) -> str:
    if context_class == "EXTERNAL_HELLGATE_BOOK_START":
        return "use_as_external_endpoint_holdout_no_gloss"
    if context_class == "VINVIN_VTLR_TIFAV_SUFFIX_BRANCH":
        return "use_as_vinvin_suffix_branch_payload_no_gloss"
    return "use_as_independent_onaf_context_control"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    variant_run_id = latest_id(conn, "row0_variant_frontier_runs")
    o23_run_id = latest_id(conn, "o23_onaf_hellgate_holdout_probe_runs")
    rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (variant_run_id,),
    ).fetchall()

    items = []
    context_counts: Counter[str] = Counter()
    right_counts: Counter[str] = Counter()
    books = set()
    for row in rows:
        bookid = str(row["bookid"])
        tokens = json.loads(row["tokens_json"] or "[]")
        for occurrence_index, start in enumerate(find_frame(tokens, FRAME), start=1):
            end = start + len(FRAME)
            left = tokens[max(0, start - 12) : start]
            right = tokens[end : min(len(tokens), end + 16)]
            context_class = classify_context(bookid, start, left)
            right_payload_class = classify_right(right)
            context_counts[context_class] += 1
            right_counts[right_payload_class] += 1
            books.add(bookid)
            items.append(
                {
                    "bookid": bookid,
                    "occurrence_index": occurrence_index,
                    "start_pos": start + 1,
                    "context_class": context_class,
                    "right_payload_class": right_payload_class,
                    "left_context": " ".join(left),
                    "right_context": " ".join(right),
                    "next_action": next_action(context_class, right_payload_class),
                }
            )

    if context_counts["VINVIN_VTLR_TIFAV_SUFFIX_BRANCH"] >= 2 and context_counts["EXTERNAL_HELLGATE_BOOK_START"] == 1:
        decision = "O23_ONAF_CONTEXTS_SEPARATED_FOR_BRANCH_ANALYSIS"
    elif items:
        decision = "O23_ONAF_CONTEXTS_AUDIT_ONLY"
    else:
        decision = "O23_ONAF_CONTEXT_NOT_FOUND"
    cur = conn.execute(
        """
        INSERT INTO o23_onaf_context_class_probe_runs
            (created_at, source_variant_run_id, source_o23_run_id,
             occurrence_count, book_count, context_class_count_json,
             right_payload_class_count_json, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            variant_run_id,
            o23_run_id,
            len(items),
            len(books),
            jdump(context_counts.most_common()),
            jdump(right_counts.most_common()),
            decision,
            jdump({"gloss_allowed": False}),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in items:
        conn.execute(
            """
            INSERT INTO o23_onaf_context_class_items
                (run_id, bookid, occurrence_index, start_pos, context_class,
                 right_payload_class, left_context, frame_text, right_context,
                 next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["occurrence_index"],
                item["start_pos"],
                item["context_class"],
                item["right_payload_class"],
                item["left_context"],
                " ".join(FRAME),
                item["right_context"],
                item["next_action"],
                "{}",
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "occurrence_count": len(items),
                "book_count": len(books),
                "context_classes": context_counts.most_common(),
                "right_payload_classes": right_counts.most_common(),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
