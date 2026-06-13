#!/usr/bin/env python3
"""Build a decoding frontier from the validated row0/base symbol corpus."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
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
        CREATE TABLE IF NOT EXISTS row0_base_frontier_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_code_symbol_run_id INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            total_symbols INTEGER NOT NULL,
            distinct_symbols INTEGER NOT NULL,
            separator_symbol TEXT,
            ngram_items INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS row0_base_symbol_counts (
            run_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            frequency_pct REAL NOT NULL,
            PRIMARY KEY (run_id, symbol)
        );

        CREATE TABLE IF NOT EXISTS row0_base_ngram_items (
            run_id INTEGER NOT NULL,
            n INTEGER NOT NULL,
            ngram TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            sample_books_json TEXT NOT NULL,
            priority_score REAL NOT NULL,
            likely_role TEXT NOT NULL,
            next_test TEXT NOT NULL,
            PRIMARY KEY (run_id, n, ngram)
        );

        CREATE TABLE IF NOT EXISTS row0_base_book_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            symbol_len INTEGER NOT NULL,
            star_count INTEGER NOT NULL,
            top_repeated_ngrams_json TEXT NOT NULL,
            decodedbase TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE INDEX IF NOT EXISTS idx_row0_base_ngram_priority
            ON row0_base_ngram_items(run_id, priority_score DESC);
        """
    )


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def likely_role(ngram: str, count: int, book_count: int) -> tuple[str, str]:
    if "*" in ngram:
        return "separator_or_control_ngram", "test_star_as_boundary_or_control_symbol"
    if book_count >= 10 and len(set(ngram)) <= max(2, len(ngram) // 2):
        return "high_repetition_formula", "compare_context_windows_and_contig_positions"
    if book_count >= 8:
        return "distributed_formula_candidate", "build_context_concordance"
    if count >= 5:
        return "local_formula_candidate", "check_overlap_with_book_families"
    return "low_priority_repeat", "retain_for_background_stats"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--min-count", type=int, default=4)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    source = one(conn, "SELECT * FROM row0_code_symbol_probe_runs ORDER BY run_id DESC LIMIT 1")
    books = conn.execute(
        """
        SELECT bookid, decodedbase
        FROM row0_code_symbol_probe_books
        WHERE run_id=? AND valid=1
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (source["run_id"],),
    ).fetchall()

    symbol_counts: Counter[str] = Counter()
    symbol_books: dict[str, set[str]] = defaultdict(set)
    ngram_counts: dict[int, Counter[str]] = {n: Counter() for n in range(2, 9)}
    ngram_books: dict[tuple[int, str], set[str]] = defaultdict(set)
    ngram_samples: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)

    for row in books:
        bookid = str(row["bookid"])
        text = row["decodedbase"] or ""
        for ch in text:
            symbol_counts[ch] += 1
            symbol_books[ch].add(bookid)
        for n in range(2, 9):
            for idx in range(0, len(text) - n + 1):
                ng = text[idx : idx + n]
                ngram_counts[n][ng] += 1
                ngram_books[(n, ng)].add(bookid)
                samples = ngram_samples[(n, ng)]
                if len(samples) < 5:
                    samples.append({"bookid": bookid, "pos": idx + 1, "context": text[max(0, idx - 10) : idx + n + 10]})

    total_symbols = sum(symbol_counts.values())
    separator = "*" if "*" in symbol_counts else None
    cur = conn.execute(
        """
        INSERT INTO row0_base_frontier_runs
            (created_at, source_code_symbol_run_id, book_count, total_symbols,
             distinct_symbols, separator_symbol, ngram_items, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
        """,
        (
            utc_now(),
            source["run_id"],
            len(books),
            total_symbols,
            len(symbol_counts),
            separator,
            "ROW0_BASE_SYMBOL_FRONTIER_READY",
            jdump({"min_count": args.min_count, "n_range": "2..8"}),
        ),
    )
    run_id = int(cur.lastrowid)

    for sym, count in symbol_counts.most_common():
        conn.execute(
            """
            INSERT INTO row0_base_symbol_counts
                (run_id, symbol, occurrence_count, book_count, frequency_pct)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                sym,
                count,
                len(symbol_books[sym]),
                round(count / total_symbols * 100.0, 6),
            ),
        )

    ngram_item_count = 0
    for n, counts in ngram_counts.items():
        for ng, count in counts.items():
            if count < args.min_count:
                continue
            books_for = sorted(ngram_books[(n, ng)], key=lambda x: int(x) if x.isdigit() else x)
            role, next_test = likely_role(ng, count, len(books_for))
            score = count * 2.0 + len(books_for) * 4.0 + n
            if "*" in ng:
                score += 8.0
            conn.execute(
                """
                INSERT INTO row0_base_ngram_items
                    (run_id, n, ngram, occurrence_count, book_count,
                     sample_books_json, priority_score, likely_role, next_test)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    n,
                    ng,
                    count,
                    len(books_for),
                    jdump({"bookids": books_for[:30], "samples": ngram_samples[(n, ng)]}),
                    round(score, 6),
                    role,
                    next_test,
                ),
            )
            ngram_item_count += 1

    for row in books:
        text = row["decodedbase"] or ""
        local = []
        for n in range(3, 8):
            local.extend((ng, c) for ng, c in Counter(text[i : i + n] for i in range(0, len(text) - n + 1)).most_common(5) if c > 1)
        conn.execute(
            """
            INSERT INTO row0_base_book_items
                (run_id, bookid, symbol_len, star_count, top_repeated_ngrams_json, decodedbase)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                str(row["bookid"]),
                len(text),
                text.count("*"),
                jdump(local[:20]),
                text,
            ),
        )

    conn.execute(
        "UPDATE row0_base_frontier_runs SET ngram_items=? WHERE run_id=?",
        (ngram_item_count, run_id),
    )
    conn.commit()

    top_symbols = conn.execute(
        """
        SELECT symbol, occurrence_count, book_count, frequency_pct
        FROM row0_base_symbol_counts
        WHERE run_id=?
        ORDER BY occurrence_count DESC
        """,
        (run_id,),
    ).fetchall()
    top_ngrams = conn.execute(
        """
        SELECT n, ngram, occurrence_count, book_count, priority_score, likely_role, next_test
        FROM row0_base_ngram_items
        WHERE run_id=?
        ORDER BY priority_score DESC, n DESC
        LIMIT 25
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "row0_base_frontier_run_id": run_id,
                "source_code_symbol_run_id": int(source["run_id"]),
                "book_count": len(books),
                "total_symbols": total_symbols,
                "distinct_symbols": len(symbol_counts),
                "separator_symbol": separator,
                "ngram_items": ngram_item_count,
                "top_symbols": [dict(row) for row in top_symbols],
                "top_ngrams": [dict(row) for row in top_ngrams],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
