#!/usr/bin/env python3
"""Materialize row0 omission diagnostics as the primary mechanical frontier."""

from __future__ import annotations

import argparse
import json
import sqlite3
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
        CREATE TABLE IF NOT EXISTS row0_omission_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            books INTEGER NOT NULL,
            total_insertedzeros INTEGER NOT NULL,
            odd_digits_books INTEGER NOT NULL,
            odd_insertedzeros_books INTEGER NOT NULL,
            odd_after_reinsert_books INTEGER NOT NULL,
            parity_match_books INTEGER NOT NULL,
            multipath_books INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS row0_omission_probe_book_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            digitslen INTEGER NOT NULL,
            insertedzeros INTEGER NOT NULL,
            pathcount INTEGER NOT NULL,
            row0omitrate REAL,
            odd_digits INTEGER NOT NULL,
            odd_insertedzeros INTEGER NOT NULL,
            odd_after_reinsert INTEGER NOT NULL,
            phase_preferred_offset INTEGER,
            phase_confidence TEXT,
            phase_score_margin REAL,
            risk_score REAL NOT NULL,
            risk_class TEXT NOT NULL,
            omitidxs_1based TEXT,
            omitsymbols TEXT,
            omitcodes TEXT,
            altomitpatterns_1based TEXT,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE INDEX IF NOT EXISTS idx_row0_omission_probe_risk
            ON row0_omission_probe_book_items(run_id, risk_score DESC);
        """
    )


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value))
    except Exception:
        return default


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value))
    except Exception:
        return default


def risk_class(score: float) -> str:
    if score >= 80:
        return "HIGH_ROW0_PHASE_RISK"
    if score >= 45:
        return "MEDIUM_ROW0_PHASE_RISK"
    if score > 0:
        return "LOW_ROW0_PHASE_RISK"
    return "NO_ROW0_RISK"


def next_action(cls: str, pathcount: int, odd_after: int) -> str:
    if odd_after:
        return "investigate_reinsert_failure"
    if pathcount > 1:
        return "enumerate_row0_paths_and_score_by_overlap"
    if cls.startswith("HIGH") or cls.startswith("MEDIUM"):
        return "reconstruct_unique_row0_path_then_compare_phase"
    return "use_as_control_book"


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
            m.bookid,
            m.digitslen,
            m.insertedzeros,
            m.pathcount,
            m.row0omitrate,
            m.omitidxs_1based,
            m.omitsymbols,
            m.omitcodes,
            m.altomitpatterns_1based,
            p.preferred_offset,
            p.confidence AS phase_confidence,
            p.score_margin AS phase_score_margin
        FROM sheet__booksdigitmodel_v118 m
        LEFT JOIN (
            SELECT *
            FROM book_phase_preference_probe_items
            WHERE run_id=(SELECT MAX(run_id) FROM book_phase_preference_probe_items)
        ) p USING (bookid)
        ORDER BY CAST(m.bookid AS INTEGER)
        """
    ).fetchall()

    books = len(rows)
    total_inserted = 0
    odd_digits_books = 0
    odd_inserted_books = 0
    odd_after = 0
    parity_match = 0
    multipath = 0

    cur = conn.execute(
        """
        INSERT INTO row0_omission_probe_runs
            (created_at, books, total_insertedzeros, odd_digits_books,
             odd_insertedzeros_books, odd_after_reinsert_books, parity_match_books,
             multipath_books, decision, payload_json)
        VALUES (?, 0, 0, 0, 0, 0, 0, 0, ?, ?)
        """,
        (
            utc_now(),
            "PENDING",
            "{}",
        ),
    )
    run_id = int(cur.lastrowid)

    for row in rows:
        digitslen = as_int(row["digitslen"])
        inserted = as_int(row["insertedzeros"])
        pathcount = as_int(row["pathcount"], 1)
        rate = as_float(row["row0omitrate"])
        odd_digits = digitslen % 2
        odd_inserted = inserted % 2
        after = (digitslen + inserted) % 2
        total_inserted += inserted
        odd_digits_books += odd_digits
        odd_inserted_books += odd_inserted
        odd_after += after
        parity_match += 1 if odd_digits == odd_inserted else 0
        multipath += 1 if pathcount > 1 else 0
        score = inserted * 8.0 + max(0, pathcount - 1) * 20.0 + rate * 60.0 + odd_digits * 6.0
        cls = risk_class(score)
        action = next_action(cls, pathcount, after)
        conn.execute(
            """
            INSERT INTO row0_omission_probe_book_items
                (run_id, bookid, digitslen, insertedzeros, pathcount, row0omitrate,
                 odd_digits, odd_insertedzeros, odd_after_reinsert,
                 phase_preferred_offset, phase_confidence, phase_score_margin,
                 risk_score, risk_class, omitidxs_1based, omitsymbols, omitcodes,
                 altomitpatterns_1based, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                str(row["bookid"]),
                digitslen,
                inserted,
                pathcount,
                rate,
                odd_digits,
                odd_inserted,
                after,
                row["preferred_offset"],
                row["phase_confidence"],
                row["phase_score_margin"],
                round(score, 6),
                cls,
                row["omitidxs_1based"],
                row["omitsymbols"],
                row["omitcodes"],
                row["altomitpatterns_1based"],
                action,
                "{}",
            ),
        )

    decision = "ROW0_OMISSION_IS_PRIMARY_MECHANICAL_FRONTIER"
    if odd_after != 0 or parity_match != books:
        decision = "ROW0_OMISSION_MODEL_INCOMPLETE"
    conn.execute(
        """
        UPDATE row0_omission_probe_runs
        SET books=?,
            total_insertedzeros=?,
            odd_digits_books=?,
            odd_insertedzeros_books=?,
            odd_after_reinsert_books=?,
            parity_match_books=?,
            multipath_books=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            books,
            total_inserted,
            odd_digits_books,
            odd_inserted_books,
            odd_after,
            parity_match,
            multipath,
            decision,
            jdump(
                {
                    "interpretation": "digitslen parity equals insertedzero parity; reinsertion restores even pair stream",
                    "priority": "enumerate row0 paths before semantic translation",
                }
            ),
            run_id,
        ),
    )
    conn.commit()

    top = conn.execute(
        """
        SELECT bookid, insertedzeros, pathcount, row0omitrate, odd_digits,
               phase_preferred_offset, phase_confidence, phase_score_margin,
               risk_score, risk_class, next_action
        FROM row0_omission_probe_book_items
        WHERE run_id=?
        ORDER BY risk_score DESC, CAST(bookid AS INTEGER)
        LIMIT 20
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "row0_probe_run_id": run_id,
                "decision": decision,
                "books": books,
                "total_insertedzeros": total_inserted,
                "odd_digits_books": odd_digits_books,
                "odd_insertedzeros_books": odd_inserted_books,
                "odd_after_reinsert_books": odd_after,
                "parity_match_books": parity_match,
                "multipath_books": multipath,
                "top_risk_books": [dict(row) for row in top],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
