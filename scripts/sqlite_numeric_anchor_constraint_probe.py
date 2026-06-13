#!/usr/bin/env python3
"""Audit external numeric/lore anchors against canonical digit streams, no gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
ANCHORS = {
    "486486": "wrinkled_bonelord_name",
    "3478": "weak_beholder_hypothesis",
    "1": "tibia_lore_one",
    "0": "obscene_lore_zero",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS numeric_anchor_constraint_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_books_export_id INTEGER NOT NULL,
            source_row0_run_id INTEGER NOT NULL,
            anchor_count INTEGER NOT NULL,
            direct_hit_anchor_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS numeric_anchor_constraint_items (
            run_id INTEGER NOT NULL,
            anchor TEXT NOT NULL,
            anchor_role TEXT NOT NULL,
            direct_digit_hit_count INTEGER NOT NULL,
            direct_digit_book_count INTEGER NOT NULL,
            reconstructed_code_hit_count INTEGER NOT NULL,
            reconstructed_code_book_count INTEGER NOT NULL,
            evidence_tier TEXT NOT NULL,
            constraint_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, anchor)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str, col: str = "run_id") -> int:
    row = conn.execute(f"SELECT {col} FROM {table} ORDER BY {col} DESC LIMIT 1").fetchone()
    return int(row[col]) if row else 0


def find_positions(text: str, needle: str) -> list[int]:
    out: list[int] = []
    start = 0
    while True:
        idx = text.find(needle, start)
        if idx < 0:
            break
        out.append(idx)
        start = idx + 1
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db, timeout=30)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    export_id = latest_id(conn, "sheet__books", "__export_id")
    row0_run = latest_id(conn, "row0_code_symbol_probe_runs")
    books = conn.execute(
        """
        SELECT bookid, digits
        FROM sheet__books
        WHERE __export_id=? AND digits IS NOT NULL
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (export_id,),
    ).fetchall()
    row0 = conn.execute(
        """
        SELECT bookid, reconstructed_code_stream
        FROM row0_code_symbol_probe_books
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (row0_run,),
    ).fetchall()

    cur = conn.execute(
        """
        INSERT INTO numeric_anchor_constraint_probe_runs
            (created_at, source_books_export_id, source_row0_run_id,
             anchor_count, direct_hit_anchor_count, decision, payload_json)
        VALUES (?, ?, ?, ?, 0, ?, ?)
        """,
        (utc_now(), export_id, row0_run, len(ANCHORS), "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    direct_hit_anchors = 0
    summaries: list[dict[str, Any]] = []
    for anchor, role in ANCHORS.items():
        direct_hits = []
        code_hits = []
        for row in books:
            positions = find_positions(str(row["digits"] or ""), anchor)
            if positions:
                direct_hits.append({"bookid": str(row["bookid"]), "positions": positions})
        for row in row0:
            positions = find_positions(str(row["reconstructed_code_stream"] or ""), anchor)
            if positions:
                code_hits.append({"bookid": str(row["bookid"]), "positions": positions})
        if direct_hits:
            direct_hit_anchors += 1
        if anchor in {"486486", "3478"}:
            status = "AUDIT_ANCHOR_DIRECT_HITS" if direct_hits or code_hits else "AUDIT_ANCHOR_NOT_IN_BOOK_DIGITS"
            next_action = "compare_hits_to_row0_context_only_no_gloss"
            tier = "EXTERNAL_AUDIT_ANCHOR" if anchor == "486486" else "WEAK_EXTERNAL_HYPOTHESIS"
        else:
            status = "LORE_NUMERIC_CONSTRAINT_BACKGROUND"
            next_action = "use_as_lore_guard_not_direct_anchor"
            tier = "EXTERNAL_CONTEXT"
        evidence = {
            "anchor": anchor,
            "role": role,
            "direct_hits": direct_hits,
            "reconstructed_code_hits": code_hits,
            "gloss_allowed": False,
        }
        summaries.append({"anchor": anchor, "status": status, "direct_books": len({h["bookid"] for h in direct_hits}), "code_books": len({h["bookid"] for h in code_hits})})
        conn.execute(
            """
            INSERT INTO numeric_anchor_constraint_items
                (run_id, anchor, anchor_role, direct_digit_hit_count,
                 direct_digit_book_count, reconstructed_code_hit_count,
                 reconstructed_code_book_count, evidence_tier, constraint_status,
                 next_action, evidence_json, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                anchor,
                role,
                sum(len(h["positions"]) for h in direct_hits),
                len({h["bookid"] for h in direct_hits}),
                sum(len(h["positions"]) for h in code_hits),
                len({h["bookid"] for h in code_hits}),
                tier,
                status,
                next_action,
                jdump(evidence),
                jdump({"evidence": evidence, "gloss_allowed": False}),
            ),
        )
    decision = "NUMERIC_ANCHOR_CONSTRAINT_AUDIT_READY_NO_GLOSS"
    conn.execute(
        """
        UPDATE numeric_anchor_constraint_probe_runs
        SET direct_hit_anchor_count=?, decision=?, payload_json=?
        WHERE run_id=?
        """,
        (direct_hit_anchors, decision, jdump({"anchors": summaries, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "anchor_count": len(ANCHORS), "direct_hit_anchor_count": direct_hit_anchors, "anchors": summaries, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
