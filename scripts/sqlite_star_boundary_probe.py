#!/usr/bin/env python3
"""Probe whether `*` behaves as boundary/operator in row0 base corpus."""

from __future__ import annotations

import argparse
import json
import math
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


def entropy(chars: list[str]) -> float:
    if not chars:
        return 0.0
    counts = Counter(chars)
    total = len(chars)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS star_boundary_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_row0_base_frontier_run_id INTEGER NOT NULL,
            source_code_symbol_run_id INTEGER NOT NULL,
            star_count INTEGER NOT NULL,
            star_books INTEGER NOT NULL,
            internal_star_count INTEGER NOT NULL,
            start_star_count INTEGER NOT NULL,
            end_star_count INTEGER NOT NULL,
            left_entropy REAL NOT NULL,
            right_entropy REAL NOT NULL,
            segment_count INTEGER NOT NULL,
            repeated_segment_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS star_boundary_context_items (
            run_id INTEGER NOT NULL,
            context_key TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            side TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, context_key, side)
        );

        CREATE TABLE IF NOT EXISTS star_boundary_segment_items (
            run_id INTEGER NOT NULL,
            segment TEXT NOT NULL,
            segment_len INTEGER NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            position_class TEXT NOT NULL,
            sample_json TEXT NOT NULL,
            priority_score REAL NOT NULL,
            likely_role TEXT NOT NULL,
            PRIMARY KEY (run_id, segment)
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
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    frontier = one(conn, "SELECT * FROM row0_base_frontier_runs ORDER BY run_id DESC LIMIT 1")
    source_id = frontier["source_code_symbol_run_id"]
    books = conn.execute(
        """
        SELECT bookid, decodedbase
        FROM row0_code_symbol_probe_books
        WHERE run_id=? AND valid=1
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (source_id,),
    ).fetchall()

    left1: Counter[str] = Counter()
    right1: Counter[str] = Counter()
    left2: Counter[str] = Counter()
    right2: Counter[str] = Counter()
    context_books: dict[tuple[str, str], set[str]] = defaultdict(set)
    segment_counts: Counter[str] = Counter()
    segment_books: dict[str, set[str]] = defaultdict(set)
    segment_samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    star_count = 0
    star_books: set[str] = set()
    start_star = 0
    end_star = 0
    internal_star = 0

    for row in books:
        bookid = str(row["bookid"])
        text = row["decodedbase"] or ""
        if "*" in text:
            star_books.add(bookid)
        for idx, ch in enumerate(text):
            if ch != "*":
                continue
            star_count += 1
            if idx == 0:
                start_star += 1
            elif idx == len(text) - 1:
                end_star += 1
            else:
                internal_star += 1
            if idx > 0:
                key = text[idx - 1]
                left1[key] += 1
                context_books[("L1:" + key, "left1")].add(bookid)
            if idx + 1 < len(text):
                key = text[idx + 1]
                right1[key] += 1
                context_books[("R1:" + key, "right1")].add(bookid)
            if idx > 1:
                key = text[idx - 2 : idx]
                left2[key] += 1
                context_books[("L2:" + key, "left2")].add(bookid)
            if idx + 2 < len(text):
                key = text[idx + 1 : idx + 3]
                right2[key] += 1
                context_books[("R2:" + key, "right2")].add(bookid)

        parts = text.split("*")
        for pos, seg in enumerate(parts):
            if not seg:
                continue
            segment_counts[seg] += 1
            segment_books[seg].add(bookid)
            samples = segment_samples[seg]
            if len(samples) < 5:
                if len(parts) == 1:
                    pclass = "whole_book_no_star"
                elif pos == 0:
                    pclass = "before_first_star"
                elif pos == len(parts) - 1:
                    pclass = "after_last_star"
                else:
                    pclass = "between_stars"
                samples.append({"bookid": bookid, "position": pos, "position_class": pclass, "segment": seg[:120]})

    cur = conn.execute(
        """
        INSERT INTO star_boundary_probe_runs
            (created_at, source_row0_base_frontier_run_id, source_code_symbol_run_id,
             star_count, star_books, internal_star_count, start_star_count, end_star_count,
             left_entropy, right_entropy, segment_count, repeated_segment_count,
             decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            frontier["run_id"],
            source_id,
            star_count,
            len(star_books),
            internal_star,
            start_star,
            end_star,
            round(entropy(list(left1.elements())), 6),
            round(entropy(list(right1.elements())), 6),
            len(segment_counts),
            sum(1 for c in segment_counts.values() if c > 1),
            "STAR_IS_STRUCTURAL_OPERATOR_OR_BOUNDARY",
            jdump({"left1": left1.most_common(), "right1": right1.most_common()}),
        ),
    )
    run_id = int(cur.lastrowid)

    for side, counter in [("left1", left1), ("right1", right1), ("left2", left2), ("right2", right2)]:
        for key, count in counter.most_common(40):
            lookup_key = ("L1:" + key if side == "left1" else "R1:" + key if side == "right1" else "L2:" + key if side == "left2" else "R2:" + key, side)
            conn.execute(
                """
                INSERT INTO star_boundary_context_items
                    (run_id, context_key, occurrence_count, book_count, side, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    key,
                    count,
                    len(context_books.get(lookup_key, set())),
                    side,
                    "{}",
                ),
            )

    for seg, count in segment_counts.items():
        if count < 2 and len(seg) < 8:
            continue
        samples = segment_samples[seg]
        classes = Counter(sample["position_class"] for sample in samples)
        pclass = classes.most_common(1)[0][0] if classes else "unknown"
        score = count * 5.0 + len(segment_books[seg]) * 4.0 + min(len(seg), 30)
        role = "repeated_formula_segment" if count > 1 else "long_unique_segment"
        if pclass in {"before_first_star", "after_last_star"}:
            role = "edge_formula_segment" if count > 1 else "edge_unique_segment"
        conn.execute(
            """
            INSERT INTO star_boundary_segment_items
                (run_id, segment, segment_len, occurrence_count, book_count,
                 position_class, sample_json, priority_score, likely_role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                seg,
                len(seg),
                count,
                len(segment_books[seg]),
                pclass,
                jdump(samples),
                round(score, 6),
                role,
            ),
        )

    conn.commit()
    top_segments = conn.execute(
        """
        SELECT segment, segment_len, occurrence_count, book_count,
               position_class, priority_score, likely_role
        FROM star_boundary_segment_items
        WHERE run_id=?
        ORDER BY priority_score DESC, occurrence_count DESC
        LIMIT 20
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "star_boundary_run_id": run_id,
                "star_count": star_count,
                "star_books": len(star_books),
                "internal_star_count": internal_star,
                "start_star_count": start_star,
                "end_star_count": end_star,
                "left_entropy": round(entropy(list(left1.elements())), 6),
                "right_entropy": round(entropy(list(right1.elements())), 6),
                "left1": left1.most_common(),
                "right1": right1.most_common(),
                "segment_count": len(segment_counts),
                "repeated_segment_count": sum(1 for c in segment_counts.values() if c > 1),
                "top_segments": [dict(row) for row in top_segments],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
