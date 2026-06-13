#!/usr/bin/env python3
"""Probe Hellgate38 as external mechanical contour: endpoints and internal template."""

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
BOOKID = "38"
INTERNAL_ANCHOR = "IVIFASTFNEIEINTA"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS hellgate38_endpoint_template_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_hellgate_run_id INTEGER NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            source_naese_run_id INTEGER,
            bookid TEXT NOT NULL,
            external_anchor_strength TEXT NOT NULL,
            start_token TEXT NOT NULL,
            end_token TEXT NOT NULL,
            same_start_token_book_count INTEGER NOT NULL,
            same_end_token_book_count INTEGER NOT NULL,
            internal_anchor_found INTEGER NOT NULL,
            internal_anchor_context_class TEXT NOT NULL,
            related_internal_book_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hellgate38_endpoint_template_items (
            run_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            item_type TEXT NOT NULL,
            bookid TEXT NOT NULL,
            token_text TEXT NOT NULL,
            start_token TEXT NOT NULL,
            end_token TEXT NOT NULL,
            contains_internal_anchor INTEGER NOT NULL,
            relation_class TEXT NOT NULL,
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    hellgate_run_id = latest_id(conn, "hellgate_external_roundtrip_probe_runs")
    variant_run_id = latest_id(conn, "row0_variant_frontier_runs")
    naese_run_id = latest_optional_id(conn, "naese_ivifast_slot_probe_runs")
    hg = conn.execute(
        """
        SELECT *
        FROM hellgate_external_roundtrip_items
        WHERE run_id=? AND bookid=? AND anchor_strength='STRONG_EXTERNAL_MECHANICAL_ANCHOR'
        LIMIT 1
        """,
        (hellgate_run_id, BOOKID),
    ).fetchone()
    if hg is None:
        raise SystemExit("Hellgate38 strong anchor missing")
    rows = conn.execute(
        """
        SELECT bookid, token_text, symbol_text, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (variant_run_id,),
    ).fetchall()
    book38 = next((row for row in rows if str(row["bookid"]) == BOOKID), None)
    if book38 is None:
        raise SystemExit("book38 row0 variant tokens missing")
    tokens38 = json.loads(book38["tokens_json"] or "[]")
    start_token = tokens38[0]
    end_token = tokens38[-1]
    symbol38 = book38["symbol_text"] or ""
    anchor_pos = symbol38.find(INTERNAL_ANCHOR)
    internal_found = int(anchor_pos >= 0)
    left_context = symbol38[max(0, anchor_pos - 16) : anchor_pos] if anchor_pos >= 0 else ""
    right_context = symbol38[anchor_pos + len(INTERNAL_ANCHOR) : anchor_pos + len(INTERNAL_ANCHOR) + 16] if anchor_pos >= 0 else ""
    if left_context.endswith("ENTEEAEISETE"):
        context_class = "ENTEEAE_RARE_EXTERNAL_CONTOUR"
    elif "NAESE" in left_context:
        context_class = "NAESE_DOMINANT_OR_VARIANT"
    else:
        context_class = "OTHER_INTERNAL_CONTEXT"

    same_start = []
    same_end = []
    related_internal = []
    for row in rows:
        tokens = json.loads(row["tokens_json"] or "[]")
        if not tokens:
            continue
        if tokens[0] == start_token:
            same_start.append(row)
        if tokens[-1] == end_token:
            same_end.append(row)
        if INTERNAL_ANCHOR in (row["symbol_text"] or ""):
            related_internal.append(row)

    decision = (
        "HELLGATE38_EXTERNAL_CONTOUR_SUPPORTS_RARE_IVIFAST_SLOT"
        if internal_found and context_class == "ENTEEAE_RARE_EXTERNAL_CONTOUR"
        else "HELLGATE38_EXTERNAL_CONTOUR_READY"
    )
    cur = conn.execute(
        """
        INSERT INTO hellgate38_endpoint_template_probe_runs
            (created_at, source_hellgate_run_id, source_variant_run_id, source_naese_run_id,
             bookid, external_anchor_strength, start_token, end_token,
             same_start_token_book_count, same_end_token_book_count,
             internal_anchor_found, internal_anchor_context_class,
             related_internal_book_count, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            hellgate_run_id,
            variant_run_id,
            naese_run_id,
            BOOKID,
            hg["anchor_strength"],
            start_token,
            end_token,
            len(same_start),
            len(same_end),
            internal_found,
            context_class,
            len(related_internal),
            decision,
            jdump(
                {
                    "left_context": left_context,
                    "right_context": right_context,
                    "gloss_allowed": False,
                    "same_start_books": [str(row["bookid"]) for row in same_start],
                    "same_end_books": [str(row["bookid"]) for row in same_end],
                }
            ),
        ),
    )
    run_id = int(cur.lastrowid)

    for row in same_start:
        tokens = json.loads(row["tokens_json"] or "[]")
        relation = "hellgate38_self" if str(row["bookid"]) == BOOKID else "same_start_token"
        conn.execute(
            """
            INSERT INTO hellgate38_endpoint_template_items
                (run_id, item_key, item_type, bookid, token_text, start_token,
                 end_token, contains_internal_anchor, relation_class, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"START:{row['bookid']}",
                "same_start_token",
                str(row["bookid"]),
                row["token_text"] or "",
                tokens[0],
                tokens[-1],
                int(INTERNAL_ANCHOR in (row["symbol_text"] or "")),
                relation,
                "compare_endpoint_context_no_gloss",
                "{}",
            ),
        )
    for row in same_end:
        tokens = json.loads(row["tokens_json"] or "[]")
        key = f"END:{row['bookid']}"
        relation = "hellgate38_self" if str(row["bookid"]) == BOOKID else "same_end_token"
        conn.execute(
            """
            INSERT OR REPLACE INTO hellgate38_endpoint_template_items
                (run_id, item_key, item_type, bookid, token_text, start_token,
                 end_token, contains_internal_anchor, relation_class, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                key,
                "same_end_token",
                str(row["bookid"]),
                row["token_text"] or "",
                tokens[0],
                tokens[-1],
                int(INTERNAL_ANCHOR in (row["symbol_text"] or "")),
                relation,
                "compare_endpoint_context_no_gloss",
                "{}",
            ),
        )
    for row in related_internal:
        tokens = json.loads(row["tokens_json"] or "[]")
        conn.execute(
            """
            INSERT OR REPLACE INTO hellgate38_endpoint_template_items
                (run_id, item_key, item_type, bookid, token_text, start_token,
                 end_token, contains_internal_anchor, relation_class, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"INTERNAL:{row['bookid']}",
                "related_internal_anchor",
                str(row["bookid"]),
                row["token_text"] or "",
                tokens[0],
                tokens[-1],
                1,
                "internal_ivifast_anchor",
                "classify_slot_context_no_gloss",
                "{}",
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "bookid": BOOKID,
                "start_token": start_token,
                "end_token": end_token,
                "same_start_token_book_count": len(same_start),
                "same_end_token_book_count": len(same_end),
                "internal_anchor_found": bool(internal_found),
                "internal_anchor_context_class": context_class,
                "related_internal_book_count": len(related_internal),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
