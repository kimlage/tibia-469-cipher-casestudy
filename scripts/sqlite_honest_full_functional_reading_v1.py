#!/usr/bin/env python3
"""Build an honest full-book functional reading layer for all 70 books.

Every book gets one of:
- FUNCTIONAL_CORE: accepted functional role from consolidated grammar
- FUNCTIONAL_RELATED: related/variant/support role, not core prose
- QUARANTINED_OR_AUDIT: known structural signal that must not become prose
- UNRESOLVED_FUNCTION: no reliable functional role yet

This is deliberately not a human translation layer.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TRUST_TO_STATUS = {
    "CORE": "FUNCTIONAL_CORE",
    "ACCEPTED_STRUCTURAL_EDGE": "FUNCTIONAL_CORE",
    "RELATED_CONTEXT": "FUNCTIONAL_RELATED",
    "VARIANT": "FUNCTIONAL_RELATED",
    "SUPPORT": "FUNCTIONAL_RELATED",
    "QUARANTINED": "QUARANTINED_OR_AUDIT",
    "AUDIT_ONLY": "QUARANTINED_OR_AUDIT",
}

ROLE_REFINEMENTS = {
    "FRAME_FORMULA_OPERATOR": "<FRAME_FORMULA_OPERATOR>",
    "HANDOFF_CONTEXT": "<HANDOFF_CONTEXT>",
    "CONTEXT_PAYLOAD": "<CONTEXT_PAYLOAD>",
    "CANONICAL_SLOT": "<NAESE:CANONICAL_SLOT_OPERATOR>",
    "R02_SLOT_BRIDGE": "<R02_SLOT_BRIDGE>",
    "C86_VINVIN_BRANCH_PAYLOAD": "<VINVIN:C86_PAYLOAD_BRANCH>",
    "R20_BRANCH_HEAD": "<VINVIN:R20_CONNECTOR_BRANCH_HEAD>",
    "R20_CONNECTOR_ENDPOINT": "<VINVIN:R20_CONNECTOR_ENDPOINT>",
    "C86_VINVIN_BRANCH_ENDPOINT": "<VINVIN:C86_PAYLOAD_BRANCH_ENDPOINT>",
    "O23_FNAAST_ENDPOINT": "<O23:SCOPED_ENDPOINT>",
    "TEMPLATE_HEAD": "<BENNA:TEMPLATE_HEAD>",
    "FORMULA_BODY": "<BENNA:FORMULA_BODY>",
    "MIXED_TEMPLATE_FORMULA_HEAD": "<BENNA:MIXED_TEMPLATE_FORMULA_HEAD>",
    "DISPLAY_FORMULA_HEAD": "<BENNA:DISPLAY_FORMULA_HEAD>",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def latest_run(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()[0])


def refine_role(role: str) -> str:
    return ROLE_REFINEMENTS.get(role, f"<{role}>")


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS honest_full_functional_reading_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            total_books INTEGER NOT NULL,
            functional_core_count INTEGER NOT NULL,
            functional_related_count INTEGER NOT NULL,
            quarantined_or_audit_count INTEGER NOT NULL,
            unresolved_function_count INTEGER NOT NULL,
            accepted_prose_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS honest_full_functional_reading_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            status TEXT NOT NULL,
            functional_reading TEXT NOT NULL,
            prose_gloss TEXT NOT NULL,
            source_component TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        )
        """
    )
    book_run = latest_run(conn, "book_structural_reading_v1_runs")
    grammar_run = latest_run(conn, "functional_grammar_synthesis_v1_runs")
    all_books = [str(r["bookid"]) for r in conn.execute("SELECT bookid FROM book_structural_reading_v1_items WHERE run_id=? ORDER BY CAST(bookid AS INT)", (book_run,))]
    grammar_rows = {
        str(r["item_id"]): r
        for r in conn.execute(
            "SELECT * FROM functional_grammar_synthesis_v1_items WHERE run_id=? AND item_type='book'",
            (grammar_run,),
        )
    }
    rows = []
    for bookid in all_books:
        g = grammar_rows.get(bookid)
        if g:
            trust = str(g["status"])
            status = TRUST_TO_STATUS.get(trust, "QUARANTINED_OR_AUDIT")
            reading = refine_role(str(g["role_label"]))
            source = str(g["source_component"])
            evidence = {"grammar_status": trust, "grammar_run": grammar_run}
        else:
            status = "UNRESOLVED_FUNCTION"
            reading = "<UNRESOLVED_FUNCTION>"
            source = "NONE"
            evidence = {"reason": "no consolidated functional grammar role", "grammar_run": grammar_run}
        rows.append((bookid, status, reading, "<NO_ACCEPTED_HUMAN_GLOSS>", source, evidence))
    counts = {status: sum(1 for r in rows if r[1] == status) for status in sorted({r[1] for r in rows})}
    decision = "FULL_FUNCTIONAL_READING_PARTIAL_NO_PROSE_GLOSS"
    cur = conn.execute(
        """
        INSERT INTO honest_full_functional_reading_v1_runs
        (created_at, decision, total_books, functional_core_count, functional_related_count, quarantined_or_audit_count, unresolved_function_count, accepted_prose_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(), decision, len(rows), counts.get("FUNCTIONAL_CORE", 0), counts.get("FUNCTIONAL_RELATED", 0), counts.get("QUARANTINED_OR_AUDIT", 0), counts.get("UNRESOLVED_FUNCTION", 0), 0,
            json.dumps({"source": "functional_grammar_synthesis_v1", "grammar_run": grammar_run, "warning": "not prose translation"}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for bookid, status, reading, gloss, source, evidence in rows:
        conn.execute(
            """
            INSERT INTO honest_full_functional_reading_v1_books
            (run_id, bookid, status, functional_reading, prose_gloss, source_component, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, bookid, status, reading, gloss, source, json.dumps(evidence, sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "total_books": len(rows), "functional_core_count": counts.get("FUNCTIONAL_CORE", 0), "functional_related_count": counts.get("FUNCTIONAL_RELATED", 0), "quarantined_or_audit_count": counts.get("QUARANTINED_OR_AUDIT", 0), "unresolved_function_count": counts.get("UNRESOLVED_FUNCTION", 0), "accepted_prose_gloss_count": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
