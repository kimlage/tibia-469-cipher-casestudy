#!/usr/bin/env python3
"""Project semantic safety after accepting F02/LTAST as boundary-only where safe."""

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
        create table if not exists projected_semantic_safety_f02_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            source_projected_run_id integer not null,
            f02_split_run_id integer not null,
            book_count integer not null,
            projected_clean_book_count integer not null,
            projected_cssr_pct real not null,
            remaining_flagged_book_count integer not null,
            f02_recovered_book_count integer not null,
            payload_json text not null
        );

        create table if not exists projected_semantic_safety_f02_items (
            run_id integer not null,
            bookid text not null,
            projected_clean integer not null,
            source_projected_clean integer not null,
            recovered_by_f02_boundary integer not null,
            projection_status text not null,
            projected_text text,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from projected_semantic_safety_f02_runs").fetchone()[0]
    source_run_id = conn.execute("select max(run_id) from projected_semantic_safety_items").fetchone()[0]
    f02_run_id = conn.execute("select max(run_id) from f02_boundary_split_items").fetchone()[0]
    f02_recovered = {
        row["bookid"]: row["projected_text"]
        for row in conn.execute(
            """
            select bookid, projected_text
            from f02_boundary_split_items
            where run_id = ? and split_status = 'BOUNDARY_OPERATOR_ONLY_CANDIDATE_NO_GLOSS'
            """,
            (f02_run_id,),
        )
    }

    rows = list(
        conn.execute(
            """
            select bookid, projected_clean, audit_text
            from projected_semantic_safety_items
            where run_id = ?
            order by cast(bookid as integer)
            """,
            (source_run_id,),
        )
    )
    clean_count = 0
    recovered_count = 0
    for row in rows:
        recovered = row["bookid"] in f02_recovered
        projected_clean = bool(row["projected_clean"]) or recovered
        if projected_clean:
            clean_count += 1
        if recovered:
            recovered_count += 1
        conn.execute(
            """
            insert into projected_semantic_safety_f02_items
            (run_id, bookid, projected_clean, source_projected_clean,
             recovered_by_f02_boundary, projection_status, projected_text, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                1 if projected_clean else 0,
                row["projected_clean"],
                1 if recovered else 0,
                "PROJECTED_SAFE_NO_GLOSS" if projected_clean else "REMAINS_FLAGGED",
                f02_recovered.get(row["bookid"], row["audit_text"]),
                json.dumps({"source_projected_run_id": source_run_id, "f02_split_run_id": f02_run_id}, ensure_ascii=False),
            ),
        )

    pct = round(100.0 * clean_count / len(rows), 2) if rows else 0.0
    remaining = len(rows) - clean_count
    decision = "PROJECTED_SEMANTIC_SAFETY_AFTER_F02_BOUNDARY_NO_GLOSS"
    conn.execute(
        """
        insert into projected_semantic_safety_f02_runs
        (run_id, created_at, decision, source_projected_run_id, f02_split_run_id,
         book_count, projected_clean_book_count, projected_cssr_pct,
         remaining_flagged_book_count, f02_recovered_book_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            source_run_id,
            f02_run_id,
            len(rows),
            clean_count,
            pct,
            remaining,
            recovered_count,
            json.dumps({"f02_recovered_books": sorted(f02_recovered, key=int)}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "book_count": len(rows),
                "projected_clean_book_count": clean_count,
                "projected_cssr_pct": pct,
                "remaining_flagged_book_count": remaining,
                "f02_recovered_book_count": recovered_count,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
