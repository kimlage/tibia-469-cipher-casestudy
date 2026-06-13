#!/usr/bin/env python3
"""Split book 30 into local mechanical segments against controls, no gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
CORE = ["T", "A", "E", "S", "E", "S", "T", "I", "E", "N", "V", "N", "S", "B", "L", "F", "S", "I", "N", "N", "A", "I"]
CORE_ALT = ["E", *CORE]
PREFIX = ["T", "B", "B", "T", "I", "B", "E", "I", "E", "I", "V", "N"]
SUFFIX = ["N", "S", "E", "T", "I", "E", "F", "I", "E", "I", "E", "F", "I", "I", "N"]
POSITIVE_CONTROLS = {"12", "21", "26"}
NEGATIVE_CONTROLS = {"32", "58"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS book30_split_frame_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_row0_variant_run_id INTEGER NOT NULL,
            core_positive_count INTEGER NOT NULL,
            core_negative_count INTEGER NOT NULL,
            prefix_negative_count INTEGER NOT NULL,
            suffix_book30_only INTEGER NOT NULL,
            split_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS book30_split_frame_items (
            run_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            bookid TEXT NOT NULL,
            segment_id TEXT NOT NULL,
            positions_json TEXT NOT NULL,
            segment_status TEXT NOT NULL,
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


def find_positions(tokens: list[str], pattern: list[str]) -> list[int]:
    size = len(pattern)
    return [idx for idx in range(0, len(tokens) - size + 1) if tokens[idx : idx + size] == pattern]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db, timeout=30)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    row0_run_id = latest_id(conn, "row0_variant_frontier_runs")
    rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        """,
        (row0_run_id,),
    ).fetchall()
    tokens_by_book = {str(row["bookid"]): json.loads(row["tokens_json"] or "[]") for row in rows}

    cur = conn.execute(
        """
        INSERT INTO book30_split_frame_probe_runs
            (created_at, source_row0_variant_run_id, core_positive_count,
             core_negative_count, prefix_negative_count, suffix_book30_only,
             split_score, decision, payload_json)
        VALUES (?, ?, 0, 0, 0, 0, 0, ?, ?)
        """,
        (utc_now(), row0_run_id, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    items: list[dict[str, Any]] = []
    counts = {
        "core_positive": 0,
        "core_negative": 0,
        "prefix_negative": 0,
        "suffix_anywhere": 0,
    }
    segments = {
        "BOOK30_PREFIX_BTI_EIVN": PREFIX,
        "BOOK30_CORE_TAESESTIEN_VNSBLFSINNAI": CORE,
        "BOOK30_CORE_ALT_ETAESESTIEN_VNSBLFSINNAI": CORE_ALT,
        "BOOK30_SUFFIX_NSETIEFIEIEFIIN": SUFFIX,
    }
    for bookid, tokens in tokens_by_book.items():
        for segment_id, pattern in segments.items():
            positions = find_positions(tokens, pattern)
            if not positions:
                continue
            if segment_id.startswith("BOOK30_CORE"):
                if bookid in POSITIVE_CONTROLS or bookid == "30":
                    counts["core_positive"] += 1
                    status = "CORE_POSITIVE_SUPPORT"
                    next_action = "use_as_book30_core_context"
                elif bookid in NEGATIVE_CONTROLS:
                    counts["core_negative"] += 1
                    status = "CORE_NEGATIVE_HIT"
                    next_action = "do_not_promote_if_negative_expands"
                else:
                    status = "CORE_OUTSIDE_HIT"
                    next_action = "audit_outside_core_hit"
            elif segment_id == "BOOK30_PREFIX_BTI_EIVN":
                if bookid in NEGATIVE_CONTROLS:
                    counts["prefix_negative"] += 1
                status = "PREFIX_CONTEXT_OR_NEGATIVE"
                next_action = "keep_prefix_as_context_not_function"
            else:
                counts["suffix_anywhere"] += 1
                status = "SUFFIX_RESIDUAL_CONTEXT"
                next_action = "keep_suffix_residual_until_more_support"
            payload = {"bookid": bookid, "segment_id": segment_id, "positions": positions, "gloss_allowed": False}
            items.append(payload)
            conn.execute(
                """
                INSERT INTO book30_split_frame_items
                    (run_id, item_key, bookid, segment_id, positions_json,
                     segment_status, next_action, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    f"{bookid}:{segment_id}",
                    bookid,
                    segment_id,
                    jdump(positions),
                    status,
                    next_action,
                    jdump(payload),
                ),
            )

    suffix_book30_only = 1 if counts["suffix_anywhere"] == 1 and any(item["bookid"] == "30" and item["segment_id"] == "BOOK30_SUFFIX_NSETIEFIEIEFIIN" for item in items) else 0
    score = 0.0
    score += min(0.40, counts["core_positive"] * 0.10)
    score += 0.20 if counts["core_negative"] == 0 else -0.20
    score += 0.15 if suffix_book30_only else 0.0
    score += 0.10 if counts["prefix_negative"] == 0 else -0.10
    score += 0.15
    score = round(score, 4)
    decision = "BOOK30_SPLIT_CORE_CONTEXT_READY_NO_GLOSS" if score >= 0.70 and counts["core_positive"] >= 3 and counts["core_negative"] == 0 else "BOOK30_SPLIT_FRAME_AUDIT_ONLY"
    conn.execute(
        """
        UPDATE book30_split_frame_probe_runs
        SET core_positive_count=?,
            core_negative_count=?,
            prefix_negative_count=?,
            suffix_book30_only=?,
            split_score=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            counts["core_positive"],
            counts["core_negative"],
            counts["prefix_negative"],
            suffix_book30_only,
            score,
            decision,
            jdump({"items": items, "gloss_allowed": False}),
            run_id,
        ),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "core_positive_count": counts["core_positive"], "core_negative_count": counts["core_negative"], "prefix_negative_count": counts["prefix_negative"], "suffix_book30_only": suffix_book30_only, "split_score": score, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
