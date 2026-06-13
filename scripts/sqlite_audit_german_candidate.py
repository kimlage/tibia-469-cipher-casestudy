#!/usr/bin/env python3
"""Audit semantic and mechanical debt in the active German candidate."""

from __future__ import annotations

import argparse
import json
import re
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


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS german_candidate_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_canonical_run_id INTEGER,
            source_german_run_id INTEGER NOT NULL,
            odd_length_books INTEGER NOT NULL,
            terminal_digit_histogram_json TEXT NOT NULL,
            unknown_groups INTEGER NOT NULL,
            repeated_unknown_groups INTEGER NOT NULL,
            low_coverage_books INTEGER NOT NULL,
            priority_items INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS german_candidate_odd_terminal_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            digit_len INTEGER NOT NULL,
            terminal_digit TEXT NOT NULL,
            decoded_tail TEXT,
            english_tail TEXT,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS german_candidate_unknown_group_items (
            run_id INTEGER NOT NULL,
            unknown_group TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            bookids_json TEXT NOT NULL,
            sample_context_json TEXT NOT NULL,
            priority_score REAL NOT NULL,
            next_test TEXT NOT NULL,
            PRIMARY KEY (run_id, unknown_group)
        );

        CREATE INDEX IF NOT EXISTS idx_german_unknown_priority
            ON german_candidate_unknown_group_items(run_id, priority_score DESC);
        """
    )


def brace_groups(text: str | None) -> list[str]:
    if not text:
        return []
    return re.findall(r"\{([^{}]*)\}", text)


def contexts(text: str | None, group: str, radius: int = 48) -> list[str]:
    if not text:
        return []
    target = "{" + group + "}"
    out: list[str] = []
    start = 0
    while True:
        idx = text.find(target, start)
        if idx < 0:
            break
        out.append(text[max(0, idx - radius) : min(len(text), idx + len(target) + radius)])
        start = idx + len(target)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--low-coverage-threshold", type=float, default=85.0)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    german_run = one(conn, "SELECT * FROM german_candidate_runs ORDER BY run_id DESC LIMIT 1")
    canonical_run = conn.execute(
        """
        SELECT *
        FROM canonical_candidate_runs
        WHERE german_candidate_run_id=?
        ORDER BY run_id DESC
        LIMIT 1
        """,
        (german_run["run_id"],),
    ).fetchone()
    books = conn.execute(
        """
        SELECT gb.*, sb.digits
        FROM german_candidate_books gb
        LEFT JOIN (
            SELECT
                CAST(bookid AS INTEGER) AS bookid_int,
                MAX(digits) AS digits
            FROM sheet__books
            WHERE bookid IS NOT NULL
            GROUP BY CAST(bookid AS INTEGER)
        ) sb
          ON sb.bookid_int=CAST(gb.bookid AS INTEGER)
        WHERE gb.run_id=?
        ORDER BY CAST(gb.bookid AS INTEGER)
        """,
        (german_run["run_id"],),
    ).fetchall()

    terminal_hist = Counter()
    unknown_hist = Counter()
    unknown_books: dict[str, set[str]] = {}
    unknown_contexts: dict[str, list[dict[str, str]]] = {}
    low_coverage_books = 0
    odd_books = 0

    cur = conn.execute(
        """
        INSERT INTO german_candidate_audit_runs
            (created_at, source_canonical_run_id, source_german_run_id, odd_length_books,
             terminal_digit_histogram_json, unknown_groups, repeated_unknown_groups,
             low_coverage_books, priority_items, payload_json)
        VALUES (?, ?, ?, 0, ?, 0, 0, 0, 0, ?)
        """,
        (
            utc_now(),
            canonical_run["run_id"] if canonical_run else None,
            german_run["run_id"],
            "{}",
            "{}",
        ),
    )
    audit_run_id = int(cur.lastrowid)

    for row in books:
        digits = row["digits"] or ""
        decoded = row["decoded_german"] or ""
        english = row["english"] or ""
        if row["coverage_pct"] is not None and float(row["coverage_pct"]) < args.low_coverage_threshold:
            low_coverage_books += 1
        if len(digits) % 2 == 1:
            odd_books += 1
            terminal = digits[-1:]
            terminal_hist[terminal] += 1
            conn.execute(
                """
                INSERT INTO german_candidate_odd_terminal_items
                    (run_id, bookid, digit_len, terminal_digit, decoded_tail, english_tail, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_run_id,
                    row["bookid"],
                    len(digits),
                    terminal,
                    decoded[-120:],
                    english[-120:],
                    jdump({"coverage_pct": row["coverage_pct"]}),
                ),
            )
        for group in brace_groups(decoded):
            normalized = group.strip() or "<empty>"
            unknown_hist[normalized] += 1
            unknown_books.setdefault(normalized, set()).add(str(row["bookid"]))
            bucket = unknown_contexts.setdefault(normalized, [])
            if len(bucket) < 5:
                for ctx in contexts(decoded, group):
                    if len(bucket) >= 5:
                        break
                    bucket.append({"bookid": str(row["bookid"]), "context": ctx})

    repeated_unknowns = sum(1 for _, count in unknown_hist.items() if count > 1)
    for group, count in unknown_hist.items():
        bookids = sorted(unknown_books[group], key=lambda x: int(x) if x.isdigit() else x)
        priority = float(count * 10 + len(bookids) * 3)
        if len(group) > 8:
            priority += 5.0
        next_test = "cluster_repeated_unknown_against_mapping_and_context"
        if count == 1:
            next_test = "manual_context_only_do_not_promote_without_external_anchor"
        conn.execute(
            """
            INSERT INTO german_candidate_unknown_group_items
                (run_id, unknown_group, occurrence_count, bookids_json, sample_context_json,
                 priority_score, next_test)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audit_run_id,
                group,
                count,
                jdump(bookids),
                jdump(unknown_contexts.get(group, [])),
                priority,
                next_test,
            ),
        )

    priority_items = conn.execute(
        "SELECT COUNT(*) FROM german_candidate_unknown_group_items WHERE run_id=?",
        (audit_run_id,),
    ).fetchone()[0]
    conn.execute(
        """
        UPDATE german_candidate_audit_runs
        SET odd_length_books=?,
            terminal_digit_histogram_json=?,
            unknown_groups=?,
            repeated_unknown_groups=?,
            low_coverage_books=?,
            priority_items=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            odd_books,
            jdump(dict(sorted(terminal_hist.items()))),
            sum(unknown_hist.values()),
            repeated_unknowns,
            low_coverage_books,
            priority_items,
            jdump(
                {
                    "source": "german_candidate_books",
                    "low_coverage_threshold": args.low_coverage_threshold,
                    "meaning": "mechanical/semantic audit debt, not failure of pair mapping",
                }
            ),
            audit_run_id,
        ),
    )
    conn.commit()

    top_unknowns = conn.execute(
        """
        SELECT unknown_group, occurrence_count, bookids_json, priority_score, next_test
        FROM german_candidate_unknown_group_items
        WHERE run_id=?
        ORDER BY priority_score DESC, occurrence_count DESC, unknown_group
        LIMIT 12
        """,
        (audit_run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "audit_run_id": audit_run_id,
                "source_german_run_id": int(german_run["run_id"]),
                "source_canonical_run_id": int(canonical_run["run_id"]) if canonical_run else None,
                "odd_length_books": odd_books,
                "terminal_digit_histogram": dict(sorted(terminal_hist.items())),
                "unknown_groups_total_occurrences": sum(unknown_hist.values()),
                "unknown_groups_distinct": len(unknown_hist),
                "repeated_unknown_groups": repeated_unknowns,
                "low_coverage_books": low_coverage_books,
                "top_unknowns": [dict(row) for row in top_unknowns],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
