#!/usr/bin/env python3
"""Project semantic safety after formula display masks and local F01/F05 split."""

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
        create table if not exists projected_semantic_safety_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            source_cssr_run_id integer not null,
            book_count integer not null,
            projected_clean_book_count integer not null,
            projected_cssr_pct real not null,
            remaining_flagged_book_count integer not null,
            remaining_blocked_book_count integer not null,
            payload_json text not null
        );

        create table if not exists projected_semantic_safety_items (
            run_id integer not null,
            bookid text not null,
            projected_clean integer not null,
            projection_status text not null,
            source_strict_clean integer not null,
            recovered_by_dead_formula_mask integer not null,
            recovered_by_local_split integer not null,
            blocked_hit_count integer not null,
            audit_text text,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from projected_semantic_safety_runs").fetchone()[0]
    cssr_run_id = conn.execute("select max(run_id) from conservative_semantic_safety_items").fetchone()[0]
    formula_run_id = conn.execute("select max(run_id) from formula_only_mask_promotion_items").fetchone()[0]
    split_run_id = conn.execute("select max(run_id) from f01_f05_local_split_policy_items").fetchone()[0]

    dead_formula_recovered = {
        row["bookid"]
        for row in conn.execute(
            "select bookid from formula_only_mask_promotion_items where run_id = ? and recovered_by_formula_only_mask = 1",
            (formula_run_id,),
        )
    }
    split_recovered = {
        row["bookid"]
        for row in conn.execute(
            """
            select distinct bookid
            from f01_f05_local_split_policy_items
            where run_id = ? and split_status = 'LOCAL_DISPLAY_FORMULA_ONLY_NO_GLOSS'
            """,
            (split_run_id,),
        )
    }

    rows = list(
        conn.execute(
            """
            select bookid, strict_clean, blocked_hit_count, audit_text
            from conservative_semantic_safety_items
            where run_id = ?
            order by cast(bookid as integer)
            """,
            (cssr_run_id,),
        )
    )
    clean = 0
    remaining_blocked = 0
    for row in rows:
        recovered_dead = row["bookid"] in dead_formula_recovered
        recovered_split = row["bookid"] in split_recovered
        projected_clean = bool(row["strict_clean"]) or recovered_dead or recovered_split
        if projected_clean:
            clean += 1
        if int(row["blocked_hit_count"]) > 0:
            remaining_blocked += 1
        status = "PROJECTED_SAFE_NO_GLOSS" if projected_clean else "REMAINS_FLAGGED"
        conn.execute(
            """
            insert into projected_semantic_safety_items
            (run_id, bookid, projected_clean, projection_status, source_strict_clean,
             recovered_by_dead_formula_mask, recovered_by_local_split, blocked_hit_count,
             audit_text, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                1 if projected_clean else 0,
                status,
                row["strict_clean"],
                1 if recovered_dead else 0,
                1 if recovered_split else 0,
                row["blocked_hit_count"],
                row["audit_text"],
                json.dumps(
                    {
                        "formula_mask_run_id": formula_run_id,
                        "split_run_id": split_run_id,
                    },
                    ensure_ascii=False,
                ),
            ),
        )

    pct = round(100.0 * clean / len(rows), 2) if rows else 0.0
    remaining_flagged = len(rows) - clean
    decision = "PROJECTED_SEMANTIC_SAFETY_AFTER_FORMULA_SPLITS_NO_GLOSS"
    conn.execute(
        """
        insert into projected_semantic_safety_runs
        (run_id, created_at, decision, source_cssr_run_id, book_count,
         projected_clean_book_count, projected_cssr_pct, remaining_flagged_book_count,
         remaining_blocked_book_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            cssr_run_id,
            len(rows),
            clean,
            pct,
            remaining_flagged,
            remaining_blocked,
            json.dumps(
                {
                    "dead_formula_recovered": sorted(dead_formula_recovered, key=int),
                    "local_split_recovered": sorted(split_recovered, key=int),
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
                "book_count": len(rows),
                "projected_clean_book_count": clean,
                "projected_cssr_pct": pct,
                "remaining_flagged_book_count": remaining_flagged,
                "remaining_blocked_book_count": remaining_blocked,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
