#!/usr/bin/env python3
"""Q25: materialize AUDIT_ONLY labels for the external German candidate."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q25_external_candidate_audit_safe_projection_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q24_run_id INTEGER NOT NULL,
            external_candidate_run_id INTEGER NOT NULL,
            projected_book_count INTEGER NOT NULL,
            projected_contig_count INTEGER NOT NULL,
            unsafe_promote_label_count INTEGER NOT NULL,
            safe_audit_only_label_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q25_external_candidate_audit_safe_projection_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            source_candidate_run_id INTEGER NOT NULL,
            source_candidate_status TEXT NOT NULL,
            safe_status TEXT NOT NULL,
            coverage_pct REAL,
            decoded_primary TEXT,
            english_gloss TEXT,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q25_external_candidate_audit_safe_projection_v1_contigs (
            run_id INTEGER NOT NULL,
            basecontigid TEXT NOT NULL,
            source_candidate_run_id INTEGER NOT NULL,
            safe_status TEXT NOT NULL,
            coverage_avg_pct REAL,
            booksinorder TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, basecontigid)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required table/run: {table}")
    return row


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q24 = latest_row(conn, "human_q24_external_candidate_containment_v1_runs")
    candidate_run_id = int(q24["external_candidate_run_id"])
    books = conn.execute(
        """
        SELECT *
        FROM canonical_candidate_books
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (candidate_run_id,),
    ).fetchall()
    contigs = conn.execute(
        """
        SELECT *
        FROM canonical_candidate_contigs
        WHERE run_id=?
        ORDER BY CAST(basecontigid AS INTEGER)
        """,
        (candidate_run_id,),
    ).fetchall()

    unsafe_promote_label_count = sum(
        1 for row in books if str(row["promotion_status"]).startswith("PROMOTE")
    )
    safe_audit_only_label_count = len(books) + len(contigs)
    canonical_promotion_allowed_count = 0
    decision = (
        "Q25_EXTERNAL_GERMAN_CANDIDATE_SAFE_AUDIT_PROJECTION_READY_NO_PROMOTION"
        if len(books) == 70
        and unsafe_promote_label_count == 70
        and safe_audit_only_label_count == len(books) + len(contigs)
        and canonical_promotion_allowed_count == 0
        else "Q25_EXTERNAL_CANDIDATE_SAFE_PROJECTION_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "How should future queries read the imported external German candidate?",
        "answer": "Use the Q25 projection tables, where every book/contig is explicitly AUDIT_ONLY_EXTERNAL_CANDIDATE.",
        "blocked_reading": "Do not read old canonical_candidate_books.promotion_status labels as canonical promotion.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q25_external_candidate_audit_safe_projection_v1_runs (
                created_at, decision, q24_run_id, external_candidate_run_id,
                projected_book_count, projected_contig_count,
                unsafe_promote_label_count, safe_audit_only_label_count,
                canonical_promotion_allowed_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q24["run_id"]),
                candidate_run_id,
                len(books),
                len(contigs),
                unsafe_promote_label_count,
                safe_audit_only_label_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q25_external_candidate_audit_safe_projection_v1_books (
                run_id, bookid, source_candidate_run_id, source_candidate_status,
                safe_status, coverage_pct, decoded_primary, english_gloss,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["bookid"]),
                    candidate_run_id,
                    str(row["promotion_status"]),
                    "AUDIT_ONLY_EXTERNAL_CANDIDATE",
                    row["coverage_pct"],
                    row["decoded_primary"],
                    row["english_gloss"],
                    j({"source_payload": row["payload_json"]}),
                )
                for row in books
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q25_external_candidate_audit_safe_projection_v1_contigs (
                run_id, basecontigid, source_candidate_run_id, safe_status,
                coverage_avg_pct, booksinorder, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["basecontigid"]),
                    candidate_run_id,
                    "AUDIT_ONLY_EXTERNAL_CANDIDATE_CONTIG",
                    row["coverage_avg_pct"],
                    row["booksinorder"],
                    j({"source_payload": row["payload_json"]}),
                )
                for row in contigs
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "q24_run_id": int(q24["run_id"]),
                "external_candidate_run_id": candidate_run_id,
                "projected_book_count": len(books),
                "projected_contig_count": len(contigs),
                "unsafe_promote_label_count": unsafe_promote_label_count,
                "safe_audit_only_label_count": safe_audit_only_label_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
