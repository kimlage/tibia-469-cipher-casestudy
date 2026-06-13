#!/usr/bin/env python3
"""Build a variant-aware token layer for the validated row0 corpus.

The base row0 stream collapses multiple two-digit codes into 14 display
symbols. Some collapsed symbols have context-specific subfunctions, so this
layer preserves code+symbol for selected variants while leaving stable symbols
compact.
"""

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

DEFAULT_VARIANT_CODES = {
    "00",  # star/control
    "02",
    "20",  # R variants
    "23",
    "32",  # O variants
    "68",
    "86",  # C variants
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS row0_variant_frontier_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_code_symbol_run_id INTEGER NOT NULL,
            source_variant_split_run_id INTEGER,
            variant_codes_json TEXT NOT NULL,
            book_count INTEGER NOT NULL,
            raw_token_count INTEGER NOT NULL,
            distinct_token_count INTEGER NOT NULL,
            ngram_item_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS row0_variant_book_tokens (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            token_count INTEGER NOT NULL,
            symbol_text TEXT NOT NULL,
            token_text TEXT NOT NULL,
            tokens_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS row0_variant_token_counts (
            run_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            source_codes_json TEXT NOT NULL,
            likely_role TEXT NOT NULL,
            PRIMARY KEY (run_id, token)
        );

        CREATE TABLE IF NOT EXISTS row0_variant_ngram_items (
            run_id INTEGER NOT NULL,
            n INTEGER NOT NULL,
            ngram_key TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            sample_json TEXT NOT NULL,
            priority_score REAL NOT NULL,
            likely_role TEXT NOT NULL,
            next_test TEXT NOT NULL,
            PRIMARY KEY (run_id, n, ngram_key)
        );

        CREATE INDEX IF NOT EXISTS idx_row0_variant_ngram_priority
            ON row0_variant_ngram_items(run_id, priority_score DESC);
        """
    )


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def role_for_token(token: str) -> str:
    if token == "*00":
        return "boundary_operator"
    if token in {"C68", "C86", "R20", "R02", "O23", "O32"}:
        return "variant_preserved_symbol"
    return "base_symbol"


def role_for_ngram(tokens: tuple[str, ...], count: int, book_count: int) -> tuple[str, str]:
    token_set = set(tokens)
    if "*00" in token_set:
        return "operator_crossing_template", "align_operator_crossing_slots"
    if any(tok in token_set for tok in {"C68", "C86", "R20", "R02", "O23", "O32"}):
        return "variant_sensitive_template", "compare_variant_specific_contexts"
    if len(tokens) >= 6 and book_count >= 8:
        return "distributed_template_candidate", "align_prefix_suffix_slots"
    if count >= 8:
        return "repeated_internal_unit", "context_concordance"
    return "background_ngram", "retain_for_stats"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--min-ngram-count", type=int, default=4)
    parser.add_argument("--max-n", type=int, default=10)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    source = one(conn, "SELECT * FROM row0_code_symbol_probe_runs ORDER BY run_id DESC LIMIT 1")
    variant_split = conn.execute("SELECT * FROM code_variant_split_probe_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    books = conn.execute(
        """
        SELECT bookid, decodedbase, reconstructed_code_stream
        FROM row0_code_symbol_probe_books
        WHERE run_id=? AND valid=1
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (source["run_id"],),
    ).fetchall()

    cur = conn.execute(
        """
        INSERT INTO row0_variant_frontier_runs
            (created_at, source_code_symbol_run_id, source_variant_split_run_id,
             variant_codes_json, book_count, raw_token_count, distinct_token_count,
             ngram_item_count, decision, payload_json)
        VALUES (?, ?, ?, ?, 0, 0, 0, 0, ?, ?)
        """,
        (
            utc_now(),
            source["run_id"],
            variant_split["run_id"] if variant_split else None,
            jdump(sorted(DEFAULT_VARIANT_CODES)),
            "PENDING",
            "{}",
        ),
    )
    run_id = int(cur.lastrowid)

    token_counts: Counter[str] = Counter()
    token_books: dict[str, set[str]] = defaultdict(set)
    token_codes: dict[str, set[str]] = defaultdict(set)
    ngram_counts: dict[int, Counter[tuple[str, ...]]] = {n: Counter() for n in range(2, args.max_n + 1)}
    ngram_books: dict[tuple[int, tuple[str, ...]], set[str]] = defaultdict(set)
    ngram_samples: dict[tuple[int, tuple[str, ...]], list[dict[str, Any]]] = defaultdict(list)
    raw_token_count = 0

    for row in books:
        bookid = str(row["bookid"])
        symbols = row["decodedbase"] or ""
        codes = (row["reconstructed_code_stream"] or "").split()
        tokens: list[str] = []
        for idx, symbol in enumerate(symbols):
            code = codes[idx] if idx < len(codes) else ""
            token = f"{symbol}{code}" if code in DEFAULT_VARIANT_CODES else symbol
            tokens.append(token)
            token_counts[token] += 1
            token_books[token].add(bookid)
            if code:
                token_codes[token].add(code)
        raw_token_count += len(tokens)
        conn.execute(
            """
            INSERT INTO row0_variant_book_tokens
                (run_id, bookid, token_count, symbol_text, token_text, tokens_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, bookid, len(tokens), symbols, " ".join(tokens), jdump(tokens)),
        )
        for n in range(2, args.max_n + 1):
            for pos in range(0, len(tokens) - n + 1):
                ng = tuple(tokens[pos : pos + n])
                ngram_counts[n][ng] += 1
                ngram_books[(n, ng)].add(bookid)
                samples = ngram_samples[(n, ng)]
                if len(samples) < 5:
                    samples.append(
                        {
                            "bookid": bookid,
                            "pos": pos + 1,
                            "context": " ".join(tokens[max(0, pos - 5) : min(len(tokens), pos + n + 5)]),
                        }
                    )

    for token, count in token_counts.items():
        conn.execute(
            """
            INSERT INTO row0_variant_token_counts
                (run_id, token, occurrence_count, book_count, source_codes_json, likely_role)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                token,
                count,
                len(token_books[token]),
                jdump(sorted(token_codes[token])),
                role_for_token(token),
            ),
        )

    ngram_items = 0
    for n, counts in ngram_counts.items():
        for ng, count in counts.items():
            if count < args.min_ngram_count:
                continue
            book_count = len(ngram_books[(n, ng)])
            role, next_test = role_for_ngram(ng, count, book_count)
            score = count * 2.0 + book_count * 4.0 + n
            if role == "operator_crossing_template":
                score += 12.0
            elif role == "variant_sensitive_template":
                score += 8.0
            conn.execute(
                """
                INSERT INTO row0_variant_ngram_items
                    (run_id, n, ngram_key, occurrence_count, book_count,
                     sample_json, priority_score, likely_role, next_test)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    n,
                    " ".join(ng),
                    count,
                    book_count,
                    jdump({"bookids": sorted(ngram_books[(n, ng)], key=lambda x: int(x) if x.isdigit() else x)[:30], "samples": ngram_samples[(n, ng)]}),
                    round(score, 6),
                    role,
                    next_test,
                ),
            )
            ngram_items += 1

    conn.execute(
        """
        UPDATE row0_variant_frontier_runs
        SET book_count=?,
            raw_token_count=?,
            distinct_token_count=?,
            ngram_item_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            len(books),
            raw_token_count,
            len(token_counts),
            ngram_items,
            "ROW0_VARIANT_AWARE_FRONTIER_READY",
            jdump({"interpretation": "symbol stream with selected code variants preserved"}),
            run_id,
        ),
    )
    conn.commit()

    top_tokens = conn.execute(
        """
        SELECT token, occurrence_count, book_count, likely_role
        FROM row0_variant_token_counts
        WHERE run_id=?
        ORDER BY occurrence_count DESC
        LIMIT 25
        """,
        (run_id,),
    ).fetchall()
    top_ngrams = conn.execute(
        """
        SELECT n, ngram_key, occurrence_count, book_count, priority_score, likely_role, next_test
        FROM row0_variant_ngram_items
        WHERE run_id=?
        ORDER BY priority_score DESC, occurrence_count DESC
        LIMIT 30
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "variant_frontier_run_id": run_id,
                "source_code_symbol_run_id": int(source["run_id"]),
                "book_count": len(books),
                "raw_token_count": raw_token_count,
                "distinct_token_count": len(token_counts),
                "ngram_item_count": ngram_items,
                "top_tokens": [dict(row) for row in top_tokens],
                "top_ngrams": [dict(row) for row in top_ngrams],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
