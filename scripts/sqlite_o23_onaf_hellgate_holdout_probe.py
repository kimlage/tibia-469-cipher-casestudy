#!/usr/bin/env python3
"""Test O23_ONAF as a Hellgate/contig endpoint holdout, without gloss."""

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
PRIMARY_BOOK = "38"
PRIMARY_FRAME = ["O23", "N", "A", "F", "I", "E", "I"]
SHORT_FRAME = ["O23", "N", "A", "F"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS o23_onaf_hellgate_holdout_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_hellgate38_run_id INTEGER NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            source_overlap_holdout_run_id INTEGER NOT NULL,
            frame_occurrence_count INTEGER NOT NULL,
            frame_book_count INTEGER NOT NULL,
            primary_book_supported INTEGER NOT NULL,
            primary_edge_alive INTEGER NOT NULL,
            independent_support_count INTEGER NOT NULL,
            negative_o23_count INTEGER NOT NULL,
            negative_nafie_count INTEGER NOT NULL,
            specificity_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS o23_onaf_hellgate_holdout_items (
            run_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            item_type TEXT NOT NULL,
            bookid TEXT,
            start_pos INTEGER,
            relation_class TEXT NOT NULL,
            left_context TEXT NOT NULL,
            frame_text TEXT NOT NULL,
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


def find_frame(tokens: list[str], frame: list[str]) -> list[int]:
    starts = []
    size = len(frame)
    for idx in range(0, len(tokens) - size + 1):
        if tokens[idx : idx + size] == frame:
            starts.append(idx)
    return starts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    hellgate_run_id = latest_id(conn, "hellgate38_endpoint_template_probe_runs")
    variant_run_id = latest_id(conn, "row0_variant_frontier_runs")
    overlap_run_id = latest_id(conn, "overlap_formula_holdout_probe_runs")
    rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (variant_run_id,),
    ).fetchall()
    alive_edge = conn.execute(
        """
        SELECT *
        FROM overlap_formula_holdout_edge_items
        WHERE run_id=?
          AND basecontigid='4'
          AND edge_index=1
          AND classification IN ('ALIVE_STRONG', 'ALIVE_WEAK')
        """,
        (overlap_run_id,),
    ).fetchone()
    primary_edge_alive = int(alive_edge is not None)

    occurrences = []
    negative_o23 = []
    negative_nafie = []
    books = set()
    right_contexts: Counter[str] = Counter()
    for row in rows:
        bookid = str(row["bookid"])
        tokens = json.loads(row["tokens_json"] or "[]")
        full_starts = find_frame(tokens, PRIMARY_FRAME)
        short_starts = find_frame(tokens, SHORT_FRAME)
        for start in full_starts:
            end = start + len(PRIMARY_FRAME)
            left = " ".join(tokens[max(0, start - 8) : start])
            right = " ".join(tokens[end : min(len(tokens), end + 12)])
            relation = "primary_hellgate_holdout" if bookid == PRIMARY_BOOK else "independent_o23_onaf_support"
            occurrences.append(
                {
                    "bookid": bookid,
                    "start_pos": start + 1,
                    "relation_class": relation,
                    "left": left,
                    "frame": " ".join(PRIMARY_FRAME),
                    "right": right,
                }
            )
            books.add(bookid)
            right_contexts[right[:24]] += 1
        for idx, token in enumerate(tokens):
            if token == "O23" and idx not in short_starts and idx not in full_starts:
                negative_o23.append((bookid, idx, tokens))
        for start in range(0, len(tokens) - 4):
            if tokens[start : start + 4] == ["N", "A", "F", "I"] and (start == 0 or tokens[start - 1] != "O23"):
                negative_nafie.append((bookid, start, tokens))

    primary_supported = int(any(item["bookid"] == PRIMARY_BOOK for item in occurrences))
    independent_support = len({item["bookid"] for item in occurrences if item["bookid"] != PRIMARY_BOOK})
    negative_o23_count = len(negative_o23)
    negative_nafie_count = len(negative_nafie)
    specificity_score = 0.0
    specificity_score += 0.30 if primary_supported else 0.0
    specificity_score += 0.25 if primary_edge_alive else 0.0
    specificity_score += min(0.25, independent_support * 0.04)
    specificity_score += 0.10 if negative_o23_count == 0 else max(0.0, 0.10 - negative_o23_count * 0.02)
    specificity_score += 0.10 if negative_nafie_count <= 2 else max(0.0, 0.10 - negative_nafie_count * 0.01)

    if specificity_score >= 0.75 and independent_support >= 3:
        decision = "O23_ONAF_ENDPOINT_FRAME_ALIVE"
    elif primary_supported and primary_edge_alive:
        decision = "O23_ONAF_HELLGATE_HOLDOUT_ONLY"
    else:
        decision = "O23_ONAF_AUDIT_ONLY"

    cur = conn.execute(
        """
        INSERT INTO o23_onaf_hellgate_holdout_probe_runs
            (created_at, source_hellgate38_run_id, source_variant_run_id,
             source_overlap_holdout_run_id, frame_occurrence_count, frame_book_count,
             primary_book_supported, primary_edge_alive, independent_support_count,
             negative_o23_count, negative_nafie_count, specificity_score,
             decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            hellgate_run_id,
            variant_run_id,
            overlap_run_id,
            len(occurrences),
            len(books),
            primary_supported,
            primary_edge_alive,
            independent_support,
            negative_o23_count,
            negative_nafie_count,
            specificity_score,
            decision,
            jdump({"right_contexts": right_contexts.most_common(), "gloss_allowed": False}),
        ),
    )
    run_id = int(cur.lastrowid)

    for idx, item in enumerate(occurrences, start=1):
        conn.execute(
            """
            INSERT INTO o23_onaf_hellgate_holdout_items
                (run_id, item_key, item_type, bookid, start_pos, relation_class,
                 left_context, frame_text, right_context, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"OCC:{idx}:{item['bookid']}:{item['start_pos']}",
                "o23_onaf_occurrence",
                item["bookid"],
                item["start_pos"],
                item["relation_class"],
                item["left"],
                item["frame"],
                item["right"],
                "compare_boundary_continuation_no_gloss",
                "{}",
            ),
        )
    for idx, (bookid, start, tokens) in enumerate(negative_o23[:20], start=1):
        conn.execute(
            """
            INSERT INTO o23_onaf_hellgate_holdout_items
                (run_id, item_key, item_type, bookid, start_pos, relation_class,
                 left_context, frame_text, right_context, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"NEG_O23:{idx}:{bookid}:{start + 1}",
                "negative_o23_without_onaf",
                bookid,
                start + 1,
                "negative_o23_without_onaf",
                " ".join(tokens[max(0, start - 8) : start]),
                tokens[start],
                " ".join(tokens[start + 1 : min(len(tokens), start + 12)]),
                "do_not_generalize_o23",
                "{}",
            ),
        )
    for idx, (bookid, start, tokens) in enumerate(negative_nafie[:20], start=1):
        conn.execute(
            """
            INSERT INTO o23_onaf_hellgate_holdout_items
                (run_id, item_key, item_type, bookid, start_pos, relation_class,
                 left_context, frame_text, right_context, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"NEG_NAFI:{idx}:{bookid}:{start + 1}",
                "negative_nafie_without_o23",
                bookid,
                start + 1,
                "negative_nafie_without_o23",
                " ".join(tokens[max(0, start - 8) : start]),
                " ".join(tokens[start : start + 4]),
                " ".join(tokens[start + 4 : min(len(tokens), start + 16)]),
                "test_continuation_without_o23",
                "{}",
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "frame_occurrence_count": len(occurrences),
                "frame_book_count": len(books),
                "primary_book_supported": bool(primary_supported),
                "primary_edge_alive": bool(primary_edge_alive),
                "independent_support_count": independent_support,
                "negative_o23_count": negative_o23_count,
                "negative_nafie_count": negative_nafie_count,
                "specificity_score": round(specificity_score, 4),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
