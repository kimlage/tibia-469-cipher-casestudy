#!/usr/bin/env python3
"""Project semantic safety after R-phase local split."""

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
        create table if not exists projected_semantic_safety_rphase_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            source_btii_run_id integer not null,
            rphase_split_run_id integer not null,
            book_count integer not null,
            projected_clean_book_count integer not null,
            projected_cssr_pct real not null,
            remaining_flagged_book_count integer not null,
            rphase_recovered_book_count integer not null,
            payload_json text not null
        );

        create table if not exists projected_semantic_safety_rphase_items (
            run_id integer not null,
            bookid text not null,
            projected_clean integer not null,
            source_projected_clean integer not null,
            recovered_by_rphase_split integer not null,
            projection_status text not null,
            projected_text text,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from projected_semantic_safety_rphase_runs").fetchone()[0]
    source_run_id = conn.execute("select max(run_id) from projected_semantic_safety_btii_items").fetchone()[0]
    split_run_id = conn.execute("select max(run_id) from rphase_local_split_policy_items").fetchone()[0]
    recovered_books = {
        row["bookid"]
        for row in conn.execute(
            """
            select bookid
            from rphase_local_split_policy_items
            where run_id = ? and split_status = 'R02_PHASE_FRAME_DISPLAY_SAFE_NO_GLOSS'
            """,
            (split_run_id,),
        )
    }
    rows = list(
        conn.execute(
            """
            select bookid, projected_clean, projected_text
            from projected_semantic_safety_btii_items
            where run_id = ?
            order by cast(bookid as integer)
            """,
            (source_run_id,),
        )
    )
    clean = 0
    recovered_count = 0
    for row in rows:
        recovered = row["bookid"] in recovered_books
        projected_clean = bool(row["projected_clean"]) or recovered
        if projected_clean:
            clean += 1
        if recovered:
            recovered_count += 1
        conn.execute(
            """
            insert into projected_semantic_safety_rphase_items
            (run_id, bookid, projected_clean, source_projected_clean,
             recovered_by_rphase_split, projection_status, projected_text, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                1 if projected_clean else 0,
                row["projected_clean"],
                1 if recovered else 0,
                "PROJECTED_SAFE_NO_GLOSS" if projected_clean else "REMAINS_FLAGGED",
                row["projected_text"],
                json.dumps({"source_btii_run_id": source_run_id, "rphase_split_run_id": split_run_id}, ensure_ascii=False),
            ),
        )

    pct = round(100.0 * clean / len(rows), 2) if rows else 0.0
    remaining = len(rows) - clean
    decision = "PROJECTED_SEMANTIC_SAFETY_AFTER_RPHASE_SPLIT_NO_GLOSS"
    conn.execute(
        """
        insert into projected_semantic_safety_rphase_runs
        (run_id, created_at, decision, source_btii_run_id, rphase_split_run_id,
         book_count, projected_clean_book_count, projected_cssr_pct,
         remaining_flagged_book_count, rphase_recovered_book_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            source_run_id,
            split_run_id,
            len(rows),
            clean,
            pct,
            remaining,
            recovered_count,
            json.dumps({"rphase_recovered_books": sorted(recovered_books, key=int)}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "book_count": len(rows),
                "projected_clean_book_count": clean,
                "projected_cssr_pct": pct,
                "remaining_flagged_book_count": remaining,
                "rphase_recovered_book_count": recovered_count,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
