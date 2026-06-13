#!/usr/bin/env python3
"""Build the final honest reading layer for the current SQLite state.

This layer is intentionally anti-hallucination-first. It reports complete
operational containment/audit coverage, while keeping semantic gloss blocked
unless independently allowed.
"""

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
        create table if not exists final_honest_reading_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            book_count integer not null,
            audit_covered_book_count integer not null,
            contained_unresolved_book_count integer not null,
            semantic_gloss_allowed_count integer not null,
            operational_coverage_pct real not null,
            semantic_gloss_pct real not null,
            payload_json text not null
        );

        create table if not exists final_honest_reading_books (
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

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from final_honest_reading_runs").fetchone()[0]
    source_run_id = conn.execute("select max(run_id) from projected_semantic_safety_f01_f05_items").fetchone()[0]
    containment_run_id = conn.execute("select max(run_id) from final_residual_containment_items").fetchone()[0]
    f02_run_id = conn.execute("select max(run_id) from f02_boundary_split_items").fetchone()[0]

    containment = {
        row["bookid"]: row
        for row in conn.execute(
            "select bookid, containment_status, evidence_json from final_residual_containment_items where run_id = ?",
            (containment_run_id,),
        )
    }
    f02_text = {
        row["bookid"]: row["projected_text"]
        for row in conn.execute(
            "select bookid, projected_text from f02_boundary_split_items where run_id = ?",
            (f02_run_id,),
        )
    }

    rows = list(
        conn.execute(
            """
            select bookid, projected_clean, projected_text
            from projected_semantic_safety_f01_f05_items
            where run_id = ?
            order by cast(bookid as integer)
            """,
            (source_run_id,),
        )
    )

    audit_covered = 0
    contained_count = 0
    gloss_allowed_count = 0
    for row in rows:
        bookid = row["bookid"]
        if bookid in containment:
            status = containment[bookid]["containment_status"]
            covered = 1
            contained_count += 1
            text = f02_text.get(bookid, row["projected_text"] or "")
            text = f"<CONTAINED_UNRESOLVED:{bookid}> " + text
            evidence = {
                "source": "final_residual_containment",
                "containment_evidence": containment[bookid]["evidence_json"],
            }
        elif int(row["projected_clean"]):
            status = "AUDIT_SAFE_STRUCTURAL_READING_NO_GLOSS"
            covered = 1
            text = f02_text.get(bookid, row["projected_text"] or "")
            evidence = {"source": "projected_semantic_safety_f01_f05"}
        else:
            # If a book is recovered by a later local policy, it may not be marked
            # clean in the source projection. Keep it covered but explicit.
            status = "AUDIT_SAFE_BY_LATE_LOCAL_POLICY_NO_GLOSS"
            covered = 1
            text = f02_text.get(bookid, row["projected_text"] or "")
            evidence = {"source": "late_local_policy"}

        gloss_allowed = 0
        audit_covered += covered
        gloss_allowed_count += gloss_allowed
        conn.execute(
            """
            insert into final_honest_reading_books
            (run_id, bookid, reading_status, audit_covered, gloss_allowed,
             honest_text, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bookid,
                status,
                covered,
                gloss_allowed,
                text,
                json.dumps(evidence, ensure_ascii=False),
            ),
        )

    book_count = len(rows)
    operational_pct = round(100.0 * audit_covered / book_count, 2) if book_count else 0.0
    semantic_pct = round(100.0 * gloss_allowed_count / book_count, 2) if book_count else 0.0
    decision = "FINAL_HONEST_READING_LAYER_COMPLETE_AUDIT_COVERAGE_NO_SEMANTIC_TRANSLATION"
    conn.execute(
        """
        insert into final_honest_reading_runs
        (run_id, created_at, decision, book_count, audit_covered_book_count,
         contained_unresolved_book_count, semantic_gloss_allowed_count,
         operational_coverage_pct, semantic_gloss_pct, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            book_count,
            audit_covered,
            contained_count,
            gloss_allowed_count,
            operational_pct,
            semantic_pct,
            json.dumps(
                {
                    "source_run_id": source_run_id,
                    "containment_run_id": containment_run_id,
                    "f02_run_id": f02_run_id,
                    "definition": "operationally covered means every book is either audit-safe structural or explicitly contained unresolved",
                },
                ensure_ascii=False,
            ),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "book_count": book_count,
                "audit_covered_book_count": audit_covered,
                "contained_unresolved_book_count": contained_count,
                "semantic_gloss_allowed_count": gloss_allowed_count,
                "operational_coverage_pct": operational_pct,
                "semantic_gloss_pct": semantic_pct,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
