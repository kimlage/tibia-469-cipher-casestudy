#!/usr/bin/env python3
"""Audit functional marker coverage over row0 books using current policy patterns."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"

PATTERNS = [
    ("STAR_00", ["*00"]),
    ("LTAST_TAIL", ["L", "T", "A", "S", "T", "T", "N"]),
    ("BENNA_FORMULA", ["B", "E", "N", "N", "A"]),
    ("NAESE_IVIFAST", ["I", "V", "I", "F", "A", "S", "T", "F", "N", "E", "I", "E", "I", "N", "T", "A"]),
    ("C68_FATCT_SLOT", ["E", "S", "E", "S", "T", "I", "E", "N", "F", "A", "T", "C68", "T", "I", "V", "V", "T", "I", "S", "E", "T"]),
    ("O23_ONAF", ["O23", "N", "A", "F", "I", "E", "I"]),
    ("C86_EVIEFIIN_TO_VN_C68_TIIN", ["C86", "E", "V", "I", "E", "F", "I", "I", "N", "I", "*00", "V", "N", "C68", "T", "I", "I", "N"]),
    ("C86_EBFAI_TO_VINVIN", ["C86", "E", "B", "F", "A", "I", "*00", "V", "L", "V", "E", "E", "I", "I", "V", "E", "V", "I", "N", "V", "I", "N"]),
    ("C86_OPERATOR_OPEN", ["*00", "I", "C86", "E"]),
    ("R20_VAETRFEVAST", ["V", "A", "E", "T", "R20", "F", "E", "V", "A", "S", "T"]),
    ("R02_TRVEIIVNTBB", ["T", "R02", "V", "E", "I", "I", "V", "N", "T", "B", "B"]),
    ("VINVIN_VTLR", ["V", "I", "N", "V", "I", "N", "S", "T", "A", "E", "*00", "V", "T", "L", "R20", "N", "E", "F", "I", "E"]),
]


def find_count(tokens: list[str], pattern: list[str]) -> int:
    count = 0
    size = len(pattern)
    for idx in range(0, len(tokens) - size + 1):
        if tokens[idx : idx + size] == pattern:
            count += 1
    return count


def local_context_counts(conn: sqlite3.Connection) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    row = conn.execute("SELECT run_id FROM zero_pair_context_policy_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        return counts
    items = conn.execute(
        """
        SELECT context_id, books_json
        FROM zero_pair_context_policy_items
        WHERE run_id=? AND policy_status='LOCAL_CONTEXT_READY'
        """,
        (row["run_id"],),
    ).fetchall()
    for item in items:
        for bookid in json.loads(item["books_json"] or "[]"):
            counts.setdefault(str(bookid), {})[item["context_id"]] = 1
    row = conn.execute("SELECT run_id FROM book30_split_context_policy_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is not None:
        items = conn.execute(
            """
            SELECT context_id, books_json
            FROM book30_split_context_policy_items
            WHERE run_id=? AND policy_status='LOCAL_CONTEXT_READY'
            """,
            (row["run_id"],),
        ).fetchall()
        for item in items:
            for bookid in json.loads(item["books_json"] or "[]"):
                counts.setdefault(str(bookid), {})[item["context_id"]] = 1
    row = conn.execute("SELECT run_id FROM c68_8_23_context_policy_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is not None:
        items = conn.execute(
            """
            SELECT context_id, books_json
            FROM c68_8_23_context_policy_items
            WHERE run_id=? AND policy_status='LOCAL_CONTEXT_READY'
            """,
            (row["run_id"],),
        ).fetchall()
        for item in items:
            for bookid in json.loads(item["books_json"] or "[]"):
                counts.setdefault(str(bookid), {})[item["context_id"]] = 1
    row = conn.execute("SELECT run_id FROM r20_livrn_audit_context_policy_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is not None:
        items = conn.execute(
            """
            SELECT context_id, books_json
            FROM r20_livrn_audit_context_policy_items
            WHERE run_id=? AND policy_status='AUDIT_CONTEXT'
            """,
            (row["run_id"],),
        ).fetchall()
        for item in items:
            for bookid in json.loads(item["books_json"] or "[]"):
                counts.setdefault(str(bookid), {})[item["context_id"]] = 1
    row = conn.execute("SELECT run_id FROM book7_audit_context_policy_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is not None:
        items = conn.execute(
            """
            SELECT context_id, books_json
            FROM book7_audit_context_policy_items
            WHERE run_id=? AND policy_status='AUDIT_CONTEXT'
            """,
            (row["run_id"],),
        ).fetchall()
        for item in items:
            for bookid in json.loads(item["books_json"] or "[]"):
                counts.setdefault(str(bookid), {})[item["context_id"]] = 1
    row = conn.execute("SELECT run_id FROM book49_audit_context_policy_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is not None:
        items = conn.execute(
            """
            SELECT context_id, books_json
            FROM book49_audit_context_policy_items
            WHERE run_id=? AND policy_status='AUDIT_CONTEXT'
            """,
            (row["run_id"],),
        ).fetchall()
        for item in items:
            for bookid in json.loads(item["books_json"] or "[]"):
                counts.setdefault(str(bookid), {})[item["context_id"]] = 1
    return counts


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db, timeout=30)
    conn.row_factory = sqlite3.Row
    run_id = latest_id(conn, "row0_variant_frontier_runs")
    rows = conn.execute(
        """
        SELECT bookid, token_count, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (run_id,),
    ).fetchall()
    local_counts = local_context_counts(conn)
    items: list[dict[str, Any]] = []
    zero: list[str] = []
    for row in rows:
        tokens = json.loads(row["tokens_json"] or "[]")
        counts = {name: find_count(tokens, pattern) for name, pattern in PATTERNS}
        counts = {name: count for name, count in counts.items() if count}
        counts.update(local_counts.get(str(row["bookid"]), {}))
        total = sum(counts.values())
        families = len(counts)
        if total == 0:
            zero.append(str(row["bookid"]))
        items.append(
            {
                "bookid": str(row["bookid"]),
                "token_count": int(row["token_count"]),
                "hit_count": total,
                "family_count": families,
                "families": counts,
            }
        )
    low = sorted(items, key=lambda item: (item["family_count"], item["hit_count"], -item["token_count"]))[:20]
    summary = {
        "decision": "FUNCTIONAL_COVERAGE_AUDIT_READY",
        "book_count": len(items),
        "zero_coverage_count": len(zero),
        "zero_coverage_books": zero,
        "low_coverage": low,
        "gloss_allowed": False,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
