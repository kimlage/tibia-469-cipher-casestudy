#!/usr/bin/env python3
"""Corpus-internal BPE/MDL probe for row0 base symbols."""

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
        CREATE TABLE IF NOT EXISTS internal_bpe_mdl_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_code_symbol_run_id INTEGER NOT NULL,
            merges_requested INTEGER NOT NULL,
            merges_applied INTEGER NOT NULL,
            initial_token_count INTEGER NOT NULL,
            final_token_count INTEGER NOT NULL,
            compression_pct REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS internal_bpe_mdl_merges (
            run_id INTEGER NOT NULL,
            merge_rank INTEGER NOT NULL,
            left_token TEXT NOT NULL,
            right_token TEXT NOT NULL,
            merged_token TEXT NOT NULL,
            pair_count INTEGER NOT NULL,
            estimated_savings INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            sample_books_json TEXT NOT NULL,
            PRIMARY KEY (run_id, merge_rank)
        );

        CREATE TABLE IF NOT EXISTS internal_bpe_mdl_token_counts (
            run_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            token_len INTEGER NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            first_seen_rank INTEGER,
            likely_role TEXT NOT NULL,
            sample_books_json TEXT NOT NULL,
            PRIMARY KEY (run_id, token)
        );

        CREATE TABLE IF NOT EXISTS internal_bpe_mdl_book_tokens (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            token_count INTEGER NOT NULL,
            tokens_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def count_pairs(corpus: dict[str, list[str]]) -> tuple[Counter[tuple[str, str]], dict[tuple[str, str], set[str]]]:
    counts: Counter[tuple[str, str]] = Counter()
    books: dict[tuple[str, str], set[str]] = defaultdict(set)
    for bookid, tokens in corpus.items():
        for idx in range(len(tokens) - 1):
            pair = (tokens[idx], tokens[idx + 1])
            counts[pair] += 1
            books[pair].add(bookid)
    return counts, books


def apply_merge(corpus: dict[str, list[str]], pair: tuple[str, str], merged: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    left, right = pair
    for bookid, tokens in corpus.items():
        new_tokens: list[str] = []
        idx = 0
        while idx < len(tokens):
            if idx + 1 < len(tokens) and tokens[idx] == left and tokens[idx + 1] == right:
                new_tokens.append(merged)
                idx += 2
            else:
                new_tokens.append(tokens[idx])
                idx += 1
        out[bookid] = new_tokens
    return out


def role_for(token: str, count: int, book_count: int) -> str:
    if "*" in token:
        return "operator_boundary_unit"
    if len(token) >= 12 and book_count >= 5:
        return "long_formula_unit"
    if len(token) >= 6 and book_count >= 10:
        return "distributed_morpheme_or_formula"
    if len(token) <= 2:
        return "primitive_symbol_pair"
    return "candidate_internal_token"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--merges", type=int, default=120)
    parser.add_argument("--min-pair-count", type=int, default=4)
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
    corpus = {str(row["bookid"]): list(row["decodedbase"] or "") for row in books}
    initial_count = sum(len(tokens) for tokens in corpus.values())

    cur = conn.execute(
        """
        INSERT INTO internal_bpe_mdl_runs
            (created_at, source_code_symbol_run_id, merges_requested,
             merges_applied, initial_token_count, final_token_count,
             compression_pct, decision, payload_json)
        VALUES (?, ?, ?, 0, ?, 0, 0, ?, ?)
        """,
        (
            utc_now(),
            source["run_id"],
            args.merges,
            initial_count,
            "PENDING",
            jdump({"min_pair_count": args.min_pair_count}),
        ),
    )
    run_id = int(cur.lastrowid)

    merge_first_rank: dict[str, int] = {}
    merges_applied = 0
    for rank in range(1, args.merges + 1):
        pair_counts, pair_books = count_pairs(corpus)
        eligible = [(pair, count) for pair, count in pair_counts.items() if count >= args.min_pair_count]
        if not eligible:
            break
        pair, count = max(eligible, key=lambda item: (item[1] * max(1, len(item[0][0]) + len(item[0][1]) - 1), len(pair_books[item[0]]), item[0]))
        merged = pair[0] + pair[1]
        savings = count * max(1, len(merged) - 1)
        merge_first_rank.setdefault(merged, rank)
        conn.execute(
            """
            INSERT INTO internal_bpe_mdl_merges
                (run_id, merge_rank, left_token, right_token, merged_token,
                 pair_count, estimated_savings, book_count, sample_books_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                pair[0],
                pair[1],
                merged,
                count,
                savings,
                len(pair_books[pair]),
                jdump(sorted(pair_books[pair], key=lambda x: int(x) if x.isdigit() else x)[:20]),
            ),
        )
        corpus = apply_merge(corpus, pair, merged)
        merges_applied += 1

    final_count = sum(len(tokens) for tokens in corpus.values())
    compression = (initial_count - final_count) / initial_count * 100.0 if initial_count else 0.0
    token_counts: Counter[str] = Counter()
    token_books: dict[str, set[str]] = defaultdict(set)
    token_samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for bookid, tokens in corpus.items():
        for pos, token in enumerate(tokens, start=1):
            token_counts[token] += 1
            token_books[token].add(bookid)
            if len(token_samples[token]) < 5:
                token_samples[token].append({"bookid": bookid, "pos": pos})
        conn.execute(
            """
            INSERT INTO internal_bpe_mdl_book_tokens
                (run_id, bookid, token_count, tokens_json)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, bookid, len(tokens), jdump(tokens)),
        )

    for token, count in token_counts.items():
        conn.execute(
            """
            INSERT INTO internal_bpe_mdl_token_counts
                (run_id, token, token_len, occurrence_count, book_count,
                 first_seen_rank, likely_role, sample_books_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                token,
                len(token),
                count,
                len(token_books[token]),
                merge_first_rank.get(token),
                role_for(token, count, len(token_books[token])),
                jdump(token_samples[token]),
            ),
        )

    conn.execute(
        """
        UPDATE internal_bpe_mdl_runs
        SET merges_applied=?,
            final_token_count=?,
            compression_pct=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            merges_applied,
            final_count,
            round(compression, 6),
            "INTERNAL_BPE_MDL_TOKENS_READY",
            jdump({"initial_symbols": initial_count, "final_tokens": final_count}),
            run_id,
        ),
    )
    conn.commit()

    top_tokens = conn.execute(
        """
        SELECT token, token_len, occurrence_count, book_count, first_seen_rank, likely_role
        FROM internal_bpe_mdl_token_counts
        WHERE run_id=?
        ORDER BY token_len DESC, occurrence_count DESC
        LIMIT 30
        """,
        (run_id,),
    ).fetchall()
    top_merges = conn.execute(
        """
        SELECT merge_rank, left_token, right_token, merged_token, pair_count, book_count, estimated_savings
        FROM internal_bpe_mdl_merges
        WHERE run_id=?
        ORDER BY merge_rank
        LIMIT 25
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "bpe_mdl_run_id": run_id,
                "source_code_symbol_run_id": int(source["run_id"]),
                "merges_applied": merges_applied,
                "initial_token_count": initial_count,
                "final_token_count": final_count,
                "compression_pct": round(compression, 6),
                "top_merges": [dict(row) for row in top_merges],
                "top_tokens": [dict(row) for row in top_tokens],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
