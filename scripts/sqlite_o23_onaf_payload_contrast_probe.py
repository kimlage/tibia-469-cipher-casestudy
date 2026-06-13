#!/usr/bin/env python3
"""Contrast payloads after O23_ONAF, focusing VEINLETFNAAST."""

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
PAYLOAD = ["V", "E", "I", "N", "L", "E", "T", "F", "N", "A", "A", "S", "T"]
HELLGATE_BOOK = "38"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS o23_onaf_payload_contrast_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            source_o23_context_run_id INTEGER NOT NULL,
            source_hellgate38_run_id INTEGER,
            source_overlap_holdout_run_id INTEGER,
            payload_occurrence_count INTEGER NOT NULL,
            payload_book_count INTEGER NOT NULL,
            hellgate_payload_supported INTEGER NOT NULL,
            contig_13_38_payload_supported INTEGER NOT NULL,
            payload_without_o23_count INTEGER NOT NULL,
            o23_without_payload_count INTEGER NOT NULL,
            context_class_count_json TEXT NOT NULL,
            payload_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS o23_onaf_payload_contrast_items (
            run_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            item_type TEXT NOT NULL,
            bookid TEXT NOT NULL,
            start_pos INTEGER NOT NULL,
            context_class TEXT NOT NULL,
            frame_text TEXT NOT NULL,
            payload_text TEXT NOT NULL,
            right_context TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_key)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def latest_optional_id(conn: sqlite3.Connection, table: str) -> int | None:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def find_frame(tokens: list[str], frame: list[str]) -> list[int]:
    starts = []
    size = len(frame)
    for idx in range(0, len(tokens) - size + 1):
        if tokens[idx : idx + size] == frame:
            starts.append(idx)
    return starts


