#!/usr/bin/env python3
"""Build final honest reading layer v2 with LIV phase-slot containment."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists final_honest_reading_v2_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            book_count integer not null,
            audit_covered_book_count integer not null,
            phase_slot_contained_book_count integer not null,
            unresolved_book_count integer not null,
            semantic_gloss_allowed_count integer not null,
            operational_coverage_pct real not null,
            semantic_gloss_pct real not null,
            payload_json text not null
        );

        create table if not exists final_honest_reading_v2_books (
            run_id integer not null,
            bookid text not null,
            reading_status text not null,
            audit_covered integer not null,
            gloss_allowed integer not null,
            honest_text text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from final_honest_reading_v2_runs").fetchone()[0]
    source_run_id = conn.execute("select max(run_id) from final_honest_reading_books").fetchone()[0]
    liv_run_id = conn.execute("select max(run_id) from liv_slot_contrast_items").fetchone()[0]
    liv_books = {
        row["bookid"]: row
        for row in conn.execute(
            """
            select bookid, slot_token, right_token, slot_class, left_context, right_context
            from liv_slot_contrast_items
            where run_id = ? and bookid in ('58','59')
            """,
            (liv_run_id,),
        )
    }

    rows = list(
        conn.execute(
            """
            select bookid, reading_status, audit_covered, honest_text, evidence_json
            from final_honest_reading_books
            where run_id = ?
            order by cast(bookid as integer)
            """,
            (source_run_id,),
        )
    )

    covered = 0
    phase_slot = 0
    unresolved = 0
    gloss = 0
    for row in rows:
        bookid = row["bookid"]
        if bookid in liv_books:
            status = "CONTAINED_PHASE_SLOT_PATTERN_NO_GLOSS"
            text = row["honest_text"].replace(f"<CONTAINED_UNRESOLVED:{bookid}>", f"<CONTAINED_PHASE_SLOT:LIV_{liv_books[bookid]['slot_token']}_N:{bookid}>")
            evidence = {
                "source": "liv_slot_contrast_probe",
                "liv_slot": dict(liv_books[bookid]),
                "previous_status": row["reading_status"],
            }
            phase_slot += 1
        else:
            status = row["reading_status"]
            text = row["honest_text"]
            evidence = json.loads(row["evidence_json"]) if row["evidence_json"] else {}
            if "UNRESOLVED" in status:
                unresolved += 1

        covered += 1
        conn.execute(
            """
            insert into final_honest_reading_v2_books
            (run_id, bookid, reading_status, audit_covered, gloss_allowed,
             honest_text, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bookid,
                status,
                1,
                0,
                text,
                json.dumps(evidence, ensure_ascii=False),
            ),
        )

    book_count = len(rows)
    operational_pct = round(100.0 * covered / book_count, 2) if book_count else 0.0
    semantic_pct = round(100.0 * gloss / book_count, 2) if book_count else 0.0
    decision = "FINAL_HONEST_READING_V2_PHASE_SLOT_COVERAGE_NO_SEMANTIC_TRANSLATION"
    conn.execute(
        """
        insert into final_honest_reading_v2_runs
        (run_id, created_at, decision, book_count, audit_covered_book_count,
         phase_slot_contained_book_count, unresolved_book_count,
         semantic_gloss_allowed_count, operational_coverage_pct, semantic_gloss_pct,
         payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            book_count,
            covered,
            phase_slot,
            unresolved,
            gloss,
            operational_pct,
            semantic_pct,
            json.dumps({"source_run_id": source_run_id, "liv_run_id": liv_run_id}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "book_count": book_count,
                "audit_covered_book_count": covered,
                "phase_slot_contained_book_count": phase_slot,
                "unresolved_book_count": unresolved,
                "semantic_gloss_allowed_count": gloss,
                "operational_coverage_pct": operational_pct,
                "semantic_gloss_pct": semantic_pct,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
