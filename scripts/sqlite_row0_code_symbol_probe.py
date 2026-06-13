#!/usr/bin/env python3
"""Infer the row0/base code->symbol model from SQLite digit model tables.

This uses the operational SQLite import only. It validates the model:
- decodedbase length equals baselen;
- observed digits are consumed exactly when omitted row0 codes contribute one digit;
- code->symbol and symbol->code distributions are inferred from the data itself.
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


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS row0_code_symbol_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            book_count INTEGER NOT NULL,
            valid_books INTEGER NOT NULL,
            invalid_books INTEGER NOT NULL,
            total_base_symbols INTEGER NOT NULL,
            total_observed_digits INTEGER NOT NULL,
            total_omitted_zero_codes INTEGER NOT NULL,
            distinct_codes INTEGER NOT NULL,
            conflicting_codes INTEGER NOT NULL,
            distinct_symbols INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS row0_code_symbol_probe_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            baselen INTEGER NOT NULL,
            decodedbase_len INTEGER NOT NULL,
            digitslen INTEGER NOT NULL,
            consumed_digits INTEGER NOT NULL,
            insertedzeros INTEGER NOT NULL,
            omitted_positions_json TEXT NOT NULL,
            omitted_codes_json TEXT NOT NULL,
            valid INTEGER NOT NULL,
            reconstructed_code_stream TEXT NOT NULL,
            decodedbase TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS row0_code_symbol_counts (
            run_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            symbol TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            omitted_count INTEGER NOT NULL,
            written_count INTEGER NOT NULL,
            PRIMARY KEY (run_id, code, symbol)
        );

        CREATE TABLE IF NOT EXISTS row0_symbol_code_counts (
            run_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            code TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            omitted_count INTEGER NOT NULL,
            written_count INTEGER NOT NULL,
            PRIMARY KEY (run_id, symbol, code)
        );

        CREATE INDEX IF NOT EXISTS idx_row0_code_symbol_code
            ON row0_code_symbol_counts(run_id, code, occurrence_count DESC);
        CREATE INDEX IF NOT EXISTS idx_row0_symbol_code_symbol
            ON row0_symbol_code_counts(run_id, symbol, occurrence_count DESC);
        """
    )


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value))
    except Exception:
        return default


def parse_ints(raw: str | None) -> list[int]:
    if not raw:
        return []
    return [int(x.strip()) for x in str(raw).replace("|", ",").split(",") if x.strip().isdigit()]


