#!/usr/bin/env python3
"""Audit rare row0 symbols and operator-like contexts."""

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
RARE_SYMBOLS = ["O", "R", "C", "*"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS rare_symbol_context_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_code_symbol_run_id INTEGER NOT NULL,
            symbol_count INTEGER NOT NULL,
            occurrence_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS rare_symbol_context_summary (
            run_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            code_counts_json TEXT NOT NULL,
            left1_json TEXT NOT NULL,
            right1_json TEXT NOT NULL,
            left2_json TEXT NOT NULL,
            right2_json TEXT NOT NULL,
            position_class_json TEXT NOT NULL,
            likely_role TEXT NOT NULL,
            next_test TEXT NOT NULL,
            PRIMARY KEY (run_id, symbol)
        );

        CREATE TABLE IF NOT EXISTS rare_symbol_context_occurrences (
            run_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            bookid TEXT NOT NULL,
            pos_1based INTEGER NOT NULL,
            position_class TEXT NOT NULL,
            code TEXT,
            left_context TEXT NOT NULL,
            right_context TEXT NOT NULL,
            full_context TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        """
    )


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def position_class(text: str, idx: int) -> str:
    if idx == 0:
        return "book_start"
    if idx == len(text) - 1:
        return "book_end"
    before = text.rfind("*", 0, idx)
    after = text.find("*", idx + 1)
    if text[idx] == "*":
        return "star_operator"
    if before < 0 and after < 0:
        return "no_star_book"
    if before < 0:
        return "before_first_star"
    if after < 0:
        return "after_last_star"
    return "between_stars"


def role(symbol: str, occ: int, left1: Counter[str], right1: Counter[str], pclass: Counter[str]) -> tuple[str, str]:
    if symbol == "*":
        return "structural_boundary_operator", "model_star_as_operator_boundary_in_templates"
    if occ <= 15:
        return "rare_operator_or_slot_marker", "inspect_occurrences_manually_and_by_template_family"
    if len(left1) <= 4 or len(right1) <= 4:
        return "context_restricted_marker", "test_as_template_slot_marker"
    return "rare_symbol_letter_or_class", "compare_against_template_positions"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    source = one(conn, "SELECT * FROM row0_code_symbol_probe_runs ORDER BY run_id DESC LIMIT 1")
    books = conn.execute(
        """
        SELECT bookid, decodedbase, reconstructed_code_stream
        FROM row0_code_symbol_probe_books
        WHERE run_id=? AND valid=1
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (source["run_id"],),
    ).fetchall()
    code_counts = {
        sym: {
            row["code"]: row["occurrence_count"]
            for row in conn.execute(
                """
                SELECT code, occurrence_count
                FROM row0_symbol_code_counts
                WHERE run_id=? AND symbol=?
                ORDER BY occurrence_count DESC
                """,
                (source["run_id"], sym),
            )
        }
        for sym in RARE_SYMBOLS
    }

    cur = conn.execute(
        """
        INSERT INTO rare_symbol_context_probe_runs
            (created_at, source_code_symbol_run_id, symbol_count,
             occurrence_count, decision, payload_json)
        VALUES (?, ?, ?, 0, ?, ?)
        """,
        (utc_now(), source["run_id"], len(RARE_SYMBOLS), "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    total_occ = 0

    for sym in RARE_SYMBOLS:
        left1: Counter[str] = Counter()
        right1: Counter[str] = Counter()
        left2: Counter[str] = Counter()
        right2: Counter[str] = Counter()
        pclasses: Counter[str] = Counter()
        bookids = set()
        occ_count = 0
        for row in books:
            text = row["decodedbase"] or ""
            codes = (row["reconstructed_code_stream"] or "").split()
            for idx, ch in enumerate(text):
                if ch != sym:
                    continue
                occ_count += 1
                total_occ += 1
                bookids.add(str(row["bookid"]))
                pcls = position_class(text, idx)
                pclasses[pcls] += 1
                if idx > 0:
                    left1[text[idx - 1]] += 1
                if idx + 1 < len(text):
                    right1[text[idx + 1]] += 1
                if idx > 1:
                    left2[text[idx - 2 : idx]] += 1
                if idx + 2 < len(text):
                    right2[text[idx + 1 : idx + 3]] += 1
                conn.execute(
                    """
                    INSERT INTO rare_symbol_context_occurrences
                        (run_id, symbol, bookid, pos_1based, position_class,
                         code, left_context, right_context, full_context, payload_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        sym,
                        str(row["bookid"]),
                        idx + 1,
                        pcls,
                        codes[idx] if idx < len(codes) else None,
                        text[max(0, idx - 20) : idx],
                        text[idx + 1 : min(len(text), idx + 21)],
                        text[max(0, idx - 20) : min(len(text), idx + 21)],
                        "{}",
                    ),
                )
        likely, next_test = role(sym, occ_count, left1, right1, pclasses)
        conn.execute(
            """
            INSERT INTO rare_symbol_context_summary
                (run_id, symbol, occurrence_count, book_count, code_counts_json,
                 left1_json, right1_json, left2_json, right2_json,
                 position_class_json, likely_role, next_test)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                sym,
                occ_count,
                len(bookids),
                jdump(code_counts[sym]),
                jdump(left1.most_common(20)),
                jdump(right1.most_common(20)),
                jdump(left2.most_common(20)),
                jdump(right2.most_common(20)),
                jdump(pclasses.most_common()),
                likely,
                next_test,
            ),
        )

    conn.execute(
        """
        UPDATE rare_symbol_context_probe_runs
        SET occurrence_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            total_occ,
            "RARE_SYMBOL_CONTEXTS_READY",
            jdump({"symbols": RARE_SYMBOLS}),
            run_id,
        ),
    )
    conn.commit()

    rows = conn.execute(
        """
        SELECT symbol, occurrence_count, book_count, code_counts_json,
               left1_json, right1_json, position_class_json, likely_role, next_test
        FROM rare_symbol_context_summary
        WHERE run_id=?
        ORDER BY occurrence_count DESC
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "rare_symbol_run_id": run_id,
                "source_code_symbol_run_id": int(source["run_id"]),
                "occurrence_count": total_occ,
                "symbols": [dict(row) for row in rows],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
