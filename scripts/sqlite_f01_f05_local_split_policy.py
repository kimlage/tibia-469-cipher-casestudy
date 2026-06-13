#!/usr/bin/env python3
"""Materialize local display-only split policy for F01/F05."""

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
        create table if not exists f01_f05_local_split_policy_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            source_probe_run_id integer not null,
            recovered_book_count integer not null,
            blocked_preserved_book_count integer not null,
            payload_json text not null
        );

        create table if not exists f01_f05_local_split_policy_items (
            run_id integer not null,
            mask_id text not null,
            bookid text not null,
            split_status text not null,
            gloss_allowed integer not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, mask_id, bookid)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from f01_f05_local_split_policy_runs").fetchone()[0]
    probe_run_id = conn.execute("select max(run_id) from f01_f05_edge_isolation_items").fetchone()[0]

    recovered = set()
    blocked = set()
    for row in conn.execute(
        """
        select mask_id, evidence_json
        from f01_f05_edge_isolation_items
        where run_id = ?
        order by mask_id
        """,
        (probe_run_id,),
    ):
        evidence = json.loads(row["evidence_json"])
        for bookid in evidence.get("formula_only_books", []):
            recovered.add(bookid)
            conn.execute(
                """
                insert into f01_f05_local_split_policy_items
                (run_id, mask_id, bookid, split_status, gloss_allowed, next_action, evidence_json)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    row["mask_id"],
                    bookid,
                    "LOCAL_DISPLAY_FORMULA_ONLY_NO_GLOSS",
                    0,
                    "allow_display_formula_marker_only_in_this_book_context",
                    json.dumps({"source_probe_run_id": probe_run_id}, ensure_ascii=False),
                ),
            )
        for bookid in evidence.get("blocked_books", []):
            blocked.add(bookid)
            conn.execute(
                """
                insert into f01_f05_local_split_policy_items
                (run_id, mask_id, bookid, split_status, gloss_allowed, next_action, evidence_json)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    row["mask_id"],
                    bookid,
                    "PRESERVE_BLOCKED_CONTEXT_NO_PROMOTION",
                    0,
                    "keep_mask_blocked_in_this_book_context",
                    json.dumps({"source_probe_run_id": probe_run_id}, ensure_ascii=False),
                ),
            )

    decision = "F01_F05_LOCAL_SPLIT_POLICY_READY_NO_GLOSS"
    conn.execute(
        """
        insert into f01_f05_local_split_policy_runs
        (run_id, created_at, decision, source_probe_run_id, recovered_book_count,
         blocked_preserved_book_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            probe_run_id,
            len(recovered),
            len(blocked),
            json.dumps({"recovered_books": sorted(recovered, key=int), "blocked_books": sorted(blocked, key=int)}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "recovered_book_count": len(recovered),
                "blocked_preserved_book_count": len(blocked),
                "recovered_books": sorted(recovered, key=int),
                "blocked_books": sorted(blocked, key=int),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