def parse_codes(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [x.strip() for x in str(raw).split() if x.strip()]


def reconstruct_book(row: sqlite3.Row) -> dict[str, Any]:
    digits = row["digits"] or ""
    decodedbase = row["decodedbase"] or ""
    baselen = as_int(row["baselen"], len(decodedbase))
    insertedzeros = as_int(row["insertedzeros"])
    omit_positions = parse_ints(row["omitidxs_1based"])
    omit_codes = parse_codes(row["omitcodes"])
    omit_by_pos: dict[int, str] = {}
    for pos, code in zip(omit_positions, omit_codes):
        omit_by_pos[pos] = code
    code_stream: list[str] = []
    symbol_events: list[tuple[str, str, bool]] = []
    cursor = 0
    valid = True
    if len(decodedbase) != baselen:
        valid = False
    for idx, symbol in enumerate(decodedbase, start=1):
        if idx in omit_by_pos:
            code = omit_by_pos[idx]
            if cursor >= len(digits) or not code.endswith(digits[cursor : cursor + 1]):
                valid = False
            cursor += 1
            omitted = True
        else:
            code = digits[cursor : cursor + 2]
            if len(code) != 2:
                valid = False
            cursor += 2
            omitted = False
        code_stream.append(code)
        symbol_events.append((code, symbol, omitted))
    if cursor != len(digits):
        valid = False
    if len(omit_positions) != insertedzeros or len(omit_codes) != insertedzeros:
        valid = False
    return {
        "bookid": str(row["bookid"]),
        "baselen": baselen,
        "decodedbase_len": len(decodedbase),
        "digitslen": len(digits),
        "consumed_digits": cursor,
        "insertedzeros": insertedzeros,
        "omit_positions": omit_positions,
        "omit_codes": omit_codes,
        "valid": valid,
        "code_stream": code_stream,
        "symbol_events": symbol_events,
        "decodedbase": decodedbase,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    rows = conn.execute(
        """
        SELECT
            b.bookid,
            b.digits,
            b.decodedbase,
            m.baselen,
            m.insertedzeros,
            m.omitidxs_1based,
            m.omitcodes
        FROM sheet__books b
        JOIN sheet__booksdigitmodel_v118 m USING (bookid)
        WHERE b.bookid IS NOT NULL
        GROUP BY CAST(b.bookid AS INTEGER)
        ORDER BY CAST(b.bookid AS INTEGER)
        """
    ).fetchall()

    cur = conn.execute(
        """
        INSERT INTO row0_code_symbol_probe_runs
            (created_at, book_count, valid_books, invalid_books,
             total_base_symbols, total_observed_digits, total_omitted_zero_codes,
             distinct_codes, conflicting_codes, distinct_symbols, decision, payload_json)
        VALUES (?, 0, 0, 0, 0, 0, 0, 0, 0, 0, ?, ?)
        """,
        (utc_now(), "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    code_symbol_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    valid_books = 0
    invalid_books = 0
    total_base_symbols = 0
    total_observed_digits = 0
    total_omitted = 0
    for row in rows:
        rec = reconstruct_book(row)
        valid_books += 1 if rec["valid"] else 0
        invalid_books += 0 if rec["valid"] else 1
        total_base_symbols += rec["baselen"]
        total_observed_digits += rec["digitslen"]
        total_omitted += rec["insertedzeros"]
        for code, symbol, omitted in rec["symbol_events"]:
            code_symbol_counts[(code, symbol)]["omitted" if omitted else "written"] += 1
        conn.execute(
            """
            INSERT INTO row0_code_symbol_probe_books
                (run_id, bookid, baselen, decodedbase_len, digitslen, consumed_digits,
                 insertedzeros, omitted_positions_json, omitted_codes_json, valid,
                 reconstructed_code_stream, decodedbase, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rec["bookid"],
                rec["baselen"],
                rec["decodedbase_len"],
                rec["digitslen"],
                rec["consumed_digits"],
                rec["insertedzeros"],
                jdump(rec["omit_positions"]),
                jdump(rec["omit_codes"]),
                1 if rec["valid"] else 0,
                " ".join(rec["code_stream"]),
                rec["decodedbase"],
                "{}",
            ),
        )

    code_to_symbols: dict[str, set[str]] = defaultdict(set)
    symbol_to_codes: dict[str, set[str]] = defaultdict(set)
    for (code, symbol), counts in sorted(code_symbol_counts.items()):
        total = counts["omitted"] + counts["written"]
        code_to_symbols[code].add(symbol)
        symbol_to_codes[symbol].add(code)
        conn.execute(
            """
            INSERT INTO row0_code_symbol_counts
                (run_id, code, symbol, occurrence_count, omitted_count, written_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, code, symbol, total, counts["omitted"], counts["written"]),
        )
        conn.execute(
            """
            INSERT INTO row0_symbol_code_counts
                (run_id, symbol, code, occurrence_count, omitted_count, written_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, symbol, code, total, counts["omitted"], counts["written"]),
        )

    conflicting = sum(1 for symbols in code_to_symbols.values() if len(symbols) > 1)
    decision = "ROW0_CODE_SYMBOL_MODEL_VALIDATED" if invalid_books == 0 and conflicting == 0 else "ROW0_CODE_SYMBOL_MODEL_HAS_CONFLICTS"
    conn.execute(
        """
        UPDATE row0_code_symbol_probe_runs
        SET book_count=?,
            valid_books=?,
            invalid_books=?,
            total_base_symbols=?,
            total_observed_digits=?,
            total_omitted_zero_codes=?,
            distinct_codes=?,
            conflicting_codes=?,
            distinct_symbols=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            len(rows),
            valid_books,
            invalid_books,
            total_base_symbols,
            total_observed_digits,
            total_omitted,
            len(code_to_symbols),
            conflicting,
            len(symbol_to_codes),
            decision,
            jdump(
                {
                    "meaning": "base digit model, not external German mapping",
                    "symbols_by_code": {code: sorted(symbols) for code, symbols in sorted(code_to_symbols.items())},
                }
            ),
            run_id,
        ),
    )
    conn.commit()

    top_codes = conn.execute(
        """
        SELECT code, symbol, occurrence_count, omitted_count, written_count
        FROM row0_code_symbol_counts
        WHERE run_id=?
        ORDER BY occurrence_count DESC, code, symbol
        LIMIT 25
        """,
        (run_id,),
    ).fetchall()
    row0_codes = conn.execute(
        """
        SELECT code, symbol, occurrence_count, omitted_count, written_count
        FROM row0_code_symbol_counts
        WHERE run_id=? AND code LIKE '0_'
        ORDER BY code, occurrence_count DESC
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "row0_code_symbol_run_id": run_id,
                "decision": decision,
                "book_count": len(rows),
                "valid_books": valid_books,
                "invalid_books": invalid_books,
                "total_base_symbols": total_base_symbols,
                "total_observed_digits": total_observed_digits,
                "total_omitted_zero_codes": total_omitted,
                "distinct_codes": len(code_to_symbols),
                "conflicting_codes": conflicting,
                "distinct_symbols": len(symbol_to_codes),
                "top_codes": [dict(row) for row in top_codes],
                "row0_codes": [dict(row) for row in row0_codes],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
