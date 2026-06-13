#!/usr/bin/env python3
"""Evaluate C68 FATCT as a local NAESE slot, without global C68/gloss."""

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


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS c68_fatct_slot_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_frame_run_id INTEGER NOT NULL,
            source_contig_overlap_run_id INTEGER NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            canonical_context_count INTEGER NOT NULL,
            edge_supported_count INTEGER NOT NULL,
            slot_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS c68_fatct_slot_items (
            run_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            bookid TEXT NOT NULL,
            start_pos INTEGER NOT NULL,
            left_context TEXT NOT NULL,
            frame_text TEXT NOT NULL,
            right_context TEXT NOT NULL,
            context_class TEXT NOT NULL,
            edge_support TEXT NOT NULL,
            slot_status TEXT NOT NULL,
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


def classify(left: str, right: str) -> str:
    if left == "E S E S T I E N" and right == "I V V T I S E T":
        return "CANONICAL_NAESE_FATCT_SLOT"
    if left == "E S E S T I E N":
        return "PREFIX_CANONICAL_SUFFIX_VARIANT"
    if right == "I V V T I S E T":
        return "SUFFIX_CANONICAL_PREFIX_VARIANT"
    return "LOCAL_VARIANT_OR_AUDIT"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    variant_run_id = latest_id(conn, "variant_frame_probe_runs")
    contig_run_id = latest_id(conn, "contig_max_overlap_probe_runs")
    rows = conn.execute(
        """
        SELECT *
        FROM variant_frame_occurrence_items
        WHERE run_id=? AND frame_key='C68_FATCT_SLOT'
        ORDER BY CAST(bookid AS INTEGER), start_pos
        """,
        (variant_run_id,),
    ).fetchall()
    edges = conn.execute(
        """
        SELECT basecontigid, edge_index, left_bookid, right_bookid, overlap_text
        FROM contig_max_overlap_edges
        WHERE run_id=?
        """,
        (contig_run_id,),
    ).fetchall()

    edge_books: set[str] = set()
    edge_refs_by_book: dict[str, list[str]] = {}
    for edge in edges:
        if "NAESESTIENFATCTIVVT" not in str(edge["overlap_text"]):
            continue
        ref = f'{edge["basecontigid"]}:{edge["edge_index"]}:{edge["left_bookid"]}->{edge["right_bookid"]}'
        for bookid in (str(edge["left_bookid"]), str(edge["right_bookid"])):
            edge_books.add(bookid)
            edge_refs_by_book.setdefault(bookid, []).append(ref)

    cur = conn.execute(
        """
        INSERT INTO c68_fatct_slot_probe_runs
            (created_at, source_variant_frame_run_id, source_contig_overlap_run_id,
             occurrence_count, book_count, canonical_context_count,
             edge_supported_count, slot_score, decision, payload_json)
        VALUES (?, ?, ?, 0, 0, 0, 0, 0, ?, ?)
        """,
        (utc_now(), variant_run_id, contig_run_id, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    class_counts: Counter[str] = Counter()
    books: set[str] = set()
    canonical = 0
    edge_supported = 0
    summaries: list[dict[str, Any]] = []
    for row in rows:
        bookid = str(row["bookid"])
        context_class = classify(row["left_context"], row["right_context"])
        has_edge = bookid in edge_books
        if context_class == "CANONICAL_NAESE_FATCT_SLOT":
            canonical += 1
        if has_edge:
            edge_supported += 1
        class_counts[context_class] += 1
        books.add(bookid)
        if context_class == "CANONICAL_NAESE_FATCT_SLOT":
            status = "SLOT_SUBFUNCTION_READY" if has_edge else "CANONICAL_SLOT_SURFACE_SUPPORT"
            next_action = "materialize_as_naese_slot_subfunction_no_gloss"
        else:
            status = "SLOT_VARIANT_AUDIT"
            next_action = "keep_as_variant_or_negative_control"
        payload = {
            "bookid": bookid,
            "context_class": context_class,
            "edge_refs": edge_refs_by_book.get(bookid, []),
            "gloss_allowed": False,
        }
        summaries.append(payload)
        conn.execute(
            """
            INSERT INTO c68_fatct_slot_items
                (run_id, item_key, bookid, start_pos, left_context, frame_text,
                 right_context, context_class, edge_support, slot_status,
                 next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f'{bookid}:{row["start_pos"]}',
                bookid,
                int(row["start_pos"]),
                row["left_context"],
                row["frame_text"],
                row["right_context"],
                context_class,
                "EDGE_SUPPORTED" if has_edge else "NO_EDGE_SUPPORT",
                status,
                next_action,
                jdump(payload),
            ),
        )

    slot_score = round(min(0.35, canonical * 0.035) + min(0.25, len(books) * 0.025) + min(0.25, edge_supported * 0.125) + 0.15, 4)
    decision = "C68_FATCT_NAESE_SLOT_SUBFUNCTION_READY_NO_GLOSS" if slot_score >= 0.75 and canonical >= 8 and edge_supported >= 2 else "C68_FATCT_SLOT_CONTEXT_ONLY"
    payload = {
        "class_counts": class_counts.most_common(),
        "edge_books": sorted(edge_books, key=lambda value: int(value) if value.isdigit() else value),
        "items": summaries,
        "gloss_allowed": False,
    }
    conn.execute(
        """
        UPDATE c68_fatct_slot_probe_runs
        SET occurrence_count=?,
            book_count=?,
            canonical_context_count=?,
            edge_supported_count=?,
            slot_score=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (len(rows), len(books), canonical, edge_supported, slot_score, decision, jdump(payload), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "occurrence_count": len(rows), "book_count": len(books), "canonical_context_count": canonical, "edge_supported_count": edge_supported, "slot_score": slot_score, "class_counts": class_counts.most_common(), "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