def classify_context(bookid: str, start: int, left: list[str]) -> str:
    if start == 0 and bookid == HELLGATE_BOOK:
        return "EXTERNAL_HELLGATE_BOOK_START"
    if left[-5:] == ["T", "I", "F", "A", "V"]:
        return "VINVIN_VTLR_TIFAV_SUFFIX_BRANCH"
    if start == 0:
        return "BOOK_START_ONAF"
    return "INTERNAL_ONAF_CONTINUATION"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    variant_run_id = latest_id(conn, "row0_variant_frontier_runs")
    o23_context_run_id = latest_id(conn, "o23_onaf_context_class_probe_runs")
    hellgate_run_id = latest_optional_id(conn, "hellgate38_endpoint_template_probe_runs")
    overlap_run_id = latest_optional_id(conn, "overlap_formula_holdout_probe_runs")
    rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (variant_run_id,),
    ).fetchall()

    occurrences = []
    payload_without_o23 = []
    o23_without_payload = []
    books = set()
    context_counts: Counter[str] = Counter()
    for row in rows:
        bookid = str(row["bookid"])
        tokens = json.loads(row["tokens_json"] or "[]")
        frame_starts = find_frame(tokens, FRAME)
        payload_starts = find_frame(tokens, PAYLOAD)
        for start in frame_starts:
            payload_start = start + len(FRAME)
            has_payload = tokens[payload_start : payload_start + len(PAYLOAD)] == PAYLOAD
            left = tokens[max(0, start - 12) : start]
            context_class = classify_context(bookid, start, left)
            if has_payload:
                right_start = payload_start + len(PAYLOAD)
                right = tokens[right_start : min(len(tokens), right_start + 12)]
                occurrences.append(
                    {
                        "bookid": bookid,
                        "start_pos": start + 1,
                        "context_class": context_class,
                        "right_context": " ".join(right),
                    }
                )
                books.add(bookid)
                context_counts[context_class] += 1
            else:
                o23_without_payload.append((bookid, start, context_class, tokens))
        frame_payload_positions = {start + len(FRAME) for start in frame_starts}
        for start in payload_starts:
            if start not in frame_payload_positions:
                payload_without_o23.append((bookid, start, tokens))

    hellgate_supported = int(any(item["bookid"] == HELLGATE_BOOK for item in occurrences))
    contig_supported = 0
    if overlap_run_id is not None:
        edge = conn.execute(
            """
            SELECT *
            FROM overlap_formula_holdout_edge_items
            WHERE run_id=?
              AND basecontigid='4'
              AND edge_index=1
              AND classification IN ('ALIVE_WEAK', 'ALIVE_STRONG')
            """,
            (overlap_run_id,),
        ).fetchone()
        contig_supported = int(edge is not None and any(item["bookid"] in {"13", "38"} for item in occurrences))

    payload_score = 0.0
    payload_score += min(0.25, len(books) * 0.05)
    payload_score += 0.25 if hellgate_supported else 0.0
    payload_score += 0.20 if contig_supported else 0.0
    payload_score += max(0.0, 0.15 - len(payload_without_o23) * 0.03)
    payload_score += max(0.0, 0.15 - len(o23_without_payload) * 0.02)
    if payload_score >= 0.75 and len(books) >= 3:
        decision = "O23_ONAF_VEINLETFNAAST_PAYLOAD_READY"
    elif payload_score >= 0.55:
        decision = "O23_ONAF_VEINLETFNAAST_PAYLOAD_CONTEXT"
    else:
        decision = "O23_ONAF_VEINLETFNAAST_PAYLOAD_AUDIT_ONLY"

    cur = conn.execute(
        """
        INSERT INTO o23_onaf_payload_contrast_probe_runs
            (created_at, source_variant_run_id, source_o23_context_run_id,
             source_hellgate38_run_id, source_overlap_holdout_run_id,
             payload_occurrence_count, payload_book_count,
             hellgate_payload_supported, contig_13_38_payload_supported,
             payload_without_o23_count, o23_without_payload_count,
             context_class_count_json, payload_score, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            variant_run_id,
            o23_context_run_id,
            hellgate_run_id,
            overlap_run_id,
            len(occurrences),
            len(books),
            hellgate_supported,
            contig_supported,
            len(payload_without_o23),
            len(o23_without_payload),
            jdump(context_counts.most_common()),
            payload_score,
            decision,
            jdump({"gloss_allowed": False, "payload": PAYLOAD}),
        ),
    )
    run_id = int(cur.lastrowid)
    for idx, item in enumerate(occurrences, start=1):
        conn.execute(
            """
            INSERT INTO o23_onaf_payload_contrast_items
                (run_id, item_key, item_type, bookid, start_pos, context_class,
                 frame_text, payload_text, right_context, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"OCC:{idx}:{item['bookid']}:{item['start_pos']}",
                "payload_after_o23_onaf",
                item["bookid"],
                item["start_pos"],
                item["context_class"],
                " ".join(FRAME),
                " ".join(PAYLOAD),
                item["right_context"],
                "test_payload_branch_no_gloss",
                "{}",
            ),
        )
    for idx, (bookid, start, tokens) in enumerate(payload_without_o23[:20], start=1):
        conn.execute(
            """
            INSERT INTO o23_onaf_payload_contrast_items
                (run_id, item_key, item_type, bookid, start_pos, context_class,
                 frame_text, payload_text, right_context, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"NEG_PAYLOAD:{idx}:{bookid}:{start + 1}",
                "payload_without_o23_onaf",
                bookid,
                start + 1,
                "negative_payload_without_frame",
                "",
                " ".join(PAYLOAD),
                " ".join(tokens[start + len(PAYLOAD) : min(len(tokens), start + len(PAYLOAD) + 12)]),
                "do_not_promote_payload_alone",
                "{}",
            ),
        )
    for idx, (bookid, start, context_class, tokens) in enumerate(o23_without_payload[:20], start=1):
        conn.execute(
            """
            INSERT INTO o23_onaf_payload_contrast_items
                (run_id, item_key, item_type, bookid, start_pos, context_class,
                 frame_text, payload_text, right_context, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"NEG_O23:{idx}:{bookid}:{start + 1}",
                "o23_onaf_without_payload",
                bookid,
                start + 1,
                context_class,
                " ".join(FRAME),
                "",
                " ".join(tokens[start + len(FRAME) : min(len(tokens), start + len(FRAME) + 12)]),
                "keep_o23_context_separate",
                "{}",
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "payload_occurrence_count": len(occurrences),
                "payload_book_count": len(books),
                "hellgate_payload_supported": bool(hellgate_supported),
                "contig_13_38_payload_supported": bool(contig_supported),
                "payload_without_o23_count": len(payload_without_o23),
                "o23_without_payload_count": len(o23_without_payload),
                "context_classes": context_counts.most_common(),
                "payload_score": round(payload_score, 4),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
