#!/usr/bin/env python3
"""Mask repeated row0/star segments and analyze the residual corpus."""

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
        CREATE TABLE IF NOT EXISTS formula_mask_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_star_boundary_run_id INTEGER NOT NULL,
            source_code_symbol_run_id INTEGER NOT NULL,
            masked_segment_count INTEGER NOT NULL,
            masked_occurrences INTEGER NOT NULL,
            residual_symbol_count INTEGER NOT NULL,
            residual_ngram_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS formula_mask_segments (
            run_id INTEGER NOT NULL,
            mask_id TEXT NOT NULL,
            segment TEXT NOT NULL,
            segment_len INTEGER NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            likely_role TEXT NOT NULL,
            PRIMARY KEY (run_id, mask_id)
        );

        CREATE TABLE IF NOT EXISTS formula_mask_book_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            original_len INTEGER NOT NULL,
            masked_occurrences INTEGER NOT NULL,
            residual_len INTEGER NOT NULL,
            masked_text TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS formula_mask_residual_ngram_items (
            run_id INTEGER NOT NULL,
            n INTEGER NOT NULL,
            ngram TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            sample_json TEXT NOT NULL,
            priority_score REAL NOT NULL,
            next_test TEXT NOT NULL,
            PRIMARY KEY (run_id, n, ngram)
        );
        """
    )


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--min-segment-occ", type=int, default=4)
    parser.add_argument("--min-segment-len", type=int, default=7)
    parser.add_argument("--min-ngram-count", type=int, default=4)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    star_run = one(conn, "SELECT * FROM star_boundary_probe_runs ORDER BY run_id DESC LIMIT 1")
    segments = conn.execute(
        """
        SELECT *
        FROM star_boundary_segment_items
        WHERE run_id=?
          AND occurrence_count>=?
          AND segment_len>=?
        ORDER BY segment_len DESC, occurrence_count DESC
        """,
        (star_run["run_id"], args.min_segment_occ, args.min_segment_len),
    ).fetchall()
    books = conn.execute(
        """
        SELECT bookid, decodedbase
        FROM row0_code_symbol_probe_books
        WHERE run_id=? AND valid=1
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (star_run["source_code_symbol_run_id"],),
    ).fetchall()

    cur = conn.execute(
        """
        INSERT INTO formula_mask_probe_runs
            (created_at, source_star_boundary_run_id, source_code_symbol_run_id,
             masked_segment_count, masked_occurrences, residual_symbol_count,
             residual_ngram_count, decision, payload_json)
        VALUES (?, ?, ?, ?, 0, 0, 0, ?, ?)
        """,
        (
            utc_now(),
            star_run["run_id"],
            star_run["source_code_symbol_run_id"],
            len(segments),
            "PENDING",
            jdump({"min_segment_occ": args.min_segment_occ, "min_segment_len": args.min_segment_len}),
        ),
    )
    run_id = int(cur.lastrowid)

    mask_specs: list[tuple[str, str]] = []
    for idx, seg in enumerate(segments, start=1):
        mask_id = f"<F{idx:02d}>"
        mask_specs.append((mask_id, seg["segment"]))
        conn.execute(
            """
            INSERT INTO formula_mask_segments
                (run_id, mask_id, segment, segment_len, occurrence_count, book_count, likely_role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                mask_id,
                seg["segment"],
                seg["segment_len"],
                seg["occurrence_count"],
                seg["book_count"],
                seg["likely_role"],
            ),
        )

    residual_counts: dict[int, Counter[str]] = {n: Counter() for n in range(2, 8)}
    residual_books: dict[tuple[int, str], set[str]] = defaultdict(set)
    residual_samples: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    masked_occurrences_total = 0
    residual_symbol_total = 0

    for row in books:
        bookid = str(row["bookid"])
        masked = row["decodedbase"] or ""
        masked_occ = 0
        for mask_id, seg in mask_specs:
            count = masked.count(seg)
            if count:
                masked = masked.replace(seg, mask_id)
                masked_occ += count
        residual = "".join(ch for ch in masked if ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ*")
        residual_symbol_total += len(residual)
        masked_occurrences_total += masked_occ
        conn.execute(
            """
            INSERT INTO formula_mask_book_items
                (run_id, bookid, original_len, masked_occurrences, residual_len, masked_text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, bookid, len(row["decodedbase"] or ""), masked_occ, len(residual), masked),
        )
        for n in range(2, 8):
            for pos in range(0, len(residual) - n + 1):
                ng = residual[pos : pos + n]
                residual_counts[n][ng] += 1
                residual_books[(n, ng)].add(bookid)
                samples = residual_samples[(n, ng)]
                if len(samples) < 5:
                    samples.append({"bookid": bookid, "pos": pos + 1, "context": residual[max(0, pos - 10) : pos + n + 10]})

    residual_ngram_count = 0
    for n, counts in residual_counts.items():
        for ng, count in counts.items():
            if count < args.min_ngram_count:
                continue
            book_count = len(residual_books[(n, ng)])
            score = count * 2.0 + book_count * 4.0 + n
            next_test = "residual_context_concordance"
            if "*" in ng:
                next_test = "residual_star_operator_context"
                score += 6.0
            conn.execute(
                """
                INSERT INTO formula_mask_residual_ngram_items
                    (run_id, n, ngram, occurrence_count, book_count,
                     sample_json, priority_score, next_test)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    n,
                    ng,
                    count,
                    book_count,
                    jdump(residual_samples[(n, ng)]),
                    round(score, 6),
                    next_test,
                ),
            )
            residual_ngram_count += 1

    conn.execute(
        """
        UPDATE formula_mask_probe_runs
        SET masked_occurrences=?,
            residual_symbol_count=?,
            residual_ngram_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            masked_occurrences_total,
            residual_symbol_total,
            residual_ngram_count,
            "FORMULA_SEGMENTS_MASKED_RESIDUAL_FRONTIER_READY",
            jdump({"masked_segments": [mask_id for mask_id, _ in mask_specs]}),
            run_id,
        ),
    )
    conn.commit()

    top_residual = conn.execute(
        """
        SELECT n, ngram, occurrence_count, book_count, priority_score, next_test
        FROM formula_mask_residual_ngram_items
        WHERE run_id=?
        ORDER BY priority_score DESC, occurrence_count DESC
        LIMIT 25
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "formula_mask_run_id": run_id,
                "masked_segment_count": len(segments),
                "masked_occurrences": masked_occurrences_total,
                "residual_symbol_count": residual_symbol_total,
                "residual_ngram_count": residual_ngram_count,
                "top_residual": [dict(row) for row in top_residual],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
